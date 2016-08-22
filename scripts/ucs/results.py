import psycopg2
import numpy as np
import sys
import matplotlib.pyplot as plt
from pandas.io.sql import read_sql

years = 8.0
scenario = int(sys.argv[1])
pgconn = psycopg2.connect(database='idep', host='iemdb', user='nobody')

df = read_sql("""SELECT r.huc_12, r.scenario,
    sum(avg_loss) * 4.463 as detach
    from results_by_huc12 r
    , huc12 h WHERE r.huc_12 = h.huc_12 and h.states ~* 'IA'
    and r.scenario in (0, %s) and h.scenario = 0 and r.valid < '2016-01-01'
    and r.valid > '2008-01-01'
    GROUP by r.scenario, r.huc_12
    ORDER by detach DESC
    """, pgconn, params=(scenario,), index_col=None)

s0 = df[df['scenario'] == 0].copy()
s0.set_index('huc_12', inplace=True)
s0.rename(columns={'detach': 'detach_s0', 'scenario': 'scenario_s0'},
          inplace=True)
s7 = df[df['scenario'] == scenario].copy()
s7.set_index('huc_12', inplace=True)
s7.rename(columns={'detach': 'detach_s7', 'scenario': 'scenario_s7'},
          inplace=True)

df = s0.join(s7)
df.sort_values(by='detach_s0', ascending=False, inplace=True)

d0 = df['detach_s0'].values
d7 = df['detach_s7'].values

sz = len(df.index)
x = np.arange(0, sz)
y = []
key = sz / 4
minval = [0, 1000.]
for i in range(0, sz):
    d0[i] = d7[i]
    thisy = np.average(d0) / years
    y.append(thisy)
    if thisy < minval[1]:
        minval = [i, thisy]
    if i == key:
        print y[0], y[i], (y[0] - y[i]) / y[0] * 100.

print minval[0] / float(sz) * 100., (y[0] - minval[1]) / y[0] * 100.

(fig, ax) = plt.subplots(1, 1)

ax.set_ylabel("Yearly Soil Detachment [tons/acre]")
ax.set_xlabel("Percentage of the State Converted [%]")
ax.set_title(("Iowa Daily Erosion Project :: UCS 4 Year Scenario\n"
              "Sequential replacement of most erosive HUC12s with scenario"))
ax.plot(x / float(x[-1]) * 100., y)
ax.grid(True)
ax.set_xticks([0, 5, 10, 25, 50, 75, 90, 95, 100])

fig.savefig('test.png')
