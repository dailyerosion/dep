"""Go."""
import sys

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import pandas as pd
from pyiem.util import get_dbconn

YEAR = int(sys.argv[1])
pgconn = get_dbconn("idep")
cursor = pgconn.cursor()

# Load up HUC12s
HUC12s = []
cursor.execute(
    """
    SELECT distinct huc_12 from results where scenario = 5
    ORDER by huc_12"""
)
for row in cursor:
    HUC12s.append(row[0])


results = []
for huc12 in ["070600060701"]:  # HUC12s:
    cursor.execute(
        """
      SELECT hs_id, extract(year from valid) as yr,
      sum(runoff) as sum_runoff,
      sum(loss) as sum_loss, sum(delivery) as sum_delivery from results
      WHERE scenario = 5 and valid between '%s-01-01' and '%s-01-01'
      and huc_12 = '%s'
      GROUP by hs_id, yr

    """
        % (YEAR, YEAR + 1, huc12)
    )

    data = {}
    print("%s %s" % (huc12, cursor.rowcount))
    for row in cursor:
        fpath = row[0]
        if fpath < 100:
            catchment = 0
        else:
            catchment = int(str(fpath)[:-2])
        sample = int(str(fpath)[-2:])
        year = row[1]
        runoff = row[2]
        loss = row[3]
        delivery = row[4]

        res = data.setdefault(
            catchment, {"runoff": [], "loss": [], "delivery": []}
        )
        res["runoff"].append(runoff)
        res["loss"].append(loss * 10.0)
        res["delivery"].append(delivery * 10.0)

    (fig, ax) = plt.subplots(1, 1, figsize=(8, 6))

    averages = []
    for i in range(10):
        averages.append([])

    for i in range(10):
        for catchment in data:
            if len(data[catchment]["loss"]) <= i:
                continue
            for val in data[catchment]["loss"][: i + 1]:
                averages[i].append(val)

    ax.grid(axis="y")
    ax.text(
        0.02,
        0.95,
        "Average",
        color="b",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        bbox=dict(color="white"),
    )
    ax.text(
        0.02,
        0.9,
        "Median",
        color="r",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        bbox=dict(color="white"),
    )
    d = ax.boxplot(averages, widths=0.7)
    for i, a in enumerate(averages):
        ax.text(
            i + 1,
            np.average(a),
            "%.2f" % (np.average(a),),
            ha="center",
            va="bottom",
            color="b",
            fontsize=10,
        )
        ax.text(
            i + 1,
            np.median(a) + 0.05,
            "%.2f" % (np.median(a),),
            ha="center",
            va="bottom",
            color="r",
            fontsize=10,
        )

    ax.set_title(
        "Convergence Study: %s %s Detachment Estimates" % (huc12, YEAR)
    )
    ax.set_ylabel("Soil Detachment (Mg/ha)")
    ax.set_xlabel("Sub-catchment Sample Size, T-test based on 10 sample avg")

    box = ax.get_position()
    ax.set_position(
        [box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9]
    )
    labels = ["#\nT\nP"]
    for i in range(10):
        x = stats.ttest_1samp(averages[i], np.average(averages[-1]))
        labels.append("%s\n%.3f\n%.3f" % (i + 1, x[0], x[1]))

    results.append(
        dict(
            huc12=huc12,
            one=np.average(averages[0]),
            ten=np.average(averages[-1]),
        )
    )
    ax.set_xticks(range(11))
    ax.set_xticklabels(labels)
    ax.set_ylim(bottom=-3)
    fig.savefig("%s_%s.pdf" % (huc12, YEAR), dpi=600)
    plt.close()

# df = pd.DataFrame(results)
# df.to_csv('results.csv')
df = pd.read_csv("results.csv")
(fig, ax) = plt.subplots(1, 1)
ax.scatter(df["one"].values * 10.0, df["ten"].values * 10.0)
ax.plot([0, 120], [0, 120], lw=2, color="k")
ax.set_xlabel("Soil Detachment with 1 Sample (Mg/ha)")
ax.set_ylabel("Soil Detachment with 10 Samples (Mg/ha)")
ax.grid(True)
ax.set_title("DEP 30 HUC12 Convergence Test for 2014")
fig.savefig("Figure6.pdf", dpi=600)
