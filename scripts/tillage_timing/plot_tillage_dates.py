"""Generate a plot."""

import pandas as pd
import matplotlib.dates as mdates
from pyiem.plot.use_agg import plt
THRESHOLDS = {
    81: 45,
    82: 40,
    83: 35,
    84: 30,
    85: 25,
    86: 20,
    87: 15,
}


def main():
    """Go Main Go."""
    (fig, ax) = plt.subplots(1, 1)
    for scenario in THRESHOLDS:
        df = pd.read_csv(
            "scenario%s_dates.txt" % (scenario, ), header=None,
            names=('date', 'total'))
        df['date'] = pd.to_datetime(df['date'])
        ax.plot(
            df['date'].values, df['total'].values / df['total'].max() * 100.,
            label='%.0f%%' % (THRESHOLDS[scenario], ))
    ax.grid(True)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%-d %b"))
    ax.set_xlabel("Date of 2018, tillage done on 30 May if threshold unmeet.")
    ax.set_ylabel("Percentage of Flowpaths Tilled")
    ax.set_title("DEP Tillage Timing based on 0-10cm VWC")
    ax.legend(loc=4, ncol=3)
    ax.set_yticks([0, 5, 10, 25, 50, 75, 90, 95, 100])
    ax.set_ylim(0, 100.1)
    fig.savefig('test.png')


if __name__ == '__main__':
    main()
