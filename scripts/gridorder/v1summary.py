"""Summarize DEP v1 data, we have 2007 through 2015

The 2007, 2008, and 2009 data looks wonky now, lets just do 2010 thru 2015
"""

import matplotlib.pyplot as plt
from pandas.io.sql import read_sql
from pyiem.util import get_dbconn

pgconn = get_dbconn("wepp")

df = read_sql(
    """
    with sums as (
        select nri_id, sum(loss) / 6. as val from results r JOIN combos c
        ON (r.run_id = c.id) WHERE valid between '2010-01-01' and '2016-01-01'
        GROUP by nri_id)
    SELECT s.nri_id, s.val * 4.463 as delivery, n.len * 0.3048 as length
    from sums s JOIN nri n on (s.nri_id = n.id)
    """,
    pgconn,
    index_col="nri_id",
)

(fig, ax) = plt.subplots(1, 1)
ax.grid(True)
df["ilength"] = df["length"].astype("i") / 5
gdf = df.groupby("ilength").mean()
ax.plot(gdf.index.values * 5, gdf["delivery"], lw=2)

ax.set_xlim(0, 200)
ax.set_ylim(0, 25)
ax.legend(loc=2)
ax.set_xlabel("Flowpath Length, (5m bin averages)")
ax.set_title("*IDEP Version 1* Average Soil Delivery by Flowpath Length")
ax.set_ylabel("Soil Delivery [t/a per year]")
ax.set_xticks([0, 25, 50, 75, 100, 150, 200])
fig.savefig("test.png")
