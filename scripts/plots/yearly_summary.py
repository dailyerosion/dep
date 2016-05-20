import datetime
import cStringIO
import psycopg2
from shapely.wkb import loads
import numpy as np
import sys
import matplotlib
matplotlib.use('agg')
from pyiem.plot import MapPlot
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import matplotlib.colors as mpcolors

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
V2RAMP = {
    'avg_loss': [0, 2.5, 5, 10, 20, 40, 60],
    'qc_precip': [15, 25, 35, 45, 55],
    'avg_delivery': [0, 2.5, 5, 10, 20, 40, 60],
    'avg_runoff': [0, 2.5, 5, 10, 15, 30],
    }

year = int(sys.argv[1])
v = sys.argv[2]
ts = datetime.date(year, 1, 1)
ts2 = datetime.date(year, 12, 31)
scenario = 0

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
m = MapPlot(axisbg='#EEEEEE', nologo=True, sector='iowa',
            title='DEP %s by HUC12 %s' % (V2NAME[v], title),
            caption='Daily Erosion Project')

# Check that we have data for this date!
cursor.execute("""
    SELECT value from properties where key = 'last_date_0'
""")
lastts = datetime.datetime.strptime(cursor.fetchone()[0], '%Y-%m-%d')
floor = datetime.date(2007, 1, 1)
cursor.execute("""
WITH data as (
  SELECT huc_12, sum("""+v+""")  as d from results_by_huc12
  WHERE scenario = %s and valid between %s and %s
  GROUP by huc_12)

SELECT ST_Transform(simple_geom, 4326), coalesce(d.d, 0)
from huc12 i LEFT JOIN data d
ON (i.huc_12 = d.huc_12) WHERE i.scenario = %s and i.states ~* 'IA'
""", (scenario, ts.strftime("%Y-%m-%d"),
      ts2.strftime("%Y-%m-%d"), scenario))
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
    bins = V2RAMP[v]
norm = mpcolors.BoundaryNorm(bins, cmap.N)
for val, patch in zip(data, patches):
    c = cmap(norm([val, ]))[0]
    patch.set_facecolor(c)

m.ax.add_collection(PatchCollection(patches, match_original=True))
m.drawcounties()
m.drawcities()
lbl = [round(_, 2) for _ in bins]
u = "%s, Avg: %.2f" % (V2UNITS[v], np.mean(data))
m.draw_colorbar(bins, cmap, norm, units=u,
                clevlabels=lbl)
ram = cStringIO.StringIO()
plt.savefig('%s_%s.png' % (year, v))
