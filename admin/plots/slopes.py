#!/usr/bin/env python
""" Plot up a comparison of Slopes! """

import cgi
import memcache
import glob
import sys
from pyiem.util import get_dbconn


def read_slope(fn):
    lines = open(fn).readlines()
    data = []
    for line in lines:
        if len(line.strip()) == 0 or line[0] == "#":
            continue
        data.append(line)
    fplen = data[2].split()[0]
    xs = []
    slp = []
    travel = 0
    for i in range(3, len(data), 2):
        slen = float(data[i].split()[1])
        nums = data[i + 1].replace(",", "").split()
        for pos in nums[0 : len(nums) : 2]:
            xs.append(float(pos) * slen + travel)
        for pos in nums[1 : len(nums) : 2]:
            slp.append(float(pos))
        travel += slen
    h2 = [0]
    x2 = [0]
    for x, s in zip(xs, slp):
        h2.append(h2[-1] + (x - x2[-1]) * (0 - s))
        x2.append(x)

    return x2, h2


def make_plot(scenario, model_twp, huc_12, mc, mckey):
    import matplotlib

    matplotlib.use("agg")
    import matplotlib.pyplot as plt
    import cStringIO

    (fig, ax) = plt.subplots(2, 1)

    slopes2 = []
    for fn in glob.glob(
        "/i/%s/slp/%s/%s/*.slp" % (scenario, huc_12[:8], huc_12[8:])
    ):
        x, y = read_slope(fn)
        slopes2.append((y[-1] - y[0]) / (x[-1] - x[0]))
        ax[0].plot(x, y, color="r", zorder=1)

    IDEPDB = get_dbconn("idep")
    cursor = IDEPDB.cursor()

    cursor.execute(
        """SELECT label from scenarios where id = %s""", (scenario,)
    )
    slabel = cursor.fetchone()[0]
    ax[0].set_title(
        (
            "IDEP Slope Comparison (scenario:%s %s)"
            + "\nHUC12: %s MODEL_TWP: %s"
        )
        % (scenario, slabel, huc_12, model_twp)
    )

    WEPPDB = psycopg2.connect(database="wepp", host="iemdb", user="nobody")
    cursor = WEPPDB.cursor()

    cursor.execute("""SELECT id from nri WHERE model_twp = %s""", (model_twp,))
    slopes1 = []
    for row in cursor:
        x2, y2 = read_slope("/mnt/idep/data/slopes/%s.slp" % (row[0],))
        slopes1.append((y2[-1] - y2[0]) / (x2[-1] - x2[0]))
        ax[0].plot(x2, y2, color="b", zorder=3)

    ax[0].grid(True)
    ax[0].set_ylabel("Elevation $\Delta$ [m]")
    ax[0].set_xlabel("Length along slope [m]")

    ax[1].boxplot([slopes1, slopes2])
    ax[1].set_xticks([1, 2])
    ax[1].set_xticklabels(["IDEPv1 (Blue)", "IDEPv2 (Red)"])
    ax[1].set_ylabel("Slope Distribution [m/m]")
    ax[1].grid(True)

    ram = cStringIO.StringIO()
    plt.savefig(ram, format="png")
    ram.seek(0)
    r = ram.read()
    mc.set(mckey, r, time=86400)
    sys.stderr.write("memcached key %s set time %s" % (mckey, 86400))

    sys.stdout.write("Content-type: image/png\n\n")
    sys.stdout.write(r)


if __name__ == "__main__":
    # Go Main Go
    form = cgi.FieldStorage()
    model_twp = form.getfirst("model_twp", "T82NR39W")
    huc_12 = form.getfirst("huc_12", "102300070302")
    scenario = int(form.getfirst("scenario", 0))

    mc = memcache.Client(["iem-memcached:11211"], debug=0)
    mckey = "%s/idep/plots/slopes_%s_%s.png" % (scenario, model_twp, huc_12)
    res = mc.get(mckey)
    if res:
        sys.stdout.write("Content-type: image/png\n\n")
        sys.stdout.write(res)
    else:
        make_plot(scenario, model_twp, huc_12, mc, mckey)
