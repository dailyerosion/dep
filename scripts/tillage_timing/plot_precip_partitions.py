"""Plot of 5 day averaged precipitation."""
import datetime

import pandas as pd
from pandas.io.sql import read_sql
from pyiem.plot.use_agg import plt
from pyiem.util import get_dbconn


def main():
    """Go Main Go."""
    myhucs = [x.strip() for x in open("myhucs.txt").readlines()]
    pgconn = get_dbconn("idep")
    df = read_sql(
        """
        SELECT extract(year from valid),
        extract(doy from valid)::int as doy,
        qc_precip
        from results_by_huc12 where scenario = 0 and
        valid < '2019-01-01' and valid >= '2008-01-01'
        and huc_12 in %s
    """,
        pgconn,
        params=(tuple(myhucs),),
    )

    (fig, ax) = plt.subplots(1, 1)
    # How many to average by
    total = 30.0 * 11.0
    # Create two week windows before and inclusive after a given date
    top = []
    bottom = []
    idxs = []
    for date in pd.date_range("2000/4/1", "2000/5/31"):
        idx = int(date.strftime("%j"))
        idxs.append(idx)
        sdoy = int((date - datetime.timedelta(days=20)).strftime("%j"))
        edoy = int((date + datetime.timedelta(days=20)).strftime("%j"))
        before = df[(df["doy"] >= sdoy) & (df["doy"] < idx)].sum() / total
        bottom.append(0 - before["qc_precip"])
        after = df[(df["doy"] >= idx) & (df["doy"] < edoy)].sum() / total
        top.append(after["qc_precip"])

    ax.bar(idxs, top, label="After Date")
    ax.bar(idxs, bottom, label="Before Date")
    ax.legend(loc=2, ncol=2)
    xticks = []
    xticklabels = []
    for date in pd.date_range("2000/4/5", "2000/5/30", freq="5d"):
        xticks.append(int(date.strftime("%j")))
        xticklabels.append(date.strftime("%b\n%-d"))
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels)
    ax.set_xlim(xticks[0] - 6, xticks[-1] + 3)
    # Force labels to update
    ax.set_ylim(-105, 105)
    ax.set_yticklabels(ax.get_yticks())
    labels = []
    for y in ax.get_yticklabels():
        val = float(y.get_text())
        if val < 0:
            val = 0 - val
        labels.append("%.0f" % (val,))
    ax.set_yticklabels(labels)
    ax.grid(True)
    ax.set_title("2008-2018 HUC12 Precipitation for 14 Day Periods")
    ax.set_ylabel("Precipitation per Year [mm]")

    fig.savefig("test.png")


if __name__ == "__main__":
    main()
