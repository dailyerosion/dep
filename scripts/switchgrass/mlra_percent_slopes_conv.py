"""Print out the percentage of slopes converted."""

from pandas.io.sql import read_sql
from pyiem.database import get_dbconn

LABELS = {
    36: "Slopes > 3% to Switchgrass",
    37: "Slopes > 6% to Switchgrass",
    38: "Slopes > 10% to Switchgrass",
}


def main(argv):
    """Go Main Go"""
    mlra_id = int(argv[1])
    pgconn = get_dbconn("idep")

    mlraxref = read_sql(
        """
    select distinct mlra_id, mlra_name from mlra
    """,
        pgconn,
        index_col="mlra_id",
    )

    print("%s," % (mlraxref.at[mlra_id, "mlra_name"],), end="")
    for _, scenario in enumerate(range(36, 39)):
        df = read_sql(
            """
        with myhucs as (
            SELECT huc_12 from huc12 where scenario = 0 and mlra_id = %s
        )
        select fpath, f.huc_12 from flowpaths f, myhucs h
        WHERE f.scenario = 0 and f.huc_12 = h.huc_12
        """,
            pgconn,
            params=(mlra_id,),
            index_col=None,
        )
        if df.empty:
            print()
            continue
        hits = 0
        for _, row in df.iterrows():
            prj = ("/prj/%s/%s/%s_%s.prj") % (
                row["huc_12"][:8],
                row["huc_12"][8:],
                row["huc_12"],
                row["fpath"],
            )
            prj2 = "/i/%s/%s" % (scenario, prj)
            if open(prj2).read().find("SWITCHGRASS.rot") > 0:
                hits += 1
        print("%.2f," % (hits / float(len(df.index)) * 100.0,), end="")
    print()


if __name__ == "__main__":
    for mlraid in [
        106,
        107,
        108,
        109,
        121,
        137,
        150,
        155,
        166,
        175,
        176,
        177,
        178,
        179,
        181,
        182,
        186,
        187,
        188,
        196,
        197,
        204,
        205,
    ]:
        main([None, mlraid])
