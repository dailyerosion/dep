"""Dump some monthly data"""

from pandas.io.sql import read_sql
from pyiem.util import get_dbconn


def main():
    """Go Main Go"""
    pgconn = get_dbconn("idep")
    df = read_sql(
        """
    SELECT r.huc_12, to_char(valid, 'YYYYmm') as date,
    sum(qc_precip) as precip_mm,
    sum(avg_loss) as detach_kgm2,
    sum(avg_delivery) as delivery_kgm2,
    sum(avg_runoff) as runoff_mm from results_by_huc12 r JOIN huc12 h on
    (r.huc_12 = h.huc_12 and r.scenario = h.scenario)
    WHERE r.scenario = 0 and h.states ~* 'MN' and
    valid >= '2017-01-01' and valid < '2021-01-01'
    GROUP by r.huc_12, date ORDER by huc_12, date
    """,
        pgconn,
    )
    df = df.pivot(
        index="huc_12",
        columns="date",
        values=["precip_mm", "detach_kgm2", "delivery_kgm2", "runoff_mm"],
    )
    df.columns = df.columns.to_flat_index()
    df.columns = ["_".join(tup) for tup in df.columns.values]
    df.to_csv("mn_dep.csv", index=True)


if __name__ == "__main__":
    main()
