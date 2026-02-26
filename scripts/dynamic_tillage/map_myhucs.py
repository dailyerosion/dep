"""Plot myhucs.txt on a map."""

import geopandas as gpd
from pyiem.database import get_sqlalchemy_conn, sql_helper
from pyiem.plot import MapPlot
from pyiem.reference import Z_OVERLAY


def main():
    """Go Main Go."""
    with open("myhucs.txt") as fh:
        huc12s = [line.strip() for line in fh]
    with get_sqlalchemy_conn("idep") as conn:
        hucdf = gpd.read_postgis(
            sql_helper("""
                select huc_12, geom, mlra_id, dominant_tillage,
                average_slope_ratio, name from huc12
                where huc_12 = ANY(:hucs) and scenario = 0
            """),
            conn,
            params={"hucs": huc12s},
            geom_col="geom",
            index_col="huc_12",
        )
        hucdf.to_csv("plots/myhucs.csv")
        mlras = hucdf["mlra_id"].unique().tolist()
        mlradf = gpd.read_postgis(
            sql_helper(
                "select mlra_id, geom from mlra where mlra_id = ANY(:mlras)"
            ),
            conn,
            params={"mlras": mlras},
            geom_col="geom",
            index_col="mlra_id",
        )
    _subtitle = f"{len(hucdf.index)} HUC12s selected over {len(mlras)} MLRAs"
    print(_subtitle)
    mp = MapPlot(
        sector="custom",
        south=36.8,
        north=49.4,
        west=-99.2,
        east=-88.9,
        logo=None,
        title="",
        nocaption=True,
    )
    mlradf.to_crs(mp.panels[0].crs).plot(
        aspect=None,
        ax=mp.panels[0].ax,
        fc="None",
        ec="k",
        lw=1,
        zorder=Z_OVERLAY,
    )
    hucdf.to_crs(mp.panels[0].crs).plot(
        aspect=None,
        ax=mp.panels[0].ax,
        color="r",
        lw=2,
        zorder=Z_OVERLAY,
    )
    mp.fig.savefig("plots/myhucs.png", dpi=300)


if __name__ == "__main__":
    main()
