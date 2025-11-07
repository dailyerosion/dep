"""Dump for tab2 of requested 10 march 2020 spreadsheet."""

import datetime
import glob

import pandas as pd
from pyiem.util import logger

from pydep.io.dep import read_wb
from pydep.io.wepp import read_env

LOG = logger()


def do_scenario(scenario, plantdate, hucs):
    """Process this scenario."""
    smdfs = []
    for huc12 in hucs:
        for fn in glob.glob(
            "/i/%s/wb/%s/%s/*" % (scenario, huc12[:8], huc12[8:])
        ):
            smdfs.append(read_wb(fn))
    smdf = pd.concat(smdfs).reset_index()
    smdf = smdf[smdf["ofe"] == 1]
    smdf = smdf[
        (smdf["date"] >= pd.to_datetime("2008/1/1"))
        & (smdf["date"] < pd.to_datetime("2019/1/1"))
    ]

    smdf["jday"] = pd.to_numeric(
        smdf["date"].dt.strftime("%j"), downcast="integer"
    )
    smres = smdf.groupby("jday").mean()

    envdfs = []
    for huc12 in hucs:
        for fn in glob.glob(
            "/i/%s/env/%s/%s/*" % (scenario, huc12[:8], huc12[8:])
        ):
            df = read_env(fn)
            if df.empty:
                continue
            envdfs.append(df)
    envdf = pd.concat(envdfs).reset_index()

    envdf = envdf[
        (envdf["date"] >= pd.to_datetime("2008/1/1"))
        & (envdf["date"] < pd.to_datetime("2019/1/1"))
    ]
    envdf["jday"] = pd.to_numeric(
        envdf["date"].dt.strftime("%j"), downcast="integer"
    )
    # Manually compute to account for zeros
    res = (envdf.groupby("jday").sum() / 11.0 / float(len(envdfs))).copy()
    smres["precip"] = res["precip"]
    smres["av_det"] = res["av_det"]
    smres = smres.fillna(0)
    LOG.info(plantdate)
    cols = ["precip", "av_det", "sw1"] if scenario == 59 else ["av_det", "sw1"]
    smres[cols].to_csv(
        "tab2_%s.csv" % (plantdate.strftime("%b%d"),),
        float_format="%.4f",
        index=False,
    )


def main():
    """Go Main Go."""
    apr10 = datetime.date(2000, 4, 10)
    with open("myhucs.txt") as fh:
        hucs = [x.strip() for x in fh.readlines()]
    for scenario in range(59, 70):
        plantdate = apr10 + datetime.timedelta(days=(scenario - 59) * 5)
        do_scenario(scenario, plantdate, hucs)


if __name__ == "__main__":
    main()
