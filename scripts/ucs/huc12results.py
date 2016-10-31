import psycopg2
from geopandas import read_postgis
from pandas.io.sql import read_sql

years = 8.0
pgconn = psycopg2.connect(database='idep', host='iemdb', user='nobody')

# Get the initial geometries
df = read_postgis("""
    SELECT huc_12, geom from huc12 WHERE states ~* 'IA' and scenario = 0
    """, pgconn, index_col='huc_12', crs='EPSG:5070')

titles2 = {0: 'base',
           7: '4yr',
           9: '3yr',
           10: '4yrnt',  # notill
           11: '3yrnt'}  # notill

for scenario in titles2.keys():
    df2 = read_sql("""
    SELECT r.huc_12,
    sum(avg_loss) * 4.463 / %s as detach,
    sum(avg_delivery) * 4.463 / %s as delivery,
    sum(avg_runoff) / 25.4 / %s as runoff
    from results_by_huc12 r
    , huc12 h WHERE r.huc_12 = h.huc_12 and h.states ~* 'IA'
    and r.scenario = %s and h.scenario = 0 and r.valid < '2016-01-01'
    and r.valid > '2008-01-01'
    GROUP by r.huc_12
    """, pgconn, params=(years, years, years, scenario), index_col='huc_12')
    p = titles2[scenario]
    newcols = {'detach': 'det%s' % (p,),
               'delivery': 'del%s' % (p,),
               'runoff': 'run%s' % (p,)}
    for key, val in newcols.iteritems():
        df[val] = df2[key]

df.to_file('ucs_results_161031.shp', driver='ESRI Shapefile')
