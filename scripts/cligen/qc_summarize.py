"""Need something that prints diagnostics of our climate file"""
from __future__ import print_function
import sys
import datetime

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

    for month in range(1, 13):
        nextmonth = (datetime.date(2009, month, 1) + datetime.timedelta(
            days=35)).replace(day=1)
        df2 = df.loc[slice(datetime.date(2009, month, 1), nextmonth)]
        print(("%02i %.2f"
               ) % (month,
                    distance(df2['pcpn'].sum(), 'MM').value('IN')))


def main(argv):
    """Do Stuff"""
    fn = argv[1]
    df = read_cli(fn)
    do_qc(fn, df)


if __name__ == '__main__':
    main(sys.argv)
