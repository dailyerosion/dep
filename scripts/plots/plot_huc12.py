"""General HUC12 mapper"""
import sys

from pyiem.plot import MapPlot, get_cmap
from pyiem.reference import Z_POLITICAL
from pyiem.util import get_sqlalchemy_conn
import geopandas as gpd
import matplotlib.colors as mpcolors


def main(argv):
    """Do Great Things"""
    plot_huc8 = False
    with get_sqlalchemy_conn("idep") as conn:
        df = gpd.read_postgis(
            """
            SELECT ST_Transform(simple_geom, 4326) as geom, dominant_tillage,
            huc_12
            from huc12 WHERE scenario = 0
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
        title="DEP Dominant Tillage Code by HUC12",
        subtitle=(f"{len(df.index)} HUC12s"),
    )
    cmap = get_cmap("plasma")
    bins = list(range(1, 8))
    norm = mpcolors.BoundaryNorm(bins, cmap.N)
    df["color"] = [c for c in cmap(norm(df["dominant_tillage"].values))]

    df.to_crs(mp.panels[0].crs).plot(
        ax=mp.panels[0].ax,
        aspect=None,
        color=df["color"],
        zorder=Z_POLITICAL - 1,
    )
    if plot_huc8:
        huc8.to_crs(mp.panels[0].crs).plot(
            ax=mp.panels[0].ax,
            aspect=None,
            edgecolor="b",
            facecolor="None",
            zorder=Z_POLITICAL + 1,
        )
    mp.draw_colorbar(bins, cmap, norm, units="Tillage Code", extend="neither")

    mp.postprocess(filename="test.png")


if __name__ == "__main__":
    main(sys.argv)
