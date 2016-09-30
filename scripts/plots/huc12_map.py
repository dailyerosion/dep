from pyiem.plot import MapPlot, nwsprecip
from shapely.wkb import loads
import psycopg2
import numpy as np
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import matplotlib.colors as mpcolors

DBCONN = psycopg2.connect(database='idep', host='iemdb', user='nobody')
cursor = DBCONN.cursor()


threshold = 2
m = MapPlot(sector='iowa', axisbg='white', nologo=True,
            subtitle='1 Jan 2013 thru 27 September 2016',
            title=('DEP Two Days with HUC12 Precip Total >= %s inches'
                   ) % (threshold,))

cursor.execute("""
 WITH data as (
    select huc_12, qc_precip,
      qc_precip +
      lag(qc_precip) OVER (PARTITION by huc_12 ORDER by valid ASC) as p1,
      qc_precip +
      lead(qc_precip) OVER (PARTITION by huc_12 ORDER by valid ASC) as p2,
      valid,
      lag(valid) OVER (PARTITION by huc_12 ORDER by valid ASC) as lag_valid,
      lead(valid) OVER (PARTITION by huc_12 ORDER by valid ASC) as lead_valid
    from results_by_huc12 where scenario = 0
    and valid > '2013-01-01'
), agg as (
    SELECT huc_12, count(*) as val
    from data where p1 > (%s * 25.4) and p2 < (%s * 25.4)
    GROUP by huc_12
)

 SELECT ST_Transform(simple_geom, 4326), d.val
 from huc12 i JOIN agg d on (d.huc_12 = i.huc_12) ORDER by val DESC

""", (threshold, threshold))

bins = np.arange(0, 29, 4)
cmap = nwsprecip()
cmap.set_under('white')
cmap.set_over('black')
norm = mpcolors.BoundaryNorm(bins, cmap.N)
patches = []

for row in cursor:
    # print "%s,%s" % (row[2], row[1])
    polygon = loads(row[0].decode('hex'))
    a = np.asarray(polygon.exterior)
    x, y = m.map(a[:, 0], a[:, 1])
    a = zip(x, y)
    # c = cmap( norm([float(row[1]),]) )[0]
    c = cmap(norm([float(row[1]), ]))[0]
    p = Polygon(a, fc=c, ec='None', zorder=2, lw=.1)
    patches.append(p)

m.ax.add_collection(PatchCollection(patches, match_original=True))
m.draw_colorbar(bins, cmap, norm, units='days')

m.drawcounties()
m.postprocess(filename='test.png')
