"""Summarize for MLRA, somehow"""
from __future__ import print_function
import sys

from pandas.io.sql import read_sql
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from pyiem.util import get_dbconn

LABELS = {
    36: 'Slopes > 3% to Switchgrass',
    37: 'Slopes > 6% to Switchgrass',
    38: 'Slopes > 10% to Switchgrass',
    }


def main(argv):
    """Go Main Go"""
    mlra_id = int(argv[1])
    pgconn = get_dbconn('idep')

    mlraxref = read_sql("""
    select distinct mlra_id, mlra_name from mlra
    """, pgconn, index_col='mlra_id')

    df = read_sql("""
    with myhucs as (
        SELECT huc_12 from huc12 where scenario = 0 and mlra_id = %s
    )
    select r.huc_12, scenario, extract(year from valid)::int as year,
    sum(avg_loss) * 4.463 as loss, sum(avg_runoff) as runoff,
    sum(avg_delivery) * 4.463 as delivery
    from results_by_huc12 r JOIN myhucs h on (r.huc_12 = h.huc_12)
    where r.valid >= '2008-01-01' and r.valid < '2017-01-01'
    and scenario in (0, 36, 37, 38)
    GROUP by r.huc_12, year, scenario
    """, pgconn, params=(mlra_id, ), index_col=None)
    gdf = df.groupby('scenario').mean()
    print("%s\t%.2f" % (mlraxref.at[mlra_id, 'mlra_name'],
                        gdf.at[0, 'runoff']), end='\t')
    for scenario in range(36, 39):
        delta = gdf.loc[(scenario, )] / gdf.loc[(0, )] * 100.
        print("%.2f (%.1f%%)" % (gdf.at[scenario, 'runoff'], delta['runoff']), end='\t')
    print()



if __name__ == '__main__':
    for mlraid in [106, 107, 108, 109, 121, 137, 150, 155, 166, 175,
                   176, 177, 178, 179, 181, 182, 186, 187, 188, 196,
                   197, 204, 205]:
        main([None, mlraid])
