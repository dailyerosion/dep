"""Replicate Figure 6."""

import click
import pandas as pd
from compute_county_district import DISTRICTS
from matplotlib.lines import Line2D
from pyiem.plot import figure


@click.command()
def main():
    """Go Main Go."""
    fig = figure(
        title="50% Planting Progress Date by Year",
        subtitle="NASS data linearly interpolated",
        logo="dep",
    )
    box_width = 0.2
    box_height = 0.2
    axes = [
        fig.add_axes((0.1, 0.6, box_width, box_height)),
        fig.add_axes((0.4, 0.6, box_width, box_height)),
        fig.add_axes((0.7, 0.6, box_width, box_height)),
        fig.add_axes((0.1, 0.35, box_width, box_height)),
        fig.add_axes((0.4, 0.35, box_width, box_height)),
        fig.add_axes((0.7, 0.35, box_width, box_height)),
        fig.add_axes((0.1, 0.1, box_width, box_height)),
        fig.add_axes((0.4, 0.1, box_width, box_height)),
        fig.add_axes((0.7, 0.1, box_width, box_height)),
    ]
    for crop in ["corn", "soybeans"]:
        deinesdf = pd.read_csv(
            f"deines2023_district_{crop}.csv", parse_dates=["date"]
        )
        depdf = pd.read_csv(
            f"{crop}_dep_vs_nass_251002.csv", parse_dates=["date"]
        )

        for ax, crd in zip(axes, DISTRICTS, strict=True):
            if crop == "corn":
                ax.annotate(
                    DISTRICTS[crd],
                    xy=(0.01, 1.05),
                    xycoords="axes fraction",
                    ha="left",
                    fontsize=10,
                )
            years = list(range(2007, 2021))
            deines = []
            nass = []
            dep = []
            for year in years:
                subdf = deinesdf[
                    (deinesdf["date"].dt.year == year)
                    & (deinesdf["district"] == crd)
                ]
                deines.append(
                    subdf[subdf["pct"] >= 50].iloc[0]["date"].dayofyear
                )

                subdf = depdf[
                    (depdf["date"].dt.year == year)
                    & (depdf["datum"] == DISTRICTS[crd])
                ]
                nass.append(
                    subdf[subdf[f"{crop} planted"] >= 50]
                    .iloc[0]["date"]
                    .dayofyear
                )
                dep.append(
                    subdf[subdf[f"dep_{crop}_planted"] >= 50]
                    .iloc[0]["date"]
                    .dayofyear
                )

            ls = ":" if crop == "soybeans" else "-"
            ax.plot(years, deines, color="r", linestyle=ls)
            ax.plot(years, nass, color="b", linestyle=ls)
            ax.plot(years, dep, color="g", linestyle=ls)

    # Create manual legend in upper right
    fig.legend(
        [
            Line2D(
                [0, 1],
                [0, 1],
                color="r",
            ),
            Line2D(
                [0, 1],
                [0, 1],
                color="b",
            ),
            Line2D(
                [0, 1],
                [0, 1],
                color="g",
            ),
            Line2D(
                [0, 1],
                [0, 1],
                ls=":",
                color="r",
            ),
            Line2D(
                [0, 1],
                [0, 1],
                ls=":",
                color="b",
            ),
            Line2D(
                [0, 1],
                [0, 1],
                ls=":",
                color="g",
            ),
        ],
        [
            "Deines et al. 2023 [corn]",
            "NASS [corn]",
            "DEP [corn]",
            "Deines et al. 2023 [soybeans]",
            "NASS [soybeans]",
            "DEP [soybeans]",
        ],
        loc="upper right",
        bbox_to_anchor=(0.9, 0.95),
        frameon=False,
        ncol=2,
    )

    fig.savefig("fig6.png")


if __name__ == "__main__":
    main()
