import psycopg2
import matplotlib.pyplot as plt
import numpy as np
import sys
from scipy import stats

YEAR = int(sys.argv[1])
pgconn = psycopg2.connect(database='idep')
cursor = pgconn.cursor()

cursor.execute("""
  SELECT hs_id, huc_12, extract(year from valid) as yr,
  sum(runoff) as sum_runoff,
  sum(loss) as sum_loss, sum(delivery) as sum_delivery from results
  WHERE scenario = 5 and valid between '%s-01-01' and '%s-01-01'
  GROUP by hs_id, huc_12, yr

""" % (YEAR, YEAR + 1))

data = {}
print cursor.rowcount
for row in cursor:
    fpath = row[0]
    if fpath < 100:
        catchment = 0
    else:
        catchment = int(str(fpath)[:-2])
    sample = int(str(fpath)[-2:])
    huc_12 = row[1]
    year = row[2]
    runoff = row[3]
    loss = row[4]
    delivery = row[5]

    if huc_12 not in data:
        data[huc_12] = dict()
    if catchment not in data[huc_12]:
        data[huc_12][catchment] = {'runoff': [], 'loss': [], 'delivery': []}
    data[huc_12][catchment]['runoff'].append(runoff)
    data[huc_12][catchment]['loss'].append(loss)
    data[huc_12][catchment]['delivery'].append(delivery)

(fig, ax) = plt.subplots(1, 1)

averages = []
for i in range(10):
    averages.append([])

for huc_12 in data:
    for i in range(10):
        samples = []
        for catchment in data[huc_12]:
            if len(data[huc_12][catchment]['loss']) <= i:
                continue
            samples.append(np.average(data[huc_12][catchment]['loss'][:i+1]))
        averages[i].append(np.average(samples))

ax.grid(axis='y')
d = ax.boxplot(averages)
for i, a in enumerate(averages):
    ax.text(i+1, np.average(a), "%.2f" % (np.average(a), ), ha='center',
            va='bottom', color='b', fontsize=10)
    ax.text(i+1, np.median(a), "%.2f" % (np.median(a), ), ha='center',
            va='bottom', color='r', fontsize=10)

ax.set_title("Convergence Study: %s Loss Estimates" % (YEAR, ))
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

fig.savefig('test.png')
