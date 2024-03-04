"""Simple plot of data."""

from matplotlib import rcParams
from pyiem.plot import figure_axes

rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Liberation Sans"],
    }
)

DATA = [-49, -41, -32, -21, -12, 0, 9, 21, 33, 46, 58]


def main():
    """Go Main Go."""
    title = (
        "Change in Hillslope Soil Loss\n"
        "by Precipitation Intensity Adjustment w/ Accumulation Change"
    )
    (fig, ax) = figure_axes(
        logo="dep",
        figsize=(8, 6),
        title=title,
    )
    ax.bar(range(len(DATA)), DATA, color="b")
    for i, val in enumerate(DATA):
        delta = -5 if val < 0 else 5
        if val == 0:
            continue
        ax.text(
            i,
            val + delta,
            f"{val:.0f}%",
            ha="center",
            va="center",
            bbox=dict(color="white"),
        )
    ax.grid(True)
    ax.set_xticks(range(len(DATA)))
    ax.set_xlabel("Precipitation Intensity Adjustment")
    # ylabel = r"Percent Change in Soil Loss (baseline: 7.8 $t$ $ha^{-1}$)"
    ylabel = r"Percent Change in Soil Loss (baseline: 3.0 $T$ $a^{-1}$)"
    ax.set_ylabel(ylabel)
    ax.set_xticklabels(
        [
            "-20%",
            "-16%",
            "-12%",
            "-8%",
            "-4%",
            "",
            "4%",
            "8%",
            "12%",
            "16%",
            "20%",
        ]
    )
    ax.grid(True)
    ax.set_ylim(-70, 70)
    ax.axhline(0, color="k")
    fig.savefig("figure1.png")


if __name__ == "__main__":
    main()
