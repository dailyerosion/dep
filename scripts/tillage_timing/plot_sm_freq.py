"""look into soil moisture frequencies."""

import calendar
import sys

from pydep.io.dep import read_wb
from pyiem.plot.use_agg import plt


def main(argv):
    """Get the tillage date."""
    huc12 = argv[1]
    fpath = argv[2]

    wbfn = "/i/59/wb/%s/%s/%s_%s.wb" % (huc12[:8], huc12[8:], huc12, fpath)
    wbdf = read_wb(wbfn)
    wbdf = wbdf[wbdf["ofe"] == 1]
    (fig, ax) = plt.subplots(1, 1)
    for threshold in range(15, 50, 5):
        df = wbdf[wbdf["sw1"] < threshold].groupby("jday").count()
        df = df.reindex(list(range(1, 367))).fillna(0)
        vals = (df["sw1"].rolling(7).mean() / 13.0 * 100,)
        ax.plot(df.index.values, vals[0], label="%s%%" % (threshold,))

    ax.set_xticks([1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335])
    ax.set_xticklabels(calendar.month_abbr[1:])
    ax.grid(True)
    ax.set_xlabel("* 7 Day Smoother Applied")
    ax.set_xlim(90, 153)
    ax.set_ylabel("Frequency [%]")
    ax.set_title(
        f"huc12: {huc12} fpath: {fpath}\n"
        "2007-2019 Frequency of 0-10 cm Soil Moisture below threshold"
    )
    ax.legend()
    fig.savefig("test.png")


if __name__ == "__main__":
    main(sys.argv)
