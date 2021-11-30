"""General HUC12 mapper"""
# third party
from pyiem.plot import MapPlot
from pyiem.util import get_dbconn
from geopandas import read_postgis

with open("myhucs.txt", encoding="utf-8") as fh:
    MYHUCS = [x.strip() for x in fh.readlines()]


def main():
    """Do Great Things"""
    pgconn = get_dbconn("idep")

    mp = MapPlot(
        continentalcolor="#EEEEEE",
        logo="dep",
        subtitle="3 HUC12s choosen per MLRA",
        nocaption=True,
        title="Climate Change Experiments 30 Random HUC12s",
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
    df = df.to_crs(mp.panels[0].crs)
    df.plot(
        ax=mp.panels[0].ax,
        edgecolor="k",
        facecolor="none",
        linewidth=0.2,
        zorder=2,
        aspect=None,  # !important
    )

    df = read_postgis(
        "select huc_12, ST_transform(geom, 4326) as geom from huc12 "
        "where huc_12 in %s and scenario = 0",
        pgconn,
        params=(tuple(MYHUCS),),
        geom_col="geom",
        index_col="huc_12",
    )
    df = df.to_crs(mp.panels[0].crs)
    df.plot(
        ax=mp.panels[0].ax,
        edgecolor="k",
        facecolor="red",
        linewidth=0.5,
        zorder=3,
        aspect=None,  # !important
    )

    mp.postprocess(filename="mlra_huc12s.png")


if __name__ == "__main__":
    main()
