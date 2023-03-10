"""A plot of the deltas for erosion between scenarios."""
import datetime
import sys

from pyiem.plot.use_agg import plt
import matplotlib.dates as mdates
from pydep.io.wepp import read_env


def main(argv):
    """Go Main Go."""
    huc12 = argv[1]
    fpath = argv[2]
    year = int(argv[3])
    prop_cycle = plt.rcParams["axes.prop_cycle"]
    colors = prop_cycle.by_key()["color"]

    data = {}
    for scenario in range(59, 70):
        data[scenario] = read_env(
            "/i/%s/env/%s/%s/%s_%s.env"
            % (scenario, huc12[:8], huc12[8:], huc12, fpath)
        ).set_index("date")
        print(data[scenario]["av_det"].sum())
    ax = plt.axes([0.2, 0.1, 0.75, 0.75])
    baseline = data[59][data[59].index.year == year]
    yticklabels = []
    for scenario in range(60, 70):
        color = colors[scenario - 60]
        date = datetime.date(2000, 4, 15) + datetime.timedelta(
            days=(scenario - 60) * 5
        )
        scendata = data[scenario][data[scenario].index.year == year]
        delta = scendata["sed_del"] - baseline["sed_del"]
        delta = delta[delta != 0]
        total = (
            (scendata["sed_del"].sum() - baseline["sed_del"].sum())
            / baseline["sed_del"].sum()
        ) * 100.0
        yticklabels.append("%s %4.2f%%" % (date.strftime("%b %d"), total))
        x = delta.index.to_pydatetime()
        # res = ax.scatter(x, delta.values + (scenario - 60))
        for idx, val in enumerate(delta):
            ax.arrow(
                x[idx],
                scenario - 60,
                0,
                val,
                head_width=0.5,
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
        "huc12: %s fpath: %s\n%s Daily Change in Delivery vs Apr 10 Planting"
        % (huc12, fpath, year)
    )
    ax.grid(axis="x")
    ax.set_yticks(range(10))
    ax.set_yticklabels(yticklabels)
    plt.gcf().savefig("test.png")


if __name__ == "__main__":
    main(sys.argv)
