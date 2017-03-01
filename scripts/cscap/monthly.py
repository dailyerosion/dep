"""Make plots of monthly values or differences"""
import psycopg2
from pandas.io.sql import read_sql

pgconn = psycopg2.connect(database='idep', host='iemdb', user='nobody')

df = read_sql("""
    WITH combos as (
        SELECT huc_12, generate_series(2007, 2016) as yr
        from huc12 where states = 'IA' and scenario = 0),
    results as (
        SELECT r.huc_12, extract(year from valid)::int as yr,
        sum(qc_precip) as precip, sum(avg_runoff) as runoff,
        sum(avg_delivery) as delivery,
        sum(avg_loss) as detachment from results_by_huc12 r
        WHERE r.scenario = 20
        and r.valid < '2017-01-01' GROUP by r.huc_12, yr),
    agg as (
        SELECT c.huc_12, c.yr, r.precip, r.runoff, r.delivery, r.detachment
        from combos c LEFT JOIN results r on (c.huc_12 = r.huc_12 and
        c.yr = r.yr))
    SELECT avg(precip) / 25.4, avg(runoff) / 25.4,
    avg(delivery) * 4.463, avg(detachment) * 4.463 from agg