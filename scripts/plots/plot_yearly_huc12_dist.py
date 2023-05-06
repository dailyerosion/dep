"""Plot a distribution."""

import seaborn as sns
from pandas.io.sql import read_sql
from pyiem.plot.use_agg import plt
from pyiem.util import get_dbconn


def main():
    """Go Main Go."""
    df = read_sql(
        "SELECT r.huc_12, sum(avg_delivery) * 4.463 as delivery from "
        "results_by_huc12 r, huc12 h WHERE r.scenario = 0 and "
        "h.scenario = 0 and r.huc_12 = h.huc_12 and h.states = 'IA' and "
        "valid >= '2019-01-01' and valid < '2020-01-01' GROUP by r.huc_12",
        get_dbconn("idep"),
        index_col="huc_12",
    )
    ax = sns.distplot(df["delivery"], hist=True, color="g", rug=False)
    ax.set_xlim(0)
    avgval = df["delivery"].mean()
    ax.set_xlabel(f"2019 Delivery [T/a], avg={avgval:.2f}")
    ax.set_ylabel("Frequency")
    ax.set_title("2019 DEP Iowa HUC12 Average Soil Delivery Histogram")
    ax.axvline(avgval)
    cnt = len(df.index)
    y = 0.9
    for thres in [0.1, 0.25, 0.5]:
        hits = len(df[df["delivery"] < thres].index)
        ax.text(
            0.9,
            y,
            "HUC12 < %.2f T/a %.0f/%.0f %.2f%%"
            % (thres, hits, cnt, hits / cnt * 100.0),
            ha="right",
            transform=ax.transAxes,
        )
        y -= 0.07
    plt.savefig("test.png")


if __name__ == "__main__":
    main()
