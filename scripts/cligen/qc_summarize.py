"""Need something that prints diagnostics of our climate file"""
from __future__ import print_function
import sys
import datetime

import pandas as pd
import requests
from pyiem.datatypes import distance
from pyiem.dep import read_cli


def do_qc(fn, df):
    """Run some checks on this dataframe"""
    # Does the frame appear to have all dates?
    if len(df.index) != len(df.resample('D').mean().index):
        print("ERROR: Appears to be missing dates!")

    if open(fn).read()[-1] != '\n':
        print("ERROR: File does not end with \\n")

    print("YEAR   RAIN MAXRATE  MAXACC  #DAYS  #>1RT  RAD/D")
    for year, gdf in df.groupby(by=df.index.year):
        print(("%s %6.2f %7.2f %7.2f %6i %6i %6.0f"
               ) % (year, distance(gdf['pcpn'].sum(), 'MM').value('IN'),
                    distance(gdf['maxr'].max(), 'MM').value('IN'),
                    distance(gdf['pcpn'].max(), 'MM').value('IN'),
                    len(gdf[gdf['pcpn'] > 0].index),
                    len(gdf[gdf['maxr'] > 25.4].index),
                    gdf['rad'].mean()
                    ))

    year = 2009
    for month in range(1, 13):
        nextmonth = (datetime.date(year, month, 1) + datetime.timedelta(
            days=35)).replace(day=1)
        df2 = df.loc[slice(datetime.date(year, month, 1), nextmonth)]
        print(("%02i %.2f"
               ) % (month,
                    distance(df2['pcpn'].sum(), 'MM').value('IN')))

    # Get prism, for a bulk comparison
    prism = requests.get(("http://mesonet.agron.iastate.edu/json/prism/"
                          "-94.39/43.27/%s0101-%s1231"
                          ) % (year, year)).json()
    rows = []
    for entry in prism['data']:
        rows.append({'date': datetime.datetime.strptime(entry['valid'][:10],
                                                        '%Y-%m-%d'),
                     'precip': entry['precip_in']
                     })
    prismdf = pd.DataFrame(rows)
    prismdf.set_index('date', inplace=True)
    print("PRISM sum precip is: %.2f" % (prismdf['precip'].sum(), ))
    print(prismdf['precip'].resample('M').sum())

    # Compare daily values
    iemjson = requests.get(("https://mesonet.agron.iastate.edu/iemre/multiday/"
                            "%s-01-01/%s-12-31/43.27/-94.39/json"
                            ) % (year, year)).json()
    rows = []
    for entry in iemjson['data']:
        rows.append({'date': datetime.datetime.strptime(entry['date'],
                                                        '%Y-%m-%d'),
                     'precip': entry['daily_precip_in']
                     })
    iemdf = pd.DataFrame(rows)
    iemdf.set_index('date', inplace=True)
    print("IEMRE sum precip is: %.2f" % (iemdf['precip'].sum(), ))
    df['iemre_precip'] = iemdf['precip']
    df['diff_precip'] = df['pcpn_in'] - df['iemre_precip']
    print(df[['diff_precip', 'pcpn_in', 'iemre_precip']
             ].sort_values(by='diff_precip', ascending=False).head())
    print(df[['diff_precip', 'pcpn_in', 'iemre_precip']
             ].sort_values(by='diff_precip', ascending=True).head())
    print(df.loc[slice(datetime.date(year, 1, 1),
                       datetime.date(year, 1, 31))][[
                              'diff_precip', 'pcpn_in', 'iemre_precip']])


def main(argv):
    """Do Stuff"""
    fn = argv[1]
    df = read_cli(fn)
    df['pcpn_in'] = distance(df['pcpn'].values, 'MM').value('IN')
    do_qc(fn, df)


if __name__ == '__main__':
    main(sys.argv)
