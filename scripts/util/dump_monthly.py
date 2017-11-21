"""Dump some monthly data"""
from __future__ import print_function

from pandas.io.sql import read_sql
from pyiem.util import get_dbconn

# English River
HUCS = ['070802090302',
        '070802090401',
        '070802090403',
        '070802090301',
        '070802090406',
        '070802090405',
        '070802090404',
        '070802090407',
        '070802090407',
        '070802090502',
        '070802090501',
        '070802090402',
        '070802090503',
        '070802090504',
        '070802090408']


def main():
    """Go Main Go"""
    pgconn = get_dbconn('idep', user='nobody')
    df = read_sql("""
    SELECT huc_12, date_trunc('month', valid)::date as date,
    sum(qc_precip) as precip_mm,
    sum(avg_loss) as detach_kgm2,
    sum(avg_delivery) as delivery_kgm2,
    sum(avg_runoff) as runoff_mm from results_by_huc12
    WHERE scenario = 0 and huc_12 in %s
    and valid >= '2008-01-01' and valid < '2017-01-01'
    GROUP by huc_12, date ORDER by huc_12, date
    """, pgconn, params=(tuple(HUCS), ))
    df.to_csv('dep_english.csv', index=False)


if __name__ == '__main__':
    main()
