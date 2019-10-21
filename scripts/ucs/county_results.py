from geopandas import read_postgis
from pandas.io.sql import read_sql
from pyiem.util import get_dbconn

years = 8.0
pgconn = get_dbconn('idep')
postgis = get_dbconn('postgis')

# Get the initial geometries
df = read_postgis("""
    SELECT ugc, name, geom from ugcs WHERE end_ts is null and
    substr(ugc, 1, 3) = 'IAC'
    """, postgis, index_col='ugc', crs='EPSG:4326')

titles2 = {0: 'base',
           7: '4yr',
           9: '3yr',
           10: '4yrnt',  # notill
           11: '3yrnt'}  # notill

for scenario in titles2.keys():
    df2 = read_sql("""WITH data as (
    SELECT r.huc_12,
    sum(avg_loss) * 4.463 / %s as detach,
    sum(avg_delivery) * 4.463 / %s as delivery,
    sum(avg_runoff) / 25.4 / %s as runoff
    from results_by_huc12 r
    , huc12 h WHERE r.huc_12 = h.huc_12 and h.states ~* 'IA'
    and r.scenario = %s and h.scenario = 0 and r.valid < '2016-01-01'
    and r.valid > '2008-01-01'
    GROUP by r.huc_12)

    SELECT ugc, avg(detach) as detach, avg(delivery) as delivery,
    avg(runoff) as runoff from data d JOIN huc12 h on (d.huc_12 = h.huc_12)
    WHERE h.scenario = 0 GROUP by ugc
    """, pgconn, params=(years, years, years, scenario), index_col='ugc')
    p = titles2[scenario]
    newcols = {'detach': 'det%s' % (p,),
               'delivery': 'del%s' % (p,),
               'runoff': 'run%s' % (p,)}
    for key, val in newcols.iteritems():
        df[val] = df2[key]

df.drop('geom', axis=1, inplace=True)
df.to_csv('county.csv')
df.to_file('ucs_county_results_161031.shp', driver='ESRI Shapefile')
