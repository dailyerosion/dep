"""Generate a plot."""

import matplotlib.dates as mdates
import pandas as pd
from pyiem.plot.use_agg import plt

THRESHOLDS = {81: 45, 82: 40, 83: 35, 84: 30, 85: 25, 86: 20, 87: 15}
PL_THRESHOLDS = {88: 1.0, 89: 0.9, 90: None}


def main():
    """Go Main Go."""
    (fig, ax) = plt.subplots(1, 1)
    ax.set_position([0.1, 0.2, 0.85, 0.75])
    for scenario in THRESHOLDS:
        df = pd.read_csv("scenario%s_dates.txt" % (scenario,))
        df["date"] = pd.to_datetime(df["date"])
        ax.plot(
            df["date"].values,
            df["total"].values / df["total"].max() * 100.0,
            label="%.0f%%" % (THRESHOLDS[scenario],),
        )
    for scenario in PL_THRESHOLDS:
        df = pd.read_csv("scenario%s_dates.txt" % (scenario,))
        df["date"] = pd.to_datetime(df["date"])
        if scenario != 90:
            label = "PL%.1f" % (PL_THRESHOLDS[scenario],)
        else:
            label = "PL(SAT)"
        ax.plot(
            df["date"].values,
            df["total"].values / df["total"].max() * 100.0,
            label=label,
            linestyle="-.",
        )
    ax.grid(True)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%-d %b"))
    ax.set_xlabel("Date of 2018, tillage done on 30 May if threshold unmeet.")
    ax.set_ylabel("Percentage of Flowpaths Tilled")
    ax.set_title("DEP Tillage Timing based on 0-10cm VWC")
    ax.legend(loc=(-0.02, -0.26), ncol=5)
    ax.set_yticks([0, 5, 10, 25, 50, 75, 90, 95, 100])
    ax.set_ylim(0, 100.1)
    fig.savefig("test.png")


if __name__ == "__main__":
    main()
