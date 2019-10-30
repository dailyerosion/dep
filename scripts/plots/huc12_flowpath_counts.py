"""Diagnostic on HUC12 flowpath counts."""

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
        select f.huc_12, count(*) as fps,
        st_transform(h.simple_geom, 4326) as geo
        from flowpaths f JOIN huc12 h on
        (f.huc_12 = h.huc_12) WHERE f.scenario = 0 and h.scenario = 0
        GROUP by f.huc_12, geo ORDER by fps ASC
    """,
        pgconn,
        index_col=None,
        geom_col="geo",
    )
    bins = np.arange(1, 42, 2)
    cmap = plt.get_cmap("copper")
    cmap.set_over("white")
    cmap.set_under("thistle")
    norm = mpcolors.BoundaryNorm(bins, cmap.N)
    mp = MapPlot(
        continentalcolor="thistle",
        nologo=True,
        sector="custom",
        south=36.8,
        north=45.0,
        west=-99.2,
        east=-88.9,
        subtitle="",
        title=(
            "DEP HUCs with <40 Flowpaths (%.0f/%.0f %.2f%%)"
            % (
                len(df[df["fps"] < 40].index),
                len(df.index),
                len(df[df["fps"] < 40].index) / len(df.index) * 100.0,
            )
        ),
    )
    for _i, row in df.iterrows():
        c = cmap(norm([row["fps"]]))[0]
        arr = np.asarray(row["geo"].exterior)
        points = mp.ax.projection.transform_points(
            ccrs.Geodetic(), arr[:, 0], arr[:, 1]
        )
        p = Polygon(points[:, :2], fc=c, ec="None", zorder=2, lw=0.1)
        mp.ax.add_patch(p)
    mp.drawcounties()
    mp.draw_colorbar(bins, cmap, norm, title="Count")
    mp.postprocess(filename="/tmp/huc12_cnts.png")

    # gdf = df.groupby('fps').count()
    # gdf.columns = ['count', ]
    # gdf['cumsum'] = gdf['count'].cumsum()
    # gdf['percent'] = gdf['cumsum'] / gdf['count'].sum() * 100.
    # gdf.to_csv('/tmp/huc12_flowpath_cnts.csv')


if __name__ == "__main__":
    main()
