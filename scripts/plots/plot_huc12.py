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


def main(argv):
    """Do Great Things"""
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()

    df = read_postgis(
        """
        with obs as (
            select huc_12, sum(avg_delivery) * 4.163 as loss
            from results_by_huc12
            WHERE scenario = 0 and valid between '2014-01-01' and '2015-01-01'
            GROUP by huc_12
        )
        SELECT ST_Transform(simple_geom, 4326) as geom, o.huc_12, o.loss
        from obs o JOIN huc12 h on (o.huc_12 = h.huc_12)
        WHERE h.scenario = 0 and states = 'IA' and loss > 25
    """,
        pgconn,
        geom_col="geom",
        index_col="huc_12",
    )
    mp = MapPlot(
        continentalcolor="#EEEEEE",
        nologo=True,
        subtitle=("%.0f HUC12s exceeded 25 T/a, covering %.1f%% of Iowa")
        % (len(df.index), df["geom"].area.sum() / 15.857 * 100.0),
        nocaption=True,
        title=("DEP 2014 HUC12 Hillslope Delivery Rates >= 25 T/a"),
    )

    for _i, row in df.iterrows():
        poly = row["geom"]
        arr = np.asarray(poly.exterior)
        points = mp.ax.projection.transform_points(
            ccrs.Geodetic(), arr[:, 0], arr[:, 1]
        )
        p = Polygon(points[:, :2], fc="r", ec="k", zorder=2, lw=0.2)
        mp.ax.add_patch(p)

    mp.drawcounties()
    mp.postprocess(filename="test.png")


if __name__ == "__main__":
    main(sys.argv)
