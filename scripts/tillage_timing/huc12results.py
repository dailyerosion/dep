"""Create summary tables."""

from pyiem.util import get_dbconn
from pandas.io.sql import read_sql


def main():
    """Go Main Go."""
    years = 1.0
    pgconn = get_dbconn("idep")

    scens = list(range(81, 91))
    scens.insert(0, 0)
    myhucs = [x.strip() for x in open("myhucs.txt").readlines()]
    for scenario in scens:
        df = read_sql(
            """
            SELECT
            sum(avg_loss) * 4.463 as detach,
            sum(avg_delivery) * 4.463 as delivery,
            sum(avg_runoff) as runoff
            from results_by_huc12 r
            WHERE r.valid >= '2018-01-01'
            and r.valid < '2019-01-01' and scenario = %s and huc_12 in %s
        """,
            pgconn,
            params=(scenario, tuple(myhucs)),
        )
        row = df.iloc[0]
        div = years * 30.0
        print(
            "%s %6.2f %6.2f %6.2f"
            % (
                scenario,
                row["runoff"] / div,
                row["delivery"] / div,
                row["detach"] / div,
            )
        )


if __name__ == "__main__":
    main()
