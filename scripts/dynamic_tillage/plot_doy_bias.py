"""Figure out where I need the most help."""

from datetime import date, timedelta
from itertools import product

import click
import pandas as pd
from pyiem.plot import figure


@click.command()
@click.option("--crop", required=True)
def main(crop: str):
    """Go main Go."""
    dailydf = pd.read_csv(f"plots/{crop}_progress.csv", parse_dates=["date"])
    dailydf["doy"] = dailydf["date"].dt.dayofyear
    dailydf["year"] = dailydf["date"].dt.year
    dailydf["diff"] = (
        dailydf[f"dep_{crop}_pct"] - dailydf[f"nass_{crop}_pct_interp"]
    )

    fig = figure(
        title="Percentage Points Planting Progress Difference by Day of Year",
        subtitle=f"{crop.capitalize()}, DEP minus Interpolated NASS",
    )
    ax = fig.add_axes((0.1, 0.1, 0.7, 0.8))

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

    ax.legend(loc=(1, 0))
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
    ax.set_ylabel("DEP minus interpolated NASS [percentage points]")

    pngfn = f"plots/doy_bias_{crop}.png"
    print(f"Creating {pngfn}")
    fig.savefig(pngfn)


if __name__ == "__main__":
    main()
