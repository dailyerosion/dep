"""Simple plot of data."""
from matplotlib import rcParams

rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Liberation Sans"],
    }
)
from pyiem.plot import figure_axes
from pyiem.plot.use_agg import plt

DATA = [-8.1, -6.3, -4.6, -2.9, -1.3, 0, 1.8, 3.3, 4.8, 6.3, 7.7]


def main():
    """Go Main Go."""
    title = (
        "Change in Hillslope Soil Loss\n"
        "by Precipitation Intensity Adjustment with Conserved Total Precip"
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
            "%i%%" % (val,),
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
    fig.savefig("figure4.png")


if __name__ == "__main__":
    main()
