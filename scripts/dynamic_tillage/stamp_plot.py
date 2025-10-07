"""Create a Postage Stamp Plot of all the years of data."""

import click
import matplotlib.cm as mpcm
import matplotlib.colors as mpcolors
import numpy
import pandas as pd
from matplotlib.patches import Rectangle
from pyiem.plot import figure_axes
from pyiem.util import logger

LOG = logger()


@click.command()
@click.option("--crop", default="corn", help="Which crop to process")
@click.option(
    "--dots",
    default="nass",
    type=click.Choice(("nass", "deines2023", "dep")),
)
@click.option(
    "--lines",
    default="dep",
    type=click.Choice(("nass", "deines2023", "dep")),
)
def main(crop: str, dots: str, lines: str):
    """Go main Go."""
    jumbo = pd.read_csv(f"{crop}_dep_vs_nass_251006.csv", parse_dates=["date"])
    jumbo["dayofyear"] = jumbo["date"].dt.dayofyear

    fig, ax = figure_axes(
        title=(
            f"{crop.capitalize()} Planting Progress "
            f"({lines} Lines, {dots} Dots)"
        ),
        logo="dep",
        figsize=(10, 8),
    )
    ax.set_position([0.05, 0.07, 0.85, 0.83])
    # Remove all splines
    for side in ["top", "right", "left", "bottom"]:
        ax.spines[side].set_visible(False)

    xtilesize = 1.0 / 19.0
    ytilesize = 1.0 / 11.0
    cmap = mpcolors.ListedColormap(
        ["#00441b", "#a1d99b", "#eeff00", "#d30000"]
    )
    norm = mpcolors.BoundaryNorm([0, 10, 20, 35, 100], cmap.N)
    dotcol = f"{dots}_{crop}_pct"
    linecol = f"{lines}_{crop}_pct"
    lyear = 2021 if "deines2023" in (dots, lines) else 2020
    for x, year in enumerate(range(2007, lyear)):
        # Psuedo axis definition
        x0 = x / 19.0
        xmin = pd.Timestamp(f"{year}-04-11").dayofyear
        xmax = pd.Timestamp(f"{year}-06-15").dayofyear
        for y, (datum, _color) in enumerate(
            zip(
                (
                    "IA_SW IA_SC IA_SE IA_WC IA_C IA_EC IA_NW IA_NC "
                    "IA_NE IA MN"
                ).split(),
                (
                    "red blue green orange tan purple "
                    "brown pink skyblue black gray"
                ).split(),
                strict=True,
            )
        ):
            # Psuedo axis definition
            y0 = y / 11.0
            df = jumbo[
                (jumbo["date"].dt.year == year)
                & (jumbo["datum"] == datum)
                & (jumbo["dayofyear"] >= xmin)
                & (jumbo["dayofyear"] <= xmax)
            ]
            # Calculate RMSE
            rmse = ((df[dotcol] - df[linecol]).pow(2).mean()) ** 0.5
            mae = (df[dotcol] - df[linecol]).abs().mean()
            print(f"{year} {datum} RMSE: {rmse:.2f} MAE: {mae:.2f}")
            background_color = cmap(norm(mae))
            ax.add_patch(
                Rectangle(
                    (x0, y0),
                    xtilesize,
                    ytilesize,
                    color=background_color,
                    alpha=1,
                )
            )
            ax.plot(
                x0 + (df["dayofyear"] - xmin) / (xmax - xmin) * xtilesize,
                y0 + df[linecol] / 100.0 * ytilesize,
                color="k",
                zorder=3,
            )
            ax.scatter(
                x0 + (df["dayofyear"] - xmin) / (xmax - xmin) * xtilesize,
                y0 + df[dotcol] / 100.0 * ytilesize,
                color="k",
                s=5,
                zorder=4,
            )
            ax.text(
                x0 + 0.75 * xtilesize,
                y0 + 0.15 * ytilesize,
                f"{mae:.0f}",
                ha="center",
                va="center",
                color="b",
                fontsize=14,
                zorder=5,
            )

    ax.set_xticks(numpy.arange(0, 0.99, 1.0 / 19.0) + xtilesize / 2.0)
    ax.set_xticklabels(range(2007, 2026), rotation=45)
    ax.set_yticks(numpy.arange(0, 0.99, 1.0 / 11.0) + ytilesize / 2.0)
    ax.set_yticklabels(
        (
            "IA\nSW IA\nSC IA\nSE IA\nWC IA\nC IA\nEC "
            "IA\nNW IA\nNC IA\nNE IA MN"
        ).split(" "),
        rotation=45,
        ha="right",
    )
    # Add gridlines
    for x in numpy.arange(0, 1.1, 1.0 / 19.0):
        ax.axvline(x, color="k", lw=0.5)
    for y in numpy.arange(0, 1.01, 1.0 / 11.0):
        ax.axhline(y, color="k", lw=0.5)
    ax.set_xlim(-0.01, 1.01)
    ax.set_ylim(-0.01, 1.01)

    # Add colorbar
    ax2 = fig.add_axes((0.9, 0.1, 0.02, 0.8))
    cb = fig.colorbar(
        mpcm.ScalarMappable(norm=norm, cmap=cmap),
        cax=ax2,
        orientation="vertical",
        spacing="proportional",
    )
    cb.set_label(
        f"MAE of {dots} vs {lines} Planting Progress [percentage points]"
    )

    # plots is symlinked
    pngfn = f"plots/{crop}_{dots}_{lines}_stamp_plot.png"
    LOG.info("Writing %s", pngfn)
    fig.savefig(pngfn)


if __name__ == "__main__":
    main()
