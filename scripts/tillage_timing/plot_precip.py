"""Plot of 5 day averaged precipitation."""

import calendar

from pandas.io.sql import read_sql
from pyiem.plot.use_agg import plt
from pyiem.util import get_dbconn


def main():
    """Go Main Go."""
    with open("myhucs.txt") as fh:
        myhucs = [x.strip() for x in fh.readlines()]
    pgconn = get_dbconn("idep")
    df = read_sql(
        """
        SELECT extract(year from valid),
        (extract(doy from valid)::int / 5)::int as datum,
        max_precip
        from results_by_huc12 where scenario = 0 and
        valid < '2019-01-01' and valid >= '2008-01-01'
        and huc_12 in %s and max_precip >= 50
    """,
        pgconn,
        params=(tuple(myhucs),),
    )
    # each datum should have 30 hucs * 11 years * 5 days of data
    gdf = df.groupby("datum").count() / (30.0 * 11.0 * 5.0)

    (fig, ax) = plt.subplots(1, 1)
    ax.bar(gdf.index.values * 5, gdf["max_precip"].values * 100.0, width=5)

    ax.set_xticks([1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335])
    ax.set_xticklabels(calendar.month_abbr[1:])
    ax.grid(True)
    ax.set_title("2008-2018 HUC12 Frequency of Daily Precipitation >= 50mm")
    ax.set_ylabel("Frequency [%]")
    ax.set_xlim(-1, 367)

    fig.savefig("test.png")


if __name__ == "__main__":
    main()
