import matplotlib.pyplot as plt
from pandas.io.sql import read_sql
from pyiem.database import get_dbconn

pgconn = get_dbconn("idep")
df = read_sql(
    """
    SELECT * from results_by_huc12 where scenario in (0, 7, 9)
    and huc_12 = '102300031504' and valid >= '2008-01-01'
    and valid < '2016-01-01' ORDER by valid ASC
    """,
    pgconn,
    index_col=None,
)

(fig, ax) = plt.subplots(1, 1)
for scenario, label in zip(
    [0, 7, 9], ["Baseline", "UCS 4 Year", "UCS 3 Year"]
):
    df2 = df[df["scenario"] == scenario]
    x = []
    y = []
    accum = 0
    for _, row in df2.iterrows():
        x.append(row["valid"])
        accum += row["avg_loss"] * 4.463
        y.append(accum)
    ax.plot(x, y, label="%s" % (label,))

ax.legend(loc="best")
ax.set_title("Accumulated Soil Detachment for 102300031504")
ax.set_ylabel("Soil Detachment [t/a]")
ax.grid(True)
fig.savefig("test.png")
