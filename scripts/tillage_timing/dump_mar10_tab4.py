"""Dump for tab2 of requested 10 march 2020 spreadsheet.

"""
import glob

from pyiem.dep import read_wb
from pyiem.util import logger
import pandas as pd
from pydep.io.wepp import read_env

LOG = logger()


def do_scenario(scenario, hucs):
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
        (smdf["date"] >= pd.to_datetime("2018/1/1"))
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
        (envdf["date"] >= pd.to_datetime("2018/1/1"))
        & (envdf["date"] < pd.to_datetime("2019/1/1"))
    ]
    envdf["jday"] = pd.to_numeric(
        envdf["date"].dt.strftime("%j"), downcast="integer"
    )
    # Manually compute to account for zeros
    res = (envdf.groupby("jday").sum() / float(len(envdfs))).copy()
    smres["precip"] = res["precip"]
    smres["av_det"] = res["av_det"]
    smres = smres.fillna(0)
    cols = ["precip", "av_det", "sw1"] if scenario == 81 else ["av_det", "sw1"]
    LOG.info("dumping scenario: %s", scenario)
    smres[cols].to_csv(
        "tab4_%s.csv" % (scenario,), float_format="%.4f", index=False
    )


def main():
    """Go Main Go."""
    hucs = [x.strip() for x in open("myhucs.txt").readlines()]
    for scenario in range(81, 91):
        do_scenario(scenario, hucs)


if __name__ == "__main__":
    main()
