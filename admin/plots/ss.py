#!/usr/bin/env python
""" Scenario Scatter """
import cgi
import cStringIO
import sys
from pyiem.util import get_dbconn


def make_plot(huc_12):
    """ Generate the plot please """
    import psycopg2
    import matplotlib

    matplotlib.use("agg")
    import matplotlib.pyplot as plt

    (fig, ax) = plt.subplots(1, 1)

    IDEPDB = get_dbconn("idep")
    cursor = IDEPDB.cursor()

    res = [[], [], []]
    cursor.execute(
        """
    SELECT scenario, yr, avg(sum) from
    (SELECT scenario, huc_12, extract(year from valid) as yr,
    sum(avg_loss) from results_by_huc12
    WHERE substr(huc_12,1,8) = %s and avg_loss > 0 
    GROUP by scenario, huc_12, yr) as foo
    GROUP by scenario, yr""",
        (huc_12[:8],),
    )
    for row in cursor:
        res[row[0]].append(row[2] * 4.463)

    ax.boxplot([res[0], res[1], res[2]])
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(["IDEPv2-current", "G4", "FullLength Test"])
    ax.set_ylabel("Displacement [t/a]")
    ax.set_title("Yearly Average Displacement for HUC8: %s" % (huc_12[:8],))
    ax.grid(True)

    ram = cStringIO.StringIO()
    plt.savefig(ram, format="png")
    ram.seek(0)
    r = ram.read()

    sys.stdout.write("Content-type: image/png\n\n")
    sys.stdout.write(r)


if __name__ == "__main__":
    # Go Main Go
    form = cgi.FieldStorage()
    huc_12 = form.getfirst("huc_12", "070200090401")

    make_plot(huc_12)
