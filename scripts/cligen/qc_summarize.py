"""Need something that prints diagnostics of our climate file"""
from __future__ import print_function
import sys
import datetime

import numpy as np
import netCDF4
import pytz
import pandas as pd
import requests
from pyiem.datatypes import distance, temperature
from pyiem.dep import read_cli
from pyiem.iemre import hourly_offset


def compute_stage4(lon, lat, year):
    """Build a daily dataframe for the stage4 data"""
    nc = netCDF4.Dataset("/mesonet/data/stage4/%s_stage4_hourly.nc" % (year,))
    lons = nc.variables['lon'][:]
    lats = nc.variables['lat'][:]
    dist = ((lons - lon)**2 + (lats - lat)**2)**0.5
    (yidx, xidx) = np.unravel_index(dist.argmin(), dist.shape)
    p01i = distance(nc.variables['p01m'][:, yidx, xidx], 'MM').value('IN')
    nc.close()
    df = pd.DataFrame({'precip': 0.0},
                      index=pd.date_range('%s-01-01' % (year, ),
                                          '%s-12-31' % (year, ),
                                          tz='America/Chicago'))
    for date in df.index.values:
        date2 = datetime.datetime.utcfromtimestamp(date.tolist()/1e9)
        ts = datetime.datetime(date2.year, date2.month, date2.day, 6)
        ts = ts.replace(tzinfo=pytz.utc)
        ts = ts.astimezone(pytz.timezone("America/Chicago"))
        ts = ts.replace(hour=0)
        ts = ts.astimezone(pytz.utc)
        tidx = hourly_offset(ts)
        # values are in the rears
        val = np.ma.sum(p01i[tidx+1:tidx+25])
        if val > 0:
            df.at[date, 'precip'] = val  # close enough
    return df


def fn2lonlat(filename):
    """Convert the filename to lon and lat"""
    tokens = filename.split("/")[-1].rsplit(".", 1)[0].split("x")
    return [0 - float(tokens[0]), float(tokens[1])]


def do_qc(fn, df, year):
    """Run some checks on this dataframe"""
    (lon, lat) = fn2lonlat(fn)
    stage4 = compute_stage4(lon, lat, year)
    # Does the frame appear to have all dates?
    if len(df.index) != len(df.resample('D').mean().index):
        print("ERROR: Appears to be missing dates!")

    if open(fn).read()[-1] != '\n':
        print("ERROR: File does not end with \\n")

    print("--------- Summary stats from the .cli file")
    print("YEAR |  RAIN | MAXRATE | MAXACC | #DAYS | #>1RT | RAD/D")
    print(" --- | --- | --- | --- | --- | --- | ---")
    for _year, gdf in df.groupby(by=df.index.year):
        print(("%s | %6.2f | %7.2f | %7.2f | %6i | %6i | %6.0f"
               ) % (_year, distance(gdf['pcpn'].sum(), 'MM').value('IN'),
                    distance(gdf['maxr'].max(), 'MM').value('IN'),
                    distance(gdf['pcpn'].max(), 'MM').value('IN'),
                    len(gdf[gdf['pcpn'] > 0].index),
                    len(gdf[gdf['maxr'] > 25.4].index),
                    gdf['rad'].mean()))

    print("----- Average high temperature -----")
    print("YEAR | Avg High F | Avg Low F | Days > 100F")
    print(" --- | --- | --- | ---")
    for _year, gdf in df.groupby(by=df.index.year):
        print(("%s | %6.2f | %6.2f | %3i"
               ) % (_year, temperature(gdf['tmax'].mean(), 'C').value('F'),
                    temperature(gdf['tmin'].mean(), 'C').value('F'),
                    len(gdf[gdf['tmax'] > 37.7].index)
                    ))

    monthly = df[df.index.year == year]['pcpn'].resample('M').sum().copy()
    monthly = pd.DataFrame({
        'dep': distance(monthly.values, 'MM').value('IN')},
                        index=range(1, 13))

    # Get prism, for a bulk comparison
    prism = requests.get(("http://mesonet.agron.iastate.edu/json/prism/"
                          "%.2f/%.2f/%s0101-%s1231"
                          ) % (lon, lat, year, year)).json()
    rows = []
    for entry in prism['data']:
        rows.append({'date': datetime.datetime.strptime(entry['valid'][:10],
                                                        '%Y-%m-%d'),
                     'precip': entry['precip_in']
                     })
    prismdf = pd.DataFrame(rows)
    prismdf.set_index('date', inplace=True)
    monthly['prism'] = prismdf['precip'].resample(
        'M').sum().copy().values

    # Compare daily values
    iemjson = requests.get(("http://mesonet.agron.iastate.edu/iemre/multiday/"
                            "%s-01-01/%s-12-31/%s/%s/json"
                            ) % (year, year, lat, lon)).json()
    rows = []
    for entry in iemjson['data']:
        rows.append({'date': datetime.datetime.strptime(entry['date'],
                                                        '%Y-%m-%d'),
                     'precip': entry['daily_precip_in']
                     })
    iemdf = pd.DataFrame(rows)
    iemdf.set_index('date', inplace=True)
    print("PRISM %s precip is: %.2f" % (year, prismdf['precip'].sum(), ))
    print("IEMRE sum precip is: %.2f" % (iemdf['precip'].sum(), ))
    print("StageIV sum precip is: %.2f" % (stage4['precip'].sum(), ))
    monthly['stage4'] = stage4['precip'].resample('M').sum().copy().values
    monthly['iemre'] = iemdf['precip'].resample('M').sum().copy().values
    monthly['prism-dep'] = monthly['prism'] - monthly['dep']
    monthly['iemre-dep'] = monthly['iemre'] - monthly['dep']

    print(" --------- %s Monthly Totals --------" % (year, ))
    print(monthly)
    df.at[slice(datetime.date(year, 1, 1),
                datetime.date(year, 12, 31)),
          'stage4_precip'] = stage4['precip'].values
    df['iemre_precip'] = iemdf['precip']
    df['diff_precip'] = df['pcpn_in'] - df['iemre_precip']
    df['diff_stage4'] = df['pcpn_in'] - df['stage4_precip']
    print(" --- Top 5 Largest DEP > IEMRE ----")
    print(df[['diff_precip', 'pcpn_in', 'iemre_precip', 'stage4_precip',
              'diff_stage4']
             ].sort_values(by='diff_precip', ascending=False).head())
    print(" --- Top 5 Largest IEMRE > DEP ----")
    print(df[['diff_precip', 'pcpn_in', 'iemre_precip', 'stage4_precip',
              'diff_stage4']
             ].sort_values(by='diff_precip', ascending=True).head())

    print(" --- Top 10 Largest Stage4 > DEP ----")
    print(df[['diff_precip', 'pcpn_in', 'iemre_precip', 'stage4_precip',
              'diff_stage4']
             ].sort_values(by='diff_stage4', ascending=True).head(10))
    print(" vvv job listing based on the above vvv")
    for dt in df.sort_values(by='diff_stage4', ascending=True).head(10).index:
        print("python daily_clifile_editor.py 0 %s %s %s" % (dt.year, dt.month,
                                                             dt.day))
    df2 = df.loc[slice(datetime.date(year, 1, 1),
                       datetime.date(year, 1, 31))][[
                              'diff_precip', 'pcpn_in', 'iemre_precip',
                              'stage4_precip']
                                                    ].sort_values(
                                                        by='diff_precip')
    print(" --- Daily values for month """)
    print(df2)


def main(argv):
    """Do Stuff"""
    fn = argv[1]
    year = int(argv[2])
    df = read_cli(fn)
    df['pcpn_in'] = distance(df['pcpn'].values, 'MM').value('IN')
    do_qc(fn, df, year)


if __name__ == '__main__':
    main(sys.argv)
