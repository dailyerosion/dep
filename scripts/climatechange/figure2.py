"""Simple plot of data."""
from pyiem.plot.use_agg import plt

DATA = [
    0.10443217650431767,
    0.097604593311172,
    0.08620678890467993,
    0.0836352547099746,
    0.07519827993697677,
    0.06791704487449034,
    0.0667185391504379,
    0.04642169443164995,
    0.04371219741072408,
    0.04069508509945578,
    0.03913181642206167,
    0.031348611598473165,
    0.0128827209211712,
    0.004378296775486867,
    0,
    -0.00202122615829433,
    -0.017385351050829122,
    -0.02270079464303605,
    -0.027487343349923008,
    -0.03284906755205476,
    -0.03002016125108538,
    -0.03653645476883498,
    -0.03346653823111135,
    -0.03891078221802415,
    -0.05119813364781085,
    -0.0549142855673828,
    -0.05426015852858575,
    -0.053857378857276594,
    -0.05854400882394952,
]


def main():
    """Go Main Go."""
    (fig, ax) = plt.subplots(1, 1)
    ax.bar(range(-14, 15), [x * 100 for x in DATA])
    ax.grid(True)
    ax.set_title(
        "Change in Hillslope Soil Loss by -/+ 14 Day Precipitation Shift"
    )
    ax.set_xlabel("Shift in Days (negative is earlier)")
    ax.set_ylabel("Percent Change in Soil Loss (baseline: 7.8 $t$ $ha^{-1}$)")
    ax.set_ylim(-12, 12)
    ax.axhline(0, color="k")
    fig.savefig("figure2.png")


if __name__ == "__main__":
    main()
