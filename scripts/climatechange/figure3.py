"""A plot of the deltas for erosion between scenarios."""
from matplotlib import rcParams
from pyiem.plot import figure_axes
from pyiem.util import logger
import numpy as np

rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Liberation Sans"],
    }
)

LOG = logger()

DATA = [
    0.07532299938501776,
    0.15766216345170533,
    0.24007253103022136,
    0.3350761437226657,
    0.42331557042071166,
    0.53209366910133,
    0.6315990841977428,
    0.7482604383664925,
    0.8539429154383379,
    0.9631476509401304,
]


def main():
    """Plot."""
    title = (
        "Change in Hillslope Soil Loss\n"
        "with Additional 1 $inch$ $h^{-1}$ Daily Events"
    )
    fig, ax = figure_axes(
        logo="dep",
        figsize=(8, 6),
        title=title,
    )
    y = np.array(DATA) * 100.0
    ax.bar(np.arange(1, 11), y, color="b")
    for i, val in enumerate(y):
        ax.text(
            i + 1,
            val + 3,
            f"{val:.0f}%",
            ha="center",
            bbox=dict(color="white", boxstyle="square,pad=0"),
        )
    ax.set_xlabel(
        "Additional 1 $inch$ $h^{-1}$ Storms per Spring Season each Year"
    )
    ax.set_ylim(0, 110)
    # ylabel = r"Percent Change in Soil Loss (baseline: 7.8 $t$ $ha^{-1}$)"
    ylabel = r"Percent Change in Soil Loss (baseline: 3.0 $T$ $a^{-1}$)"
    ax.set_ylabel(ylabel)
    ax.set_xticks(range(1, 11))
    ax.grid(True)
    fig.savefig("figure3.png")


if __name__ == "__main__":
    main()
