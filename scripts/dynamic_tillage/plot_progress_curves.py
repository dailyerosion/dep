"""See that we have seperation."""

import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from pyiem.plot import figure


def main():
    """Go Main Go."""
    fig = figure(
        title="",
        figsize=(10.72, 7.2),
        logo=None,
    )
    corndf = pd.read_csv("plots/corn_progress.csv", parse_dates=["date"])
    corndf["day_of_year"] = corndf["date"].dt.dayofyear
    soybeansdf = pd.read_csv(
        "plots/soybeans_progress.csv", parse_dates=["date"]
    )
    soybeansdf["day_of_year"] = soybeansdf["date"].dt.dayofyear
    subplot_width = 0.25
    ax = {
        "IA_corn": fig.add_axes((0.1, 0.55, subplot_width, 0.35)),
        "IA_soybeans": fig.add_axes((0.1, 0.1, subplot_width, 0.35)),
        "MN_corn": fig.add_axes((0.4, 0.55, subplot_width, 0.35)),
        "MN_soybeans": fig.add_axes((0.4, 0.1, subplot_width, 0.35)),
        "NE_corn": fig.add_axes((0.7, 0.55, subplot_width, 0.35)),
        "NE_soybeans": fig.add_axes((0.7, 0.1, subplot_width, 0.35)),
    }
    xticklabels = []
    xticks = []
    for dt in pd.date_range("2000/04/01", "2000/06/15"):
        if dt.day in [1, 15]:
            xticks.append(dt.dayofyear)
            xticklabels.append(dt.strftime("%-d %b"))

    for state in ["MN", "IA", "NE"]:
        for crop in ["corn", "soybeans"]:
            thisax = ax[f"{state}_{crop}"]
            thisax.annotate(
                f"{state} {crop}",
                xy=(0.5, 1.02),
                xycoords="axes fraction",
                ha="center",
                va="bottom",
            )
            thisax.set_xticks(xticks)
            thisax.set_xticklabels(xticklabels, rotation=45)
            thisax.set_yticks([0, 5, 25, 50, 75, 95, 100])
            if state == "IA":
                thisax.set_yticklabels([0, 5, 25, 50, 75, 95, 100])
            else:
                thisax.set_yticklabels([])
            filtered = corndf if crop == "corn" else soybeansdf
            filtered = filtered[filtered["datum"] == state]
            climo = (
                filtered[["day_of_year", f"nass_{crop}_pct_interp"]]
                .groupby("day_of_year")
                .describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
                .droplevel(0, axis=1)
            )
            thisax.plot(
                climo.index,
                climo["mean"],
                color="k",
                lw=2,
            )
            thisax.plot(
                climo.index,
                climo["max"] - climo["min"],
                color="g",
                lw=2,
            )
            thisax.fill_between(
                climo.index,
                climo["min"],
                climo["max"],
                alpha=0.2,
                color="blue",
            )
            thisax.fill_between(
                climo.index,
                climo["25%"],
                climo["75%"],
                alpha=0.2,
                color="red",
            )
            thisax.grid(True)

    # Create legend
    fig.legend(
        [
            Rectangle((0, 0), 1, 1, color="blue", alpha=0.2),
            Rectangle((0, 0), 1, 1, color="red", alpha=0.2),
            Line2D([0, 1], [0, 1], color="k", lw=2),
            Line2D([0, 1], [0, 1], color="g", lw=2),
        ],
        ["Range", "25-75% Range", "Mean", "Range"],
        loc="upper center",
        ncol=4,
    )

    fig.savefig("plots/nass_progress_climo.png")


if __name__ == "__main__":
    main()
