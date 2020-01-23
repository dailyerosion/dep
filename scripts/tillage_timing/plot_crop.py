"""A plot of the deltas for erosion between scenarios."""
import datetime
import sys

from pyiem.dep import read_crop
from pyiem.plot.use_agg import plt
import matplotlib.dates as mdates


def main(argv):
    """Go Main Go."""
    huc12 = argv[1]
    fpath = argv[2]
    year = int(argv[3])
    prop_cycle = plt.rcParams["axes.prop_cycle"]
    colors = prop_cycle.by_key()["color"]

    data = {}
    for scenario in range(59, 70):
        df = read_crop(
            "/i/%s/crop/%s/%s/%s_%s.crop"
            % (scenario, huc12[:8], huc12[8:], huc12, fpath)
        )
        data[scenario] = df[df["ofe"] == 1].set_index("date")
    ax1 = plt.axes([0.15, 0.5, 0.85, 0.35])
    ax2 = plt.axes([0.15, 0.1, 0.85, 0.35])
    baseline = data[59][data[59].index.year == year]
    for scenario in range(60, 70):
        color = colors[scenario - 60]
        date = datetime.date(2000, 4, 15) + datetime.timedelta(
            days=(scenario - 60) * 5
        )
        scendata = data[scenario][data[scenario]["year"] == year]
        delta = scendata["canopy_percent"] - baseline["canopy_percent"]
        x = delta.index.to_pydatetime()
        ax1.plot(
            x,
            scendata["canopy_percent"] * 100.0,
            label=date.strftime("%b %d"),
            color=color,
        )
        ax2.plot(x, delta.values * 100.0, color=color)
    ax1.set_xlim(datetime.date(year, 4, 15), datetime.date(year, 7, 15))
    ax2.set_xlim(datetime.date(year, 4, 15), datetime.date(year, 7, 15))
    ax1.xaxis.set_major_locator(mdates.DayLocator([1]))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax2.xaxis.set_major_locator(mdates.DayLocator([1]))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax1.set_ylabel("Coverage [%]")
    ax2.set_ylabel("Absolute Differnece from Apr 10 [%]")
    ax2.set_ylim(-101, 0)
    ax1.set_title(
        "huc12: %s fpath: %s\n%s Canopy Coverage by Planting Date"
        % (huc12, fpath, year)
    )
    ax1.grid()
    ax2.grid()
    ax1.legend(loc=2, ncol=2)
    plt.gcf().savefig("test.png")


if __name__ == "__main__":
    main(sys.argv)
