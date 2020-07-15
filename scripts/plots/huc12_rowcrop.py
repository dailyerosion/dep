"""Diagnostic on HUC12 rowcrop counts."""

import numpy as np
import cartopy.crs as ccrs
from matplotlib.patches import Polygon
import matplotlib.colors as mpcolors
from geopandas import read_postgis
from pyiem.util import get_dbconn
from pyiem.plot.use_agg import plt
from pyiem.plot.geoplot import MapPlot


def main():
    """Go Main Go."""
    pgconn = get_dbconn("idep")
    df = read_postgis(
        """
        with data as (
            select huc_12, fpath, substr(landuse, 12, 1) as crop from
            flowpaths f JOIN flowpath_points p on (f.fid = p.flowpath)
            WHERE f.scenario = 0),
        agg as (
            select huc_12,
            sum(case when crop in ('C', 'B') then 1 else 0 end) /
            count(*)::float * 100 as percent from data GROUP by huc_12)
        select a.huc_12, a.percent as ag,
        ST_Transform(h.simple_geom, 4326) as geo from agg a JOIN huc12 h on
        (a.huc_12 = h.huc_12) where h.scenario = 0 and h.states = 'MN'
    """,
        pgconn,
        index_col="huc_12",
        geom_col="geo",
    )
    bins = [1, 10, 25, 50, 75, 90, 100]
    cmap = plt.get_cmap("copper")
    cmap.set_over("red")
    cmap.set_under("thistle")
    norm = mpcolors.BoundaryNorm(bins, cmap.N)
    mp = MapPlot(
        continentalcolor="thistle",
        logo="dep",
        sector="state",
        state="MN",
        caption="Daily Erosion Project",
        title="Minnesota DEP HUC12 Percentage of Flowpaths in Row Crops",
        subtitle=(
            "Number of HUC12s with <40%% Row Crop (%.0f/%.0f %.2f%%)"
            % (
                len(df[df["ag"] < 40].index),
                len(df.index),
                len(df[df["ag"] < 40].index) / len(df.index) * 100.0,
            )
        ),
    )
    for _i, row in df.iterrows():
        c = cmap(norm([row["ag"]]))[0]
        arr = np.asarray(row["geo"].exterior)
        points = mp.ax.projection.transform_points(
            ccrs.Geodetic(), arr[:, 0], arr[:, 1]
        )
        p = Polygon(points[:, :2], fc=c, ec="None", zorder=2, lw=0.1)
        mp.ax.add_patch(p)
    mp.drawcounties()
    mp.draw_colorbar(bins, cmap, norm, extend="max", title="Count")
    mp.postprocess(filename="/tmp/huc12_agland.png")

    # gdf = df.groupby('fps').count()
    # gdf.columns = ['count', ]
    # gdf['cumsum'] = gdf['count'].cumsum()
    # gdf['percent'] = gdf['cumsum'] / gdf['count'].sum() * 100.
    # gdf.to_csv('/tmp/huc12_flowpath_cnts.csv')


if __name__ == "__main__":
    main()
