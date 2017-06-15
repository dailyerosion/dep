"""General HUC12 mapper"""
from __future__ import print_function

import datetime
import sys

from pyiem.plot import MapPlot, nwsprecip
from shapely.wkb import loads
import psycopg2
import numpy as np
import cartopy.crs as ccrs
from matplotlib.patches import Polygon
import matplotlib.colors as mpcolors


def main(argv):
    """Do Great Things"""
    year = int(argv[1])
    pgconn = psycopg2.connect(database='idep', host='localhost',
                              port=5555, user='nobody')
    cursor = pgconn.cursor()

    mp = MapPlot(continentalcolor='white', nologo=True,
                 sector='custom',
                 south=36.8, north=45.0, west=-99.2, east=-88.9,
                 subtitle='Assumes 56 lb test weight',
                 title=('%s Corn Yield HUC12 Average'
                        ) % (year, ))

    cursor.execute("""
    with hucs as (
        select huc_12, ST_Transform(simple_geom, 4326) as geo
        from huc12),
    data as (
        SELECT huc12, avg(yield_kgm2) * 8921.8 / 56. as val from harvest
        where crop = 'Corn' and valid between %s and %s
        GROUP by huc12
    )

    SELECT geo, huc12, val from hucs h JOIN data d on (h.huc_12 = d.huc12)
    """, (datetime.date(year, 1, 1), datetime.date(year, 12, 31)))

    bins = np.arange(0, 310, 30)
    cmap = nwsprecip()
    cmap.set_under('white')
    cmap.set_over('black')
    norm = mpcolors.BoundaryNorm(bins, cmap.N)

    for row in cursor:
        polygon = loads(row[0].decode('hex'))
        arr = np.asarray(polygon.exterior)
        points = mp.ax.projection.transform_points(ccrs.Geodetic(),
                                                   arr[:, 0], arr[:, 1])
        color = cmap(norm([float(row[2]), ]))[0]
        poly = Polygon(points[:, :2], fc=color, ec='None', zorder=2, lw=.1)
        mp.ax.add_patch(poly)

    mp.draw_colorbar(bins, cmap, norm, units='bu/acre')

    # mp.drawcounties()
    mp.postprocess(filename='test.png')


if __name__ == '__main__':
    main(sys.argv)
