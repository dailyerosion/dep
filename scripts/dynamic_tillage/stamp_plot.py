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
    jumbo = pd.read_csv(f"plots/{crop}_progress.csv", parse_dates=["date"])
    jumbo["dayofyear"] = jumbo["date"].dt.dayofyear

    _title = (
        f"{crop.capitalize()} Planting Progress ({lines} Lines, {dots} Dots)"
    )

    fig, ax = figure_axes(
        title="",
        logo=None,
        figsize=(10, 8),
    )
    ax.set_position([0.08, 0.1, 0.77, 0.77])
    # Remove all splines
    for side in ["top", "right", "left", "bottom"]:
        ax.spines[side].set_visible(False)

    lyear = 2021 if "deines2023" in (dots, lines) else 2026
    cols = float(lyear - 2008)

    # Sequential color scheme: dark green (best) → red (worst)
    # Removes problematic yellow for better visibility
    cmap = mpcolors.ListedColormap(
        ["#1a9850", "#91cf60", "#fc8d59", "#d73027"]
    )
    norm = mpcolors.BoundaryNorm([0, 10, 20, 35, 60], cmap.N)
    dotcol = f"{dots}_{crop}_pct"
    linecol = f"{lines}_{crop}_pct"
    datums = (
        "IA_SW IA_SC IA_SE IA_WC IA_C IA_EC IA_NW IA_NC IA_NE IA MN NE"
    ).split()
    colors = (
        "red blue green orange tan purple brown pink skyblue black gray white"
    ).split()
    if lines == "dep" and dots == "deines2023":
        datums = (
            "NE_NE",
            "NE_EC",
            "NE_SE",
            "MN_SW",
            "MN_SC",
            "MN_SE",
            "MN_WC",
            "MN_C",
            "MN_NW",
        )
        colors = colors[:9]
    xtilesize = 1.0 / cols
    ytilesize = 1.0 / len(datums)

    for x, year in enumerate(range(2008, lyear)):
        # Psuedo axis definition
        x0 = x / cols
        xmin = pd.Timestamp(f"{year}-04-11").dayofyear
        xmax = pd.Timestamp(f"{year}-06-15").dayofyear
        for y, (datum, _color) in enumerate(
            zip(
                datums,
                colors,
                strict=True,
            )
        ):
            # Psuedo axis definition
            y0 = y / len(datums)
            df = jumbo[
                (jumbo["date"].dt.year == year)
                & (jumbo["datum"] == datum)
                & (jumbo["dayofyear"] >= xmin)
                & (jumbo["dayofyear"] <= xmax)
            ]
            if df.empty:
                continue
            # Calculate RMSE
            _rmse = ((df[dotcol] - df[linecol]).pow(2).mean()) ** 0.5
            mae = (df[dotcol] - df[linecol]).abs().mean()
            background_color = cmap(norm(mae))
            # Colored border to indicate MAE
            ax.add_patch(
                Rectangle(
                    (x0, y0),
                    xtilesize,
                    ytilesize,
                    color=background_color,
                    alpha=1,
                    fill=False,
                    linewidth=2.5,
                    zorder=6,
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
            # MAE text in colored box
            ax.text(
                x0 + 0.98 * xtilesize,
                y0 + 0.02 * ytilesize,
                f"{mae:.0f}",
                ha="right",
                va="bottom",
                color="white",
                fontsize=9,
                weight="bold",
                bbox=dict(
                    boxstyle="round,pad=0.25",
                    facecolor=background_color,
                    edgecolor="none",
                    alpha=0.95,
                    pad=2,
                ),
                zorder=5,
            )

    ax.set_xticks(numpy.arange(0, 0.99, 1.0 / cols) + xtilesize / 2.0)
    ax.set_xticklabels(
        range(2008, lyear),
        rotation=45,
        fontsize=14,
    )
    ax.set_yticks(numpy.arange(0, 0.99, 1.0 / len(datums)) + ytilesize / 2.0)
    ax.set_yticklabels(
        datums,
        rotation=0,
        ha="right",
        fontsize=14,
    )
    # Add gridlines
    for x in numpy.arange(0, 1.1, 1.0 / cols):
        ax.axvline(x, color="k", lw=0.5)
    for y in numpy.arange(0, 1.01, 1.0 / len(datums)):
        ax.axhline(y, color="k", lw=0.5)
    ax.set_xlim(-0.01, 1.01)
    ax.set_ylim(-0.01, 1.01)

    # Add colorbar
    ax2 = fig.add_axes((0.88, 0.1, 0.02, 0.77))
    cb = fig.colorbar(
        mpcm.ScalarMappable(norm=norm, cmap=cmap),
        cax=ax2,
        orientation="vertical",
        spacing="proportional",
    )
    # Set the fontsize
    cb.ax.tick_params(labelsize=14)
    cb.set_label(
        f"MAE of {dots} vs {lines} Planting Progress [percentage points]",
        fontsize=14,
    )

    # plots is symlinked
    pngfn = f"plots/{crop}_{dots}_{lines}_stamp_plot.png"
    LOG.info("Writing %s", pngfn)
    fig.savefig(pngfn, dpi=300)


if __name__ == "__main__":
    main()
