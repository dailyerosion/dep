"""Summarize for MLRA, somehow"""
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

    fig, ax = plt.subplots(3, 3, figsize=(12, 6))

    mlraxref = read_sql("""
    select mlra_id, mlra_name from mlra
    """, pgconn, index_col='mlra_id')
    fig.text(0.5, 0.96,
             ("CSCAP Yearly Scenario Changes for MLRA: %s [%s]"
              ) % (mlraxref.at[mlra_id, 'mlra_name'], mlra_id),
             ha='center', fontsize=16)

    for col, scenario in enumerate(range(36, 39)):
        df = read_sql("""
        with myhucs as (
            SELECT huc_12 from huc12 where scenario = 0 and mlra_id = %s
        )
        select r.huc_12, scenario, extract(year from valid)::int as year,
        sum(avg_loss) * 4.463 as loss, sum(avg_runoff) as runoff,
        sum(avg_delivery) * 4.463 as delivery
        from results_by_huc12 r JOIN myhucs h on (r.huc_12 = h.huc_12)
        where r.valid >= '2008-01-01' and r.valid < '2017-01-01'
        and (scenario = 0 or scenario = %s)
        GROUP by r.huc_12, year, scenario
        """, pgconn, params=(mlra_id, scenario), index_col=None)
        gdf = df.groupby(('scenario', 'year')).mean()
        delta = gdf.loc[(scenario, )] - gdf.loc[(0, )]
        for row, varname in enumerate(['runoff', 'loss', 'delivery']):
            ax[row, col].bar(delta.index.values, delta[varname],
                             color=['b'
                                    if x > 0 else 'r'
                                    for x in delta[varname].values])
            if row == 0:
                ax[row, col].set_title("Scenario %s\n%s" % (scenario,
                                                            LABELS[scenario]))
    ylabels = ['Runoff [mm]', 'Loss [T/a]', 'Delivery [T/a]']
    for row in range(3):
        ymin = 99
        ymax = -99
        for col in range(3):
            ylim = ax[row, col].get_ylim()
            ymin = min([ylim[0], ymin])
            ymax = max([ylim[1], ymax])
        for col in range(3):
            ax[row, col].set_ylim(ymin, ymax)
            ax[row, col].grid(True)
            if col > 0:
                ax[row, col].set_yticklabels([])
            else:
                ax[row, col].set_ylabel(ylabels[row])

    fig.savefig('mlra%s.png' % (mlra_id, ))
    plt.close()


if __name__ == '__main__':
    for mlraid in [106, 107, 108, 109, 121, 137, 150, 155, 166, 175,
                   176, 177, 178, 179, 181, 182, 186, 187, 188, 196,
                   197, 204, 205]:
        main([None, mlraid])
