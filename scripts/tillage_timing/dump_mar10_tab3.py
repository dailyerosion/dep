"""Dump for tab1 of requested 10 march 2020 spreadsheet."""

import glob

import pandas as pd
from pyiem.util import logger

from pydep.io.wepp import read_env

LOG = logger()


def do_scenario(scenario, hucs):
    """Process this scenario."""

    df = pd.read_csv("scenario%s_dates.txt" % (scenario,))
    m50 = df["total"].max() / 2.0
    tillage_date = df[df["total"] >= m50]["date"].iloc[0]

    envdfs = []
    for huc12 in hucs:
        for fn in glob.glob(
            "/i/%s/env/%s/%s/*" % (scenario, huc12[:8], huc12[8:])
        ):
            df = read_env(fn)
            if df.empty:
                continue
            envdfs.append(df.groupby(df["date"].dt.year).sum().copy())

    envdf = pd.concat(envdfs).reset_index()
    res = envdf.groupby("date").mean()
    for year in range(2018, 2019):
        print(
            "%s,%.2f,%.2f,M,%.2f,%s"
            % (
                year,
                res.at[year, "precip"],
                res.at[year, "runoff"],
                res.at[year, "av_det"],
                tillage_date[:10],
            )
        )
    print()


def main():
    """Go Main Go."""
    hucs = [x.strip() for x in open("myhucs.txt").readlines()]
    for scenario in range(81, 91):
        do_scenario(scenario, hucs)


if __name__ == "__main__":
    main()
