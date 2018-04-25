"""Go"""
from __future__ import print_function

from shapely.wkb import loads
import numpy as np
from matplotlib.patches import Polygon
import matplotlib.colors as mpcolors
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from pyiem.util import get_dbconn
from pyiem.datatypes import distance
from pyiem.plot import MapPlot, maue, james2, james


def main():
    pgconn = get_dbconn('idep')
    cursor = pgconn.cursor()

    mp = MapPlot(continentalcolor='white', nologo=True, # sector='custom',
                 # south=36.8, north=45.0, west=-99.2, east=-88.9,
                 caption='Daily Erosion Project',
                 subtitle='HUC12 Areal Averaged, Based on NOAA Stage IV RADAR Bias Corrected Data',
                 title=("Estimated Rainfall between 12 April 2008 and 12 June "
                        "2008 (inclusive)"))

    cursor.execute("""
    with agg as (
        select huc_12, sum(qc_precip) as precip from results_by_huc12
        WHERE valid >= '2008-04-12' and valid <= '2008-06-12' and scenario = 0
        GROUP by huc_12)

    SELECT ST_Transform(geom, 4326), h.huc_12,
    coalesce(a.precip, 0) as precip from huc12 h
    LEFT JOIN agg a on (h.huc_12 = a.huc_12) WHERE h.scenario = 0
    and h.states ~* 'IA'
    ORDER by precip DESC
    """)

    bins = np.arange(0, 26, 2)
    bins[0] = 0.01
    cmap = plt.get_cmap("plasma_r")
    cmap.set_under('white')
    cmap.set_over('black')
    norm = mpcolors.BoundaryNorm(bins, cmap.N)
    for row in cursor:
        val = distance(row[2], 'MM').value('IN')
        if val > 30:
            print("%s %s" % (row[1], val))
        multipoly = loads(row[0].decode('hex'))
        for polygon in multipoly:
            arr = np.asarray(polygon.exterior)
            points = mp.ax.projection.transform_points(ccrs.Geodetic(),
                                                       arr[:, 0], arr[:, 1])
            color = cmap(norm([val, ]))[0]
            poly = Polygon(points[:, :2], fc=color, ec='None', zorder=2, lw=.1)
            mp.ax.add_patch(poly)

    mp.draw_colorbar(bins, cmap, norm, units='inches')

    mp.drawcounties()
    plt.savefig('test.pdf')


if __name__ == '__main__':
    main()
