"""Dump for tab1 of requested 10 march 2020 spreadsheet."""

import datetime
import glob

import pandas as pd
from pyiem.util import logger

from pydep.io.wepp import read_env

LOG = logger()


def do_scenario(scenario, plantdate, hucs):
    """Process this scenario."""
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
    LOG.info(plantdate)
    for year in range(2008, 2019):
        print(
            "%s,%.2f,%.2f,M,%.2f"
            % (
                year,
                res.at[year, "precip"],
                res.at[year, "runoff"],
                res.at[year, "av_det"],
            )
        )
    print()


def main():
    """Go Main Go."""
    apr10 = datetime.date(2000, 4, 10)
    hucs = [x.strip() for x in open("myhucs.txt").readlines()]
    for scenario in range(59, 70):
        plantdate = apr10 + datetime.timedelta(days=(scenario - 59) * 5)
        do_scenario(scenario, plantdate, hucs)


if __name__ == "__main__":
    main()
