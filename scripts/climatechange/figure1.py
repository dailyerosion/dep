"""Simple plot of data."""
from matplotlib import rcParams

rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Liberation Sans"],
    }
)
from pyiem.plot.use_agg import plt

DATA = [-49, -41, -32, -21, -12, 0, 9, 21, 33, 46, 58]


def main():
    """Go Main Go."""
    (fig, ax) = plt.subplots(1, 1)
    ax.bar(range(len(DATA)), DATA, color="gray")
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
    ax.set_title(
        "Change in Hillslope Soil Loss by Precipitation Intensity Adjustment"
    )
    ax.set_xlabel("Precipitation Intensity Adjustment")
    ax.set_ylabel(r"Percent Change in Soil Loss (baseline: 7.8 $t$ $ha^{-1}$)")
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
    fig.savefig("figure1.png", dpi=600)


if __name__ == "__main__":
    main()
