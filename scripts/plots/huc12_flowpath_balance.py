"""Diagnostic on HUC12 flowpath balance."""

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
    with centroids as (
        select huc_12, st_centroid(geom) as center, simple_geom from huc12
        where scenario = 0),
    agg as (
        select c.huc_12,
        sum(case when st_y(center) < st_ymax(geom) then 1 else 0 end) as west,
        count(*) from flowpaths f JOIN centroids c on
        (f.huc_12 = c.huc_12) WHERE f.scenario = 0
        GROUP by c.huc_12)
    select a.huc_12, st_transform(c.simple_geom, 4326) as geo,
    a.west, a.count from agg a JOIN centroids c
    ON (a.huc_12 = c.huc_12)
    """,
        pgconn,
        index_col=None,
        geom_col="geo",
    )
    df["percent"] = df["west"] / df["count"] * 100.0
    bins = np.arange(0, 101, 10)
    cmap = plt.get_cmap("RdBu")
    norm = mpcolors.BoundaryNorm(bins, cmap.N)
    mp = MapPlot(
        continentalcolor="thistle",
        nologo=True,
        sector="custom",
        south=36.8,
        north=48.0,
        west=-99.2,
        east=-88.9,
        subtitle="",
        title=(
            "DEP Flowpaths North of HUC12 Centroid (%.0f/%.0f %.2f%%)"
            % (
                df["west"].sum(),
                df["count"].sum(),
                df["west"].sum() / df["count"].sum() * 100.0,
            )
        ),
    )
    for _i, row in df.iterrows():
        c = cmap(norm([row["percent"]]))[0]
        arr = np.asarray(row["geo"].exterior)
        points = mp.ax.projection.transform_points(
            ccrs.Geodetic(), arr[:, 0], arr[:, 1]
        )
        p = Polygon(points[:, :2], fc=c, ec="None", zorder=2, lw=0.1)
        mp.ax.add_patch(p)
    mp.drawcounties()
    mp.draw_colorbar(bins, cmap, norm, title="Percent", extend="neither")
    mp.postprocess(filename="/tmp/huc12_north.png")

    # gdf = df.groupby('fps').count()
    # gdf.columns = ['count', ]
    # gdf['cumsum'] = gdf['count'].cumsum()
    # gdf['percent'] = gdf['cumsum'] / gdf['count'].sum() * 100.
    # gdf.to_csv('/tmp/huc12_flowpath_cnts.csv')


if __name__ == "__main__":
    main()
