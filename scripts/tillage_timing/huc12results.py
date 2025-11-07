"""Create summary tables."""

from pandas.io.sql import read_sql
from pyiem.database import get_dbconn


def main():
    """Go Main Go."""
    years = 13.0
    pgconn = get_dbconn("idep")

    scens = [
        141,
    ]
    scens.insert(0, 0)
    with open("myhucs.txt") as fh:
        myhucs = [x.strip() for x in fh.readlines()]
    for scenario in scens:
        df = read_sql(
            """
            SELECT
            sum(avg_loss) * 4.463 as detach,
            sum(avg_delivery) * 4.463 as delivery,
            sum(avg_runoff) as runoff,
            sum(avg_precip) as precip
            from results_by_huc12 r
            WHERE r.valid >= '2008-01-01'
            and r.valid < '2021-01-01' and scenario = %s and huc_12 in %s
        """,
            pgconn,
            params=(scenario, tuple(myhucs)),
        )
        row = df.iloc[0]
        div = years * 30.0
        print(
            "%s %6.2f %6.2f %6.2f %6.2f"
            % (
                scenario,
                row["runoff"] / div,
                row["delivery"] / div,
                row["detach"] / div,
                row["precip"] / div,
            )
        )


if __name__ == "__main__":
    main()
