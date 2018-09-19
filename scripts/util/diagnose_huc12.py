"""Do some diagnostics on what the raw DEP files are telling us"""
from __future__ import print_function
import sys
import glob

import pandas as pd
from pyiem import dep


def summarize_hillslopes(huc12, scenario):
    """Print out top hillslopes"""
    envs = glob.glob("/i/%s/env/%s/%s/*.env" % (scenario,
                                                huc12[:8], huc12[8:]))
    dfs = []
    for env in envs:
        df = dep.read_env(env)
        df['flowpath'] = int(env.split("/")[-1].split("_")[1][:-4])
        dfs.append(df)
    df = pd.concat(dfs)
    df2 = df[['sed_del', 'flowpath']].groupby(
        'flowpath').sum().sort_values('sed_del', ascending=False)
    print("==== TOP 5 HIGHEST SEDIMENT DELIVERY TOTALS")
    print(df2.head())
    flowpath = df2.index[0]
    df2 = df[df['flowpath'] == flowpath].sort_values('sed_del',
                                                     ascending=False)
    print("==== TOP 5 HIGHEST SEDIMENT DELIVERY FOR %s" % (flowpath, ))
    print(df2[['date', 'sed_del', 'precip', 'runoff', 'av_det']].head())
    df3 = df2.groupby('year').sum().sort_values('sed_del', ascending=False)
    print("==== TOP 5 HIGHEST SEDIMENT DELIVERY EVENTS FOR %s" % (flowpath, ))
    print(df3[['sed_del', 'precip', 'runoff', 'av_det']].head())


def main(argv):
    """Go Main"""
    huc12 = argv[1]
    scenario = argv[2]
    summarize_hillslopes(huc12, scenario)


if __name__ == '__main__':
    main(sys.argv)
