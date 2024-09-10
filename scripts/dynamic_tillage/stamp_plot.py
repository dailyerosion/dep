"""Create a Postage Stamp Plot of all the years of data."""

import glob

import click
import matplotlib.cm as mpcm
import matplotlib.colors as mpcolors
import numpy
import pandas as pd
from matplotlib.patches import Rectangle
from pyiem.plot import figure_axes, get_cmap
from pyiem.plot.use_agg import plt


@click.command()
@click.option("--crop", default="corn", help="Which crop to process")
def main(crop: str):
    """Go main Go."""
    dfs = []
    for csvfn in glob.glob(f"plotsv3/{crop}_*.csv"):
        _, _, datum = csvfn[:-4].split("_")
        progress = pd.read_csv(csvfn, parse_dates=["valid"])
        progress["datum"] = datum
        dfs.append(progress)
    jumbo = pd.concat(dfs)
    jumbo["dayofyear"] = jumbo["valid"].dt.dayofyear
    fig, ax = figure_axes(
        title="Corn Planting Progress (DEP Lines, NASS Dots)",
        logo="dep",
        figsize=(10, 8),
    )
    ax.set_position([0.05, 0.07, 0.85, 0.83])
    # Remove all splines
    for side in ["top", "right", "left", "bottom"]:
        ax.spines[side].set_visible(False)

    xtilesize = 1.0 / 18.0
    ytilesize = 1.0 / 11.0
    cmap = get_cmap("RdYlGn_r")
    norm = mpcolors.BoundaryNorm([0, 10, 40, 70, 100], cmap.N)
    for x, year in enumerate(range(2007, 2025)):
        # Psuedo axis definition
        x0 = x / 18.0
        xmin = pd.Timestamp(f"{year}-04-11").dayofyear
        xmax = pd.Timestamp(f"{year}-06-15").dayofyear
        for y, (district, _color) in enumerate(
            zip(
                "sw sc se wc c ec nw nc ne IA MN".split(),
                (
                    "red blue green orange tan purple "
                    "brown pink skyblue black gray"
                ).split(),
            )
        ):
            # Psuedo axis definition
            y0 = y / 11.0
            df = jumbo[
                (jumbo["valid"].dt.year == year)
                & (jumbo["datum"] == district)
                & (jumbo["dayofyear"] >= xmin)
                & (jumbo["dayofyear"] <= xmax)
            ]
            nass = df[df["corn planted"].notna()]
            # Calculate RMSE
            rmse = (
                (nass["corn planted"] - nass["dep_corn_planted"]).pow(2).mean()
            ) ** 0.5
            mae = (
                (nass["corn planted"] - nass["dep_corn_planted"]).abs().mean()
            )
            print(f"{year} {district} RMSE: {rmse:.2f} MAE: {mae:.2f}")
            background_color = cmap(norm(mae))
            ax.add_patch(
                Rectangle(
                    (x0, y0),
                    xtilesize,
                    ytilesize,
                    color=background_color,
                    alpha=0.5,
                )
            )
            ax.plot(
                x0 + (df["dayofyear"] - xmin) / (xmax - xmin) * xtilesize,
                y0 + df["dep_corn_planted"] / 100.0 * ytilesize,
                color="k",
            )
            ax.scatter(
                x0 + (nass["dayofyear"] - xmin) / (xmax - xmin) * xtilesize,
                y0 + nass["corn planted"] / 100.0 * ytilesize,
                color="k",
                s=5,
            )
            ax.text(
                x0 + 0.5 * xtilesize,
                y0 + 0.5 * ytilesize,
                f"{mae:.0f}",
                ha="center",
                va="center",
                color="b",
                fontsize=14,
            )

    ax.set_xticks(numpy.arange(0, 0.99, 1.0 / 18.0) + xtilesize / 2.0)
    ax.set_xticklabels(range(2007, 2025), rotation=45)
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
    for x in numpy.arange(0, 1.1, 1.0 / 18.0):
        ax.axvline(x, color="k", lw=0.5)
    for y in numpy.arange(0, 1.01, 1.0 / 11.0):
        ax.axhline(y, color="k", lw=0.5)
    ax.set_xlim(-0.01, 1.01)
    ax.set_ylim(-0.01, 1.01)

    # Add colorbar
    ax2 = fig.add_axes((0.9, 0.1, 0.02, 0.8))
    cb = plt.colorbar(
        mpcm.ScalarMappable(norm=norm, cmap=cmap),
        cax=ax2,
        orientation="vertical",
        alpha=0.5,
    )
    cb.set_label("MAE of NASS vs DEP Planting Progress [%]")

    fig.savefig("plotsv3/stamp_plot.png")


if __name__ == "__main__":
    main()
