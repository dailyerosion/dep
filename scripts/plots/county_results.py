"""County level agg."""

from geopandas import read_postgis
from pandas.io.sql import read_sql
from pyiem.plot.geoplot import MapPlot
from pyiem.util import get_dbconn


def main():
    """Go Main Go."""
    years = 12.0  # 2008 - 2019
    pgconn = get_dbconn("idep")
    postgis = get_dbconn("postgis")

    # Get the initial geometries
    df = read_postgis(
        """
        SELECT ugc, name, geom from ugcs WHERE end_ts is null and
        substr(ugc, 1, 3) = 'IAC'
        """,
        postgis,
        index_col="ugc",
        crs="EPSG:4326",
    )
    scenario = 0
    df2 = read_sql(
        """WITH data as (
    SELECT r.huc_12,
    sum(avg_loss) * 4.463 / %s as detach,
    sum(avg_delivery) * 4.463 / %s as delivery,
    sum(avg_runoff) / 25.4 / %s as runoff
    from results_by_huc12 r
    , huc12 h WHERE r.huc_12 = h.huc_12 and h.states ~* 'IA'
    and r.scenario = %s and h.scenario = 0 and r.valid < '2020-01-01'
    and r.valid > '2008-01-01'
    GROUP by r.huc_12)

    SELECT ugc, avg(detach) as detach, avg(delivery) as delivery,
    avg(runoff) as runoff from data d JOIN huc12 h on (d.huc_12 = h.huc_12)
    WHERE h.scenario = 0 GROUP by ugc ORDER by delivery desc
    """,
        pgconn,
        params=(years, years, years, scenario),
        index_col="ugc",
    )
    newcols = {
        "detach": "det%s" % (0,),
        "delivery": "del%s" % (0,),
        "runoff": "run%s" % (0,),
    }
    for key, val in newcols.items():
        df[val] = df2[key]
    df = df.sort_values("del0", ascending=False)
    print(df.head(10))

    mp = MapPlot(
        title="2008-2019 DEP Top 10 Erosive Counties", logo="dep", caption=""
    )
    df2 = df.head(10)
    mp.fill_ugcs(df2["del0"].to_dict())
    mp.postprocess(filename="test.png")


if __name__ == "__main__":
    main()
