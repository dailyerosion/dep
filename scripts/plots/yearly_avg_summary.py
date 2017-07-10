"""Period of record plot summaries"""
from __future__ import print_function
import datetime
import sys

import psycopg2
import numpy as np
from geopandas import read_postgis
import matplotlib
matplotlib.use('agg')
from pyiem.plot import MapPlot
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import matplotlib.colors as mpcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature

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


def main(argv):
    """Go Main Go"""
    v = argv[1]
    agg = argv[2]
    ts = datetime.date(2008, 1, 1)
    ts2 = datetime.date(2016, 12, 31)
    scenario = 0

    # suggested for runoff and precip
    if v in ['qc_precip', 'avg_runoff']:
        colors = ['#ffffa6', '#9cf26d', '#76cc94', '#6399ba', '#5558a1']
    # suggested for detachment
    elif v in ['avg_loss']:
        colors = ['#cbe3bb', '#c4ff4d', '#ffff4d', '#ffc44d', '#ff4d4d',
                  '#c34dee']
    # suggested for delivery
    elif v in ['avg_delivery']:
        colors = ['#ffffd2', '#ffff4d', '#ffe0a5', '#eeb74d', '#ba7c57',
                  '#96504d']
    cmap = mpcolors.ListedColormap(colors, 'james')
    cmap.set_under('white')
    cmap.set_over('black')

    pgconn = psycopg2.connect(database='idep', host='localhost', port=5555,
                              user='nobody')

    title = "for %s" % (ts.strftime("%-d %B %Y"),)
    if ts != ts2:
        title = "between %s and %s" % (ts.strftime("%-d %b %Y"),
                                       ts2.strftime("%-d %b %Y"))
    mp = MapPlot(axisbg='#EEEEEE', nologo=True, sector='iowa',
                 nocaption=True,
                 title=("DEP %s %s %s"
                        ) % (V2NAME[v],
                             "Yearly Average" if agg == 'avg' else 'Total',
                             title),
                 caption='Daily Erosion Project')

    df = read_postgis("""
    WITH data as (
      SELECT huc_12, extract(year from valid) as yr,
      sum("""+v+""")  as d from results_by_huc12
      WHERE scenario = %s and valid >= %s and valid <= %s
      GROUP by huc_12, yr),

    agg as (
      SELECT huc_12, """ + agg + """(d) as d from data GROUP by huc_12)

    SELECT ST_Transform(simple_geom, 4326) as geo, coalesce(d.d, 0) as data
    from huc12 i LEFT JOIN agg d
    ON (i.huc_12 = d.huc_12) WHERE i.scenario = %s and i.states ~* 'IA'
    """, pgconn, params=(scenario, ts, ts2, scenario), geom_col='geo',
                      index_col=None)
    df['data'] = df['data'] * V2MULTI[v]
    if df['data'].max() < 0.01:
        bins = [0.01, 0.02, 0.03, 0.04, 0.05]
    else:
        bins = np.array(V2RAMP[v]) * (10. if agg == 'sum' else 1.)
    norm = mpcolors.BoundaryNorm(bins, cmap.N)

    # m.ax.add_geometries(df['geo'], ccrs.PlateCarree())
    for _, row in df.iterrows():
        c = cmap(norm([row['data'], ]))[0]
        arr = np.asarray(row['geo'].exterior)
        points = mp.ax.projection.transform_points(ccrs.Geodetic(),
                                                   arr[:, 0], arr[:, 1])
        p = Polygon(points[:, :2], fc=c, ec='k', zorder=2, lw=0.1)
        mp.ax.add_patch(p)

    mp.drawcounties()
    mp.drawcities()
    lbl = [round(_, 2) for _ in bins]
    u = "%s, Avg: %.2f" % (V2UNITS[v], df['data'].mean())
    mp.draw_colorbar(bins, cmap, norm,
                     clevlabels=lbl, units=u,
                     title="%s :: %s" % (V2NAME[v], V2UNITS[v]))
    plt.savefig('%s_%s_%s%s.eps' % (ts.year, ts2.year, v,
                                    "_sum" if agg == 'sum' else ''))


if __name__ == '__main__':
    main(sys.argv)
