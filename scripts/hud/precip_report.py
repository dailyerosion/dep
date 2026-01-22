"""Generate a precip report for the HUD project"""

import matplotlib.pyplot as plt
from pandas.io.sql import read_sql
from pyiem.database import get_dbconn

HUCS = """
Headwaters Cedar Creek 071000060202
Outlet Creek 071000060307
Bear Creek-Cedar River 070802051004
Lime Creek 070802051003
Hinkle Creek 070802051102
Mud Creek 070802050907
Opossum Creek 070802051201
Wildcat Creek 070802051202
Devils Run-Wolf Creek 070802050808
Twelvemile Creek 070802050807
Headwaters North English 070802090401
Upper Clear Creek 070802090101
Middle Clear Creek 070802090102
Lower Clear Creek 070802090103
Middle North English River 070802090406
Middle English River 070802090302
Gritter Creek 070802090301"""

AVGS = [
    1.23 + 1.21 + 2.25,
    3.42 + 4.19 + 4.73,
    4.37 + 3.92 + 3.60,
    2.66 + 2.03 + 1.50,
]


def get_hucinfo():
    """Make our table"""
    res = []
    for line in HUCS.split("\n"):
        if len(line) < 10:
            continue
        tokens = line.rsplit(" ", 1)
        res.append(tokens)
    return res


def main():
    """Go Main Go"""
    hucinfo = get_hucinfo()
    hucs = [y for _x, y in hucinfo]
    pgconn = get_dbconn("idep")
    df = read_sql(
        """
    SELECT huc_12, extract(month from valid) as mo,
    sum(qc_precip) / 25.4 as rain
    from results_by_huc12 WHERE scenario = 0 and
    valid >= '2017-01-01' and valid < '2018-01-01'
    and huc_12 in %s
    GROUP by huc_12, mo
    """,
        pgconn,
        params=(tuple(hucs),),
        index_col=["huc_12", "mo"],
    )
    fig = plt.figure(figsize=(9.0, 6.0))
    fig.text(
        0.5,
        0.95,
        "DEP Selected HUC12 2017 Quarterly Precipitation Totals",
        ha="center",
        fontsize=14,
    )
    ax1 = fig.add_axes([0.23, 0.1, 0.15, 0.8])
    ax1.text(0, 1.01, "Jan, Feb, Mar", transform=ax1.transAxes)
    ax1.set_yticks(range(len(hucs)))
    ax1.set_yticklabels([x for x, _y in hucinfo])
    ax1.grid(True, zorder=1)
    ax1.axvline(AVGS[0], color="r", lw=2, zorder=3)

    ax2 = fig.add_axes([0.43, 0.1, 0.15, 0.8])
    ax2.set_yticks(range(len(hucs)))
    ax2.set_yticklabels([])
    ax2.grid(True, zorder=1)
    ax2.text(0, 1.01, "Apr, May, Jun", transform=ax2.transAxes)
    ax2.axvline(AVGS[1], color="r", lw=2, zorder=3)

    ax3 = fig.add_axes([0.63, 0.1, 0.15, 0.8])
    ax3.text(0, 1.01, "Jul, Aug, Sep", transform=ax3.transAxes)
    ax3.set_yticks(range(len(hucs)))
    ax3.set_yticklabels([])
    ax3.grid(True, zorder=1)
    ax3.axvline(AVGS[2], color="r", lw=2, zorder=3)

    ax4 = fig.add_axes([0.83, 0.1, 0.15, 0.8])
    ax4.text(0, 1.01, "Oct, Nov, Dec", transform=ax4.transAxes)
    ax4.set_yticks(range(len(hucs)))
    ax4.set_yticklabels([])
    ax4.grid(True, zorder=1)
    ax4.axvline(AVGS[3], color="r", lw=2, zorder=3)

    for mo, ax in zip([1, 4, 7, 10], [ax1, ax2, ax3, ax4], strict=False):
        vals = []
        for huc in hucs:
            vals.append(
                (
                    df.at[(huc, mo), "rain"]
                    + df.at[(huc, mo + 1), "rain"]
                    + df.at[(huc, mo + 2), "rain"]
                )
            )
        ax.barh(range(len(hucs)), vals, zorder=2)
        ax.set_xticks(range(0, int(max(vals)) + 1, 1 if max(vals) < 9 else 2))
        ax.set_xlabel("Precip [inch]")
    fig.text(
        0.02,
        0.02,
        "Red Line is Climatology\nbased on 1893-2017 Data",
        color="red",
    )
    fig.savefig("test.png")


if __name__ == "__main__":
    main()
