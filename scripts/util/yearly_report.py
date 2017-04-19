"""Generate a report for the yearly DEP totals"""
import sys

import psycopg2
from pandas.io.sql import read_sql


def main(argv):
    """Do What We Wanted"""
    scenario = int(argv[1])
    pgconn = psycopg2.connect(database='idep', host='localhost', port=5555)

    df = read_sql("""
        WITH iahuc12 as (
            SELECT huc_12 from huc12 where states = 'IA' and scenario = 0
        ), agg as (
            SELECT r.huc_12, extract(year from valid)::int as yr,
            sum(qc_precip) as precip, sum(avg_runoff) as runoff,
            sum(avg_delivery) as delivery,
            sum(avg_loss) as detachment from results_by_huc12 r JOIN iahuc12 i
            on (r.huc_12 = i.huc_12) WHERE r.scenario = %s
            and r.valid < '2017-01-01' GROUP by r.huc_12, yr
        )

        SELECT yr, round((avg(precip) / 25.4)::numeric, 2) as precip_in,
        round((avg(runoff) / 25.4)::numeric, 2) as runoff_in,
        round((avg(delivery) * 4.463)::numeric, 2) as delivery_ta,
        round((avg(detachment) * 4.463)::numeric, 2) as detachment_ta
        from agg GROUP by yr ORDER by yr
    """, pgconn, params=(scenario, ), index_col='yr')

    print df
    print df.mean()


if __name__ == '__main__':
    main(sys.argv)
