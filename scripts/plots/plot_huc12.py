'''
Explore mapping IDEPv1 data direct from the database with matplotlib
'''
from pyiem.plot import MapPlot, maue, james2, james
from shapely.wkb import loads
import psycopg2
import sys
import numpy as np
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import matplotlib.colors as mpcolors
import matplotlib.cm as cm

DBCONN = psycopg2.connect(database='idep')
cursor = DBCONN.cursor()

orig = {}
for line in open('/tmp/flowpathcounts.txt'):
    tokens = line.split()
    orig[tokens[0]] = float(tokens[1])

m = MapPlot(sector='iowa', axisbg='white', nologo=True,
            #subtitle='IDEPv2 minus IDEPv1',
            title='IDEPv2 %s of Valid Flowpaths vs Gelder Provided by HUC12'  )



cursor.execute("""
 WITH data as (
  select huc_12, count(*) from flowpaths where scenario = 0 
  GROUP by huc_12
  )

 SELECT ST_Transform(geom, 4326), d.huc_12, d.count from 
 huc12 h JOIN data d on (d.huc_12 = h.huc_12) WHERE h.scenario = 0
 ORDER by count DESC

""")

bins = np.arange(80,101,5)
#cmap = cm.get_cmap('BrBG')
#cmap.set_under('orange')
#cmap.set_over('black')
cmap = james()
cmap.set_under('white')
cmap.set_over('black')
norm = mpcolors.BoundaryNorm(bins, cmap.N)
patches = []
for row in cursor:
    #print "%s,%s" % (row[2], row[1])
    geom = loads( row[0].decode('hex') )
    for polygon in geom:
        a = np.asarray(polygon.exterior)
        x,y = m.map(a[:,0], a[:,1])
        a = zip(x,y)
        percentage = row[2] / orig[row[1]] * 100.0
        if percentage < 90:
            print "%s %.1f %s/%s" % (row[1], percentage, row[2], orig[row[1]])
        c = cmap( norm([percentage,] ))[0]
        p = Polygon(a,fc=c,ec='None',zorder=2, lw=.1)
        patches.append(p)

          
m.ax.add_collection(PatchCollection(patches,match_original=True))
m.draw_colorbar(bins, cmap, norm, units='%s')

m.drawcounties()
m.postprocess(filename='test.png')