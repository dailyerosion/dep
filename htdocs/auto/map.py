#!/usr/bin/env python
"""Mapping Interface"""
import memcache
import sys
import cgi
import datetime
import os
import cStringIO
import psycopg2
from shapely.wkb import loads
import numpy as np


def make_map(ts, scenario, v):
    """Make the map"""
    from pyiem.plot import MapPlot
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    from matplotlib.collections import PatchCollection
    import matplotlib.colors as mpcolors

    c = ['#ffffa6', '#9cf26d', '#76cc94', '#6399ba', '#5558a1']
    cmap = mpcolors.ListedColormap(c, 'james')
    cmap.set_under('white')
    cmap.set_over('black')

    pgconn = psycopg2.connect(database='idep', host='iemdb', user='nobody')
    cursor = pgconn.cursor()

    m = MapPlot(axisbg='#EEEEEE', nologo=True,
                title='IDEPv2 2014 Precipitation by HUC12',
                caption='Daily Erosion Project')

    cursor.execute("""
    WITH data as (
      SELECT huc_12, sum(qc_precip) / 25.4 as d from results_by_huc12
      WHERE scenario = 0 and valid between '2014-01-01' and '2015-01-01'
      GROUP by huc_12)

    SELECT ST_Transform(simple_geom, 4326), d.d
    from ia_huc12 i LEFT JOIN data d
    ON (i.huc_12 = d.huc_12)""")
    patches = []
    data = []
    for row in cursor:
        polygon = loads(row[0].decode('hex'))
        a = np.asarray(polygon.exterior)
        (x, y) = m.map(a[:, 0], a[:, 1])
        a = zip(x, y)
        p = Polygon(a, fc='white', ec='k', zorder=2, lw=.1)
        patches.append(p)
        data.append(row[1])
    data = np.array(data)
    bins = np.percentile(data, [20, 40, 60, 80, 100])
    bins = np.concatenate(([np.min(np.where(data > 0, data, 999)), ], bins))
    bins = np.around(bins.astype('f'), 2)
    norm = mpcolors.BoundaryNorm(bins, cmap.N)
    for val, patch in zip(data, patches):
        c = cmap(norm([val, ]))[0]
        patch.set_facecolor(c)

    m.ax.add_collection(PatchCollection(patches, match_original=True))
    m.draw_colorbar(bins, cmap, norm, units='inches')
    ram = cStringIO.StringIO()
    plt.savefig(ram, format='png', dpi=100)
    ram.seek(0)
    return ram.read()


def main(argv):
    """Do something fun"""
    form = cgi.FieldStorage()
    year = form.getfirst('year', 2015)
    month = form.getfirst('month', 5)
    day = form.getfirst('day', 5)
    scenario = form.getfirst('scenario', 0)
    v = form.getfirst('v', 'loss')

    ts = datetime.date(int(year), int(month), int(day))
    mckey = "/auto/map.py/%s/%s/%s" % (ts.strftime("%Y%m%d"), scenario,
                                       v)
    mc = memcache.Client(['iem-memcached:11211'], debug=0)
    res = mc.get(mckey)
    sys.stdout.write("Content-type: image/png\n\n")
    hostname = os.environ.get("SERVER_NAME", "")
    if not res or hostname == "idep.local":
        # Lazy import to help speed things up
        res = make_map(ts, scenario, v)
        sys.stderr.write("Setting cache: %s" % (mckey,))
        mc.set(mckey, res, 3600)
    sys.stdout.write(res)

if __name__ == '__main__':
    # See how we are called
    main(sys.argv)
