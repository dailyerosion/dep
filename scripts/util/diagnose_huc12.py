"""Do some diagnostics on what the raw DEP files are telling us"""
import datetime
import glob
import sys

import pandas as pd
from pandas.io.sql import read_sql
from pydep.io.wepp import read_env
from pyiem.util import get_dbconn

YEARS = datetime.date.today().year - 2007 + 1
CONV = 4.463


def get_lengths(huc12, scenario):
    """Figure out our slope lengths."""
    pgconn = get_dbconn("idep")
    return read_sql(
        "SELECT fpath, ST_Length(geom) as length from flowpaths "
        "where scenario = %s and huc_12 = %s",
        pgconn,
        params=(scenario, huc12),
        index_col="fpath",
    )


def summarize_hillslopes(huc12, scenario):
    """Print out top hillslopes"""
    lengths = get_lengths(huc12, scenario)
    envs = glob.glob(
        "/i/%s/env/%s/%s/*.env" % (scenario, huc12[:8], huc12[8:])
    )
    dfs = []
    for env in envs:
        df = read_env(env)
        df["flowpath"] = int(env.split("/")[-1].split("_")[1][:-4])
        dfs.append(df)
    df = pd.concat(dfs)
    df = df.join(lengths, on="flowpath")
    df["delivery_ta"] = df["sed_del"] / df["length"] * CONV / YEARS
    flowpath = 424  # df2.index[0]
    print(
        df[df["flowpath"] == flowpath]
        .groupby("year")
        .sum()
        .sort_index(ascending=True)
    )
    df2 = (
        df[["delivery_ta", "flowpath"]]
        .groupby("flowpath")
        .sum()
        .sort_values("delivery_ta", ascending=False)
    )
    print("==== TOP 5 HIGHEST SEDIMENT DELIVERY TOTALS")
    print(df2.head())
    print("==== TOP 5 LOWEST SEDIMENT DELIVERY TOTALS")
    print(df2.tail())
    print(df2.loc[flowpath])
    df2 = df[df["flowpath"] == flowpath].sort_values(
        "sed_del", ascending=False
    )
    print("==== TOP 5 HIGHEST SEDIMENT DELIVERY FOR %s" % (flowpath,))
    print(df2[["date", "sed_del", "precip", "runoff", "av_det"]].head())
    df3 = df2.groupby("year").sum().sort_values("sed_del", ascending=False)
    print("==== TOP 5 HIGHEST SEDIMENT DELIVERY EVENTS FOR %s" % (flowpath,))
    print(df3[["sed_del", "precip", "runoff", "av_det"]].head())


def main(argv):
    """Go Main"""
    huc12 = argv[1]
    scenario = argv[2]
    summarize_hillslopes(huc12, scenario)


if __name__ == "__main__":
    main(sys.argv)
