"""General HUC12 mapper"""
import datetime
import sys

from pyiem.plot.use_agg import plt
from pyiem.plot import MapPlot, nwsprecip
from pyiem.reference import Z_POLITICAL
from pyiem.util import get_sqlalchemy_conn
import geopandas as gpd
from shapely.wkb import loads
import numpy as np
import cartopy.crs as ccrs
from matplotlib.patches import Polygon
import matplotlib.colors as mpcolors


def main(argv):
    """Do Great Things"""
    with get_sqlalchemy_conn("idep") as conn:
        df = gpd.read_postgis(
            """
            with obs as (
                select huc_12, sum(avg_delivery) * 4.463 as loss
                from results_by_huc12
                WHERE scenario = 0 and
                valid between '2014-01-01' and '2015-01-01'
                GROUP by huc_12
            )
            SELECT ST_Transform(simple_geom, 4326) as geom, o.huc_12, o.loss
            from obs o RIGHT JOIN huc12 h on (o.huc_12 = h.huc_12)
            WHERE h.scenario = 0
        """,
            conn,
            geom_col="geom",
            index_col="huc_12",
        )
        huc8 = gpd.read_postgis(
            "select simple_geom, huc8 from wbd_huc8 WHERE huc8 in ( "
            "select distinct substr(huc_12, 1, 8) from huc12 where scenario "
            "= 0)",
            conn,
            geom_col="simple_geom",
            index_col="huc8",
        )
    mp = MapPlot(
        sector="custom",
        south=36.8,
        north=49.4,
        west=-99.2,
        east=-88.9,
        continentalcolor="white",
        logo="dep",
        nocaption=True,
        title="DEP HUC12 Model Domain as of 17 March 2022",
        subtitle=(f"{len(df.index)} HUC12s over {len(huc8.index)} HUC8s"),
    )
    df.to_crs(mp.panels[0].crs).plot(
        ax=mp.panels[0].ax,
        aspect=None,
        color="tan",
        zorder=Z_POLITICAL - 1,
    )
    huc8.to_crs(mp.panels[0].crs).plot(
        ax=mp.panels[0].ax,
        aspect=None,
        edgecolor="b",
        facecolor="None",
        zorder=Z_POLITICAL + 1,
    )
    mp.postprocess(filename="test.png")


if __name__ == "__main__":
    main(sys.argv)
