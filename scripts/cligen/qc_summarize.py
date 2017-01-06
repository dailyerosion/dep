"""Need something that prints diagnostics of our climate file"""
import sys
import pandas as pd
import datetime
from pyiem.datatypes import distance
from pyiem.dep import read_cli


def qc(fn, df):
    """Run some checks on this dataframe"""
    # Does the frame appear to have all dates?
    if len(df.index) != len(df.resample('D').mean().index):
        print("ERROR: Appears to be missing dates!")

    if open(fn).read()[-1] != '\n':
        print("ERROR: File does not end with \\n")

    print("YEAR   RAIN MAXRATE  MAXACC  #DAYS  #>1RT")
    for year, gdf in df.groupby(by=df.index.year):
        print(("%s %6.2f %7.2f %7.2f %6i %6i"
               ) % (year, distance(gdf['pcpn'].sum(), 'MM').value('IN'),
                    distance(gdf['maxr'].max(), 'MM').value('IN'),
                    distance(gdf['pcpn'].max(), 'MM').value('IN'),
                    len(gdf[gdf['pcpn'] > 0].index),
                    len(gdf[gdf['maxr'] > 25.4].index)
                    ))


def main(argv):
    """Do Stuff"""
    fn = argv[1]
    df = read_cli(fn)
    qc(fn, df)


if __name__ == '__main__':
    main(sys.argv)
