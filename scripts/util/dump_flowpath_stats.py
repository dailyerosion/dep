from pandas.io.sql import read_sql
import psycopg2

pgconn = psycopg2.connect('dbname=idep')

df = read_sql("""WITH data as (
    SELECT huc_12, ST_length(geom) as length from
    flowpaths where scenario = 0)

    SELECT huc_12,
    count(*) as count_all,
    sum(case when length < 22.1 then 1 else 0 end) as count_lt221,
    sum(case when length > 22.1 then 1 else 0 end) as count_gt221,
 min(case when length > 22.1 then length else null end) as min_length_gt221_m,
 avg(case when length > 22.1 then length else null end) as avg_length_gt221_m,
    min(length) as min_length_all_m,
    avg(length) as avg_length_all_m,
    max(length) as max_length_all_m
    from data GROUP by huc_12
    """, pgconn, index_col='huc_12')

df.to_csv("huc12_flowpath_stats_v2.csv")
