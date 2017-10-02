"""Go"""
from __future__ import print_function

from pyiem.plot import MapPlot, maue, james2, james
from shapely.wkb import loads
import psycopg2
import numpy as np
from matplotlib.patches import Polygon
import matplotlib.colors as mpcolors
import cartopy.crs as ccrs


def main():
    pgconn = psycopg2.connect(database='idep')
    cursor = pgconn.cursor()

    mp = MapPlot(continentalcolor='white', nologo=True, sector='custom',
                 south=36.8, north=45.0, west=-99.2, east=-88.9,
                 title=("HUC12 Frequency of Flowpaths with 1+ segment with "
                        "'T' management"))

    cursor.execute("""
    with data as (
        select distinct flowpath from flowpath_points
        where (lu2007 || lu2008 || lu2009 || lu2010 || lu2011 || lu2012
        || lu2013 || lu2014 || lu2015 || lu2016 || lu2017) ~* 'T'
        and scenario = 0),
    agg as (select huc_12, count(*) from flowpaths f JOIn data d
    on (f.fid = d.flowpath) GROUP by huc_12)

    SELECT ST_Transform(geom, 4326), h.huc_12,
    coalesce(a.count, 0) from huc12 h
    LEFT JOIN agg a on (h.huc_12 = a.huc_12) WHERE h.scenario = 0
    ORDER by count DESC
    """)

    bins = np.arange(1, 45, 4)
    cmap = james2()
    cmap.set_under('tan')
    cmap.set_over('black')
    norm = mpcolors.BoundaryNorm(bins, cmap.N)
    for row in cursor:
        if row[2] > 30:
            print("%s %s" % (row[1], row[2]))
        multipoly = loads(row[0].decode('hex'))
        for polygon in multipoly:
            arr = np.asarray(polygon.exterior)
            points = mp.ax.projection.transform_points(ccrs.Geodetic(),
                                                       arr[:, 0], arr[:, 1])
            color = cmap(norm([float(row[2]), ]))[0]
            poly = Polygon(points[:, :2], fc=color, ec='None', zorder=2, lw=.1)
            mp.ax.add_patch(poly)

    mp.draw_colorbar(bins, cmap, norm, units='count')

    mp.drawcounties()
    mp.postprocess(filename='test.png')


if __name__ == '__main__':
    main()
