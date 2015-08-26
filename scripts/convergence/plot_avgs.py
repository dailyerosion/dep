import psycopg2
import matplotlib.pyplot as plt
import numpy as np
import sys
from scipy import stats

YEAR = int(sys.argv[1])
pgconn = psycopg2.connect(database='idep')
cursor = pgconn.cursor()

# Load up HUC12s
HUC12s = []
cursor.execute("""SELECT distinct huc_12 from results where scenario = 5""")
for row in cursor:
    HUC12s.append(row[0])

for huc12 in HUC12s:
    cursor.execute("""
      SELECT hs_id, extract(year from valid) as yr,
      sum(runoff) as sum_runoff,
      sum(loss) as sum_loss, sum(delivery) as sum_delivery from results
      WHERE scenario = 5 and valid between '%s-01-01' and '%s-01-01'
      and huc_12 = '%s'
      GROUP by hs_id, yr

    """ % (YEAR, YEAR + 1, huc12))

    data = {}
    print huc12, cursor.rowcount
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

        res = data.setdefault(catchment, {'runoff': [], 'loss': [],
                                          'delivery': []})
        res['runoff'].append(runoff)
        res['loss'].append(loss)
        res['delivery'].append(delivery)

    (fig, ax) = plt.subplots(1, 1)

    averages = []
    for i in range(10):
        averages.append([])

    for i in range(10):
        for catchment in data:
            if len(data[catchment]['loss']) <= i:
                continue
            for val in data[catchment]['loss'][:i+1]:
                averages[i].append(val)

    ax.grid(axis='y')
    ax.text(0.98, 0.95, "Average", color='b', transform=ax.transAxes,
            ha='right', va='bottom', bbox=dict(color='white'))
    ax.text(0.98, 0.9, "Median", color='r', transform=ax.transAxes,
            ha='right', va='bottom', bbox=dict(color='white'))
    d = ax.boxplot(averages)
    for i, a in enumerate(averages):
        ax.text(i+1, np.average(a), "%.2f" % (np.average(a), ), ha='center',
                va='bottom', color='b', fontsize=10)
        ax.text(i+1, np.median(a)-0.05, "%.2f" % (np.median(a), ), ha='center',
                va='top', color='r', fontsize=10)

    ax.set_title("Convergence Study: %s %s Loss Estimates" % (huc12, YEAR))
    ax.set_ylabel("Loss - Displacement (kg m-2)")
    ax.set_xlabel("Sub-catchment Sample Size, T-test based on 10 sample avg")

    box = ax.get_position()
    ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width,
                     box.height * 0.9])
    labels = ["#\nT\nP"]
    for i in range(10):
        x = stats.ttest_1samp(averages[i], np.average(averages[-1]))
        labels.append("%s\n%.3f\n%.3f" % (i+1, x[0], x[1]))

    ax.set_xticks(range(11))
    ax.set_xticklabels(labels)
    ax.set_ylim(bottom=-3)
    fig.savefig('%s_%s.png' % (huc12, YEAR))
    plt.close()
