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


m = MapPlot(sector='iowa', axisbg='white', nologo=True,
            #subtitle='IDEPv2 minus IDEPv1',
            title='IDEPv2 Number of Valid Flowpaths by HUC12'  )



cursor.execute("""
 WITH data as (
  select huc_12, count(*) from flowpaths where scenario = 0 
  GROUP by huc_12
  )

 SELECT ST_Transform(geom, 4326), d.huc_12, d.count from 
 ia_huc12 h JOIN data d on (d.huc_12 = h.huc_12) ORDER by count DESC

""")

bins = np.arange(0,301,30)
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
        c = cmap( norm([float( row[2]),] ))[0]
        p = Polygon(a,fc=c,ec='None',zorder=2, lw=.1)
        patches.append(p)

          
m.ax.add_collection(PatchCollection(patches,match_original=True))
m.draw_colorbar(bins, cmap, norm, units='count')

m.drawcounties()
m.postprocess(filename='test.png')