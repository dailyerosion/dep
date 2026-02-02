"""Figure showing days suitable bias."""

from datetime import date, timedelta
from itertools import product

import click
import pandas as pd
from pyiem.plot import figure


@click.command()
def main():
    """Go main Go."""
    dailydf = pd.read_csv("plots/corn_progress.csv", parse_dates=["date"])
    dailydf = dailydf[dailydf["dep_days_suitable"].notna()]
    dailydf["doy"] = dailydf["date"].dt.dayofyear
    dailydf["year"] = dailydf["date"].dt.year
    dailydf["diff"] = (
        dailydf["dep_days_suitable"] - dailydf["nass_days_suitable"]
    )

    fig = figure(
        title="Weekly Days Suitable Difference by Day of Year",
        subtitle="DEP minus NASS",
    )
    ax = fig.add_axes((0.1, 0.1, 0.45, 0.8))

    for datum, year in product(
        dailydf["datum"].unique(), dailydf["year"].unique()
    ):
        subdf = dailydf[
            (dailydf["datum"] == datum) & (dailydf["year"] == year)
        ]
        if subdf.empty:
            continue
        maxval = subdf["diff"].abs().max()
        ax.scatter(
            subdf["doy"],
            subdf["diff"],
            color="#eee" if maxval < 50 else None,
            label=None if maxval < 50 else f"{datum} {year} {maxval:.0f}",
            zorder=2 if maxval < 50 else 3,
        )

    # Plot a simple average
    for state in ["IA", "MN"]:
        subdf = dailydf[dailydf["datum"] == state]
        mean_df = subdf[["doy", "diff"]].groupby("doy").mean()
        median_df = subdf[["doy", "diff"]].groupby("doy").median()
        ax.plot(
            mean_df.index,
            mean_df["diff"],
            lw=5,
            color="k",
            zorder=2,
        )
        ax.plot(
            mean_df.index,
            mean_df["diff"],
            lw=3,
            label=f"{state} Mean",
            zorder=3,
        )
        ax.plot(
            median_df.index,
            median_df["diff"],
            lw=5,
            color="k",
            zorder=2,
        )
        ax.plot(
            median_df.index,
            median_df["diff"],
            lw=3,
            label=f"{state} Median",
            zorder=3,
        )

    ax.legend(loc=(0.8, 0))
    ax.grid()

    xticks = []
    xticklabels = []
    xlim = ax.get_xlim()
    for i in range(int(xlim[0]), int(xlim[1])):
        dt = date(2000, 1, 1) + timedelta(days=i - 1)
        if dt.day in [1, 8, 15, 22]:
            xticks.append(i)
            xticklabels.append(dt.strftime("%-d\n%b"))
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels)
    ax.set_ylabel("DEP minus NASS [days]")

    ax2 = fig.add_axes((0.6, 0.1, 0.35, 0.8))
    boxdf = dailydf[["datum", "diff"]].copy()
    boxdf.boxplot(by="datum", ax=ax2)
    # Set xticklabels rotation to 45
    for tick in ax2.get_xticklabels():
        tick.set_rotation(45)
    ax2.set_xlabel("")
    fig.suptitle("")
    ax2.set_title("Weekly Difference Distribution by Datum")
    ax2.grid()

    pngfn = "plots/doy_bias_suitable.png"
    print(f"Creating {pngfn}")
    fig.savefig(pngfn)


if __name__ == "__main__":
    main()
