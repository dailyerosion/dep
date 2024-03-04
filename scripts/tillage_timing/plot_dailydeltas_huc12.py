"""A plot of the deltas for erosion between scenarios."""

import datetime
import sys

import matplotlib.dates as mdates
import pandas as pd
from pandas.io.sql import read_sql
from pyiem.plot.use_agg import plt
from pyiem.util import get_dbconn


def main(argv):
    """Go Main Go."""
    huc12 = argv[1]
    year = int(argv[2])
    prop_cycle = plt.rcParams["axes.prop_cycle"]
    colors = prop_cycle.by_key()["color"]
    pgconn = get_dbconn("idep")
    df = read_sql(
        """
        SELECT scenario, huc_12, avg_delivery, valid from results_by_huc12
        WHERE scenario >= 59 and scenario < 70 and
        extract(year from valid) = %s and huc_12 = %s ORDER by valid ASC
    """,
        pgconn,
        params=(year, huc12),
    )
    df["valid"] = pd.to_datetime(df["valid"])
    ax = plt.axes([0.2, 0.1, 0.75, 0.75])
    baseline = df[df["scenario"] == 59].copy().set_index("valid")
    yticklabels = []
    col = "avg_delivery"
    for scenario in range(60, 70):
        color = colors[scenario - 60]
        date = datetime.date(2000, 4, 15) + datetime.timedelta(
            days=(scenario - 60) * 5
        )
        scendata = df[df["scenario"] == scenario].copy().set_index("valid")
        delta = scendata[col] - baseline[col]
        delta = delta[delta != 0]
        total = (
            (scendata[col].sum() - baseline[col].sum()) / baseline[col].sum()
        ) * 100.0
        yticklabels.append("%s %4.2f%%" % (date.strftime("%b %d"), total))
        x = delta.index.to_pydatetime()
        # res = ax.scatter(x, delta.values + (scenario - 60))
        for idx, val in enumerate(delta):
            ax.arrow(
                x[idx],
                scenario - 60,
                0,
                val * 10.0,
                head_width=4,
                head_length=0.1,
                fc=color,
                ec=color,
            )
        ax.axhline(scenario - 60, color=color)
    ax.set_xlim(datetime.date(year, 1, 1), datetime.date(year + 1, 1, 1))
    ax.set_ylim(-0.5, 10)
    ax.xaxis.set_major_locator(mdates.DayLocator([1]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.set_title(
        "huc12: %s \n%s Daily Change in Delivery vs Apr 10 Planting"
        % (huc12, year)
    )
    ax.grid(axis="x")
    ax.set_yticks(range(10))
    ax.set_yticklabels(yticklabels)
    plt.gcf().savefig("test.png")


if __name__ == "__main__":
    main(sys.argv)
