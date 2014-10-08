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
            title='IDEPv2 Average Length Weighted Slope Change [%] by township'  )

data = {}
for line in open('tmp.txt'):
    tokens = line.split(",")
    data[ tokens[0] ] = float(tokens[1])

data1 = {}
for line in open('tmp1.txt'):
    tokens = line.split(",")
    data1[ tokens[0] ] = float(tokens[1]) * 100.


cursor.execute("""
-- WITH data as (
--  select model_twp, sum(slope * length) / sum(length) as val from 
-- flowpath_points f, iatwp i where ST_Contains(i.the_geom, f.geom) 
-- GROUP by model_twp
-- )

-- SELECT ST_Transform(the_geom, 4326), data.val * 100.0, data.model_twp from iatwp i JOIN data on (data.model_twp = i.model_twp)

SELECT ST_Transform(the_geom, 4326), model_twp from iatwp i

""")

bins = np.arange(0,18,2)
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
        #c = cmap( norm([float(row[1]),]) )[0]
        diff = data.get(row[1], 0) - data1.get(row[1], 0)
        print '%10s 1:%5.2f 2:%5.2f' % (row[1],data1.get(row[1], 0), data.get(row[1], 0))
        diff = data.get(row[1], 0)
        c = cmap( norm([float( diff),] ))[0]
        p = Polygon(a,fc=c,ec='None',zorder=2, lw=.1)
        patches.append(p)

          
m.ax.add_collection(PatchCollection(patches,match_original=True))
m.draw_colorbar(bins, cmap, norm, units='%')

m.drawcounties()
m.postprocess(filename='test.png')