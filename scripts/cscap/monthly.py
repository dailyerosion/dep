"""Make plots of monthly values or differences"""
import psycopg2
from pandas.io.sql import read_sql

pgconn = psycopg2.connect(database='idep', host='iemdb', user='nobody')


def get_scenario(scenario):
    df = read_sql("""
        WITH yearly as (
            SELECT huc_12, generate_series(2007, 2016) as yr
            from huc12 where states = 'IA' and scenario = 0),
        combos as (
            SELECT huc_12, yr, generate_series(1, 12) as mo from yearly),
        results as (
            SELECT r.huc_12, extract(year from valid)::int as yr,
            extract(month from valid)::int as mo,
            sum(qc_precip) as precip, sum(avg_runoff) as runoff,
            sum(avg_delivery) as delivery,
            sum(avg_loss) as detachment from results_by_huc12 r
            WHERE r.scenario = %s
            and r.valid < '2017-01-01' GROUP by r.huc_12, yr, mo),
        agg as (
            SELECT c.huc_12, c.yr, c.mo, coalesce(r.precip, 0) as precip,
            coalesce(r.runoff, 0) as runoff,
            coalesce(r.delivery, 0) as delivery,
            coalesce(r.detachment, 0) as detachment
            from combos c LEFT JOIN results r on (c.huc_12 = r.huc_12 and
            c.yr = r.yr and c.mo = r.mo))
        select mo,
        avg(runoff) / 25.4 as runoff_in,
        avg(delivery) * 4.463 as delivery_ta,
        avg(detachment) * 4.463 as detachment_ta
        from agg GROUP by mo ORDER by mo ASC
    """, pgconn, params=(scenario, ), index_col='mo')
    return df

adf = get_scenario(20)
bdf = get_scenario(19)

print bdf - adf
