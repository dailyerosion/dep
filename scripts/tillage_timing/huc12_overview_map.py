"""General HUC12 mapper"""
from __future__ import print_function

import datetime
import sys

from pyiem.plot.use_agg import plt
from pyiem.plot import MapPlot, nwsprecip
from pyiem.util import get_dbconn
from geopandas import read_postgis
from shapely.wkb import loads
import numpy as np
import cartopy.crs as ccrs
from matplotlib.patches import Polygon
import matplotlib.colors as mpcolors

MYHUCS = [x.strip() for x in open("myhucs.txt").readlines()]


def main(argv):
    """Do Great Things"""
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()

    mp = MapPlot(
        continentalcolor="#EEEEEE",
        nologo=True,
        subtitle="3 HUC12s choosen per MLRA",
        nocaption=True,
        title=("Tillage Timing Experiment 30 Random HUC12s"),
    )

    df = read_postgis(
        """
        SELECT geom, mlra_id from mlra WHERE mlra_id in (
            select distinct mlra_id from huc12
            where huc_12 in %s and scenario = 0)
    """,
        pgconn,
        params=(tuple(MYHUCS),),
        geom_col="geom",
        index_col="mlra_id",
    )
    for _i, row in df.iterrows():
        for poly in row["geom"]:
            arr = np.asarray(poly.exterior)
            points = mp.ax.projection.transform_points(
                ccrs.Geodetic(), arr[:, 0], arr[:, 1]
            )
            p = Polygon(points[:, :2], fc="None", ec="k", zorder=2, lw=0.2)
            mp.ax.add_patch(p)

    df = read_postgis(
        """
        select huc_12, ST_transform(geom, 4326) as geom from huc12
        where huc_12 in %s and scenario = 0
    """,
        pgconn,
        params=(tuple(MYHUCS),),
        geom_col="geom",
        index_col="huc_12",
    )
    for _i, row in df.iterrows():
        for poly in row["geom"]:
            arr = np.asarray(poly.exterior)
            points = mp.ax.projection.transform_points(
                ccrs.Geodetic(), arr[:, 0], arr[:, 1]
            )
            p = Polygon(points[:, :2], fc="r", ec="k", zorder=3, lw=0.5)
            mp.ax.add_patch(p)

    mp.postprocess(filename="test.png")


if __name__ == "__main__":
    main(sys.argv)
