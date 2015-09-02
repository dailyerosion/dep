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

V2NAME = {
    'avg_loss': 'Detachment',
    'qc_precip': 'Precipitation',
    'avg_delivery': 'Delivery',
    'avg_runoff': 'Runoff'}
V2MULTI = {
    'avg_loss': 4.463,
    'qc_precip': 1. / 25.4,
    'avg_delivery': 4.463,
    'avg_runoff': 1. / 25.4,
    }
V2UNITS = {
    'avg_loss': 'tons/acre',
    'qc_precip': 'inches',
    'avg_delivery': 'tons/acre',
    'avg_runoff': 'inches',
    }


def make_map(ts, ts2, scenario, v):
    """Make the map"""
    import matplotlib
    matplotlib.use('agg')
    from pyiem.plot import MapPlot
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    from matplotlib.collections import PatchCollection
    import matplotlib.colors as mpcolors

    # suggested for runoff and precip
    if v in ['qc_precip', 'avg_runoff']:
        c = ['#ffffa6', '#9cf26d', '#76cc94', '#6399ba', '#5558a1']
    # suggested for detachment
    elif v in ['avg_loss']:
        c = ['#cbe3bb', '#c4ff4d', '#ffff4d', '#ffc44d', '#ff4d4d', '#c34dee']
    # suggested for delivery
    elif v in ['avg_delivery']:
        c = ['#ffffd2', '#ffff4d', '#ffe0a5', '#eeb74d', '#ba7c57', '#96504d']
    cmap = mpcolors.ListedColormap(c, 'james')
    cmap.set_under('white')
    cmap.set_over('black')

    pgconn = psycopg2.connect(database='idep', host='iemdb', user='nobody')
    cursor = pgconn.cursor()

    title = "for %s" % (ts.strftime("%-d %B %Y"),)
    if ts != ts2:
        title = "for period between %s and %s" % (ts.strftime("%-d %b %Y"),
                                                  ts2.strftime("%-d %b %Y"))
    m = MapPlot(axisbg='#EEEEEE', nologo=True, sector='custom',
                south=38.2, north=44.9, west=-97.7, east=-89.1,
                title='DEP %s by HUC12 %s' % (V2NAME[v], title),
                caption='Daily Erosion Project')

    # Check that we have data for this date!
    cursor.execute("""
        SELECT value from properties where key = 'last_date_0'
    """)
    lastts = datetime.datetime.strptime(cursor.fetchone()[0], '%Y-%m-%d')
    floor = datetime.date(2007, 1, 1)
    if ts > lastts.date() or ts2 > lastts.date() or ts < floor:
        m.ax.text(0.5, 0.5, "Data Not Available\nPlease Check Back Later!",
                  transform=m.ax.transAxes, fontsize=20, ha='center')
        ram = cStringIO.StringIO()
        plt.savefig(ram, format='png', dpi=100)
        ram.seek(0)
        return ram.read(), False
    cursor.execute("""
    WITH data as (
      SELECT huc_12, sum("""+v+""")  as d from results_by_huc12
      WHERE scenario = %s and valid between %s and %s
      GROUP by huc_12)

    SELECT ST_Transform(simple_geom, 4326), coalesce(d.d, 0)
    from ia_huc12 i LEFT JOIN data d
    ON (i.huc_12 = d.huc_12)""", (scenario, ts.strftime("%Y-%m-%d"),
                                  ts2.strftime("%Y-%m-%d")))
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
    data = np.array(data) * V2MULTI[v]
    if np.max(data) < 0.01:
        bins = [0.01, 0.02, 0.03, 0.04, 0.05]
    else:
        bins = np.percentile(data[np.nonzero(data)], [20, 40, 60, 80, 100])
        bins = np.concatenate(([np.min(np.where(data > 0, data, 999)), ],
                               bins))
        if bins[0] < 0.01:
            bins[0] = 0.01
        # Push up the last bin slightly, so that data included in ramp
        bins[-1] = bins[-1] + 0.01
        if bins[1] < 0.01:
            bins = np.linspace(bins[0], bins[-1], 6)
        bins = np.around(bins.astype('f'), 2)
    norm = mpcolors.BoundaryNorm(bins, cmap.N)
    for val, patch in zip(data, patches):
        c = cmap(norm([val, ]))[0]
        patch.set_facecolor(c)

    m.ax.add_collection(PatchCollection(patches, match_original=True))
    m.draw_colorbar(bins, cmap, norm, units=V2UNITS[v])
    ram = cStringIO.StringIO()
    plt.savefig(ram, format='png', dpi=100)
    ram.seek(0)
    return ram.read(), True


def main(argv):
    """Do something fun"""
    form = cgi.FieldStorage()
    year = form.getfirst('year', 2015)
    month = form.getfirst('month', 5)
    day = form.getfirst('day', 5)
    year2 = form.getfirst('year2', year)
    month2 = form.getfirst('month2', month)
    day2 = form.getfirst('day2', day)
    scenario = int(form.getfirst('scenario', 0))
    v = form.getfirst('v', 'avg_loss')

    ts = datetime.date(int(year), int(month), int(day))
    ts2 = datetime.date(int(year2), int(month2), int(day2))
    mckey = "/auto/map.py/%s/%s/%s/%s" % (ts.strftime("%Y%m%d"),
                                          ts2.strftime("%Y%m%d"), scenario,
                                          v)
    mc = memcache.Client(['iem-memcached:11211'], debug=0)
    res = mc.get(mckey)
    sys.stdout.write("Content-type: image/png\n\n")
    hostname = os.environ.get("SERVER_NAME", "")
    if not res or hostname == "dailyerosion.local":
        # Lazy import to help speed things up
        res, do_cache = make_map(ts, ts2, scenario, v)
        sys.stderr.write("Setting cache: %s" % (mckey,))
        if do_cache:
            mc.set(mckey, res, 3600)
    sys.stdout.write(res)

if __name__ == '__main__':
    # See how we are called
    main(sys.argv)
