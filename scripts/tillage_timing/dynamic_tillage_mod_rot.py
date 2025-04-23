"""Yikes, inspect WB file, do dynamic tillage dates for 2018."""

import datetime
import sys

import pandas as pd
from pandas.io.sql import read_sql
from pyiem.util import get_dbconn
from tqdm import tqdm

from pydep.io.dep import read_wb

APR15 = pd.Timestamp(year=2018, month=4, day=15)
MAY30 = pd.Timestamp(year=2018, month=5, day=30)
THRESHOLDS = {81: 45, 82: 40, 83: 35, 84: 30, 85: 25, 86: 20, 87: 15}
PL_THRESHOLDS = {88: 1.0, 89: 0.9, 90: None}


def date_diagnostic(scenario, dates):
    """Look at some stats."""
    running = 0
    with open("scenario%s_dates.txt" % (scenario,), "w") as fp:
        fp.write("date,total\n")
        for date in pd.date_range(APR15, MAY30):
            hits = [d for d in dates if d == date]
            running += len(hits)
            fp.write("%s,%s\n" % (date, running))


def get_threshold_bypl(scenario, row):
    """Inspect the soil file for what we need."""
    fn = "/i/0/sol/%s/%s/%s_%s.sol" % (
        row["huc_12"][:8],
        row["huc_12"][8:],
        row["huc_12"],
        row["fpath"],
    )
    # Take the top layer of the first soil, good enough for now.
    with open(fn) as fp:
        line = fp.readlines()[4]
    tokens = line.strip().split()
    # depth, sand, clay, OM, CEC, Rock
    clay = float(tokens[2])
    om = float(tokens[3])
    pl = 14.22 + 0.005 * clay**2 + 3.63 * om - 0.048 * clay * om
    if PL_THRESHOLDS[scenario] is None:
        with open(fn) as fp:
            line = fp.readlines()[3]
        tokens = line.strip().split()
        satv = float(tokens[4])
        satm = satv / 2.65 * (1 - satv)
        return ((pl / 100.0 - 0.4 * satm) / 0.6) * 100.0
    return pl * PL_THRESHOLDS[scenario]


def compute_tillage_date(scenario, row):
    """Get the tillage date."""
    wbfn = "/i/0/wb/%s/%s/%s_%s.wb" % (
        row["huc_12"][:8],
        row["huc_12"][8:],
        row["huc_12"],
        row["fpath"],
    )
    wbdf = read_wb(wbfn)
    wbdf2 = wbdf[
        (
            (wbdf["ofe"] == 1)
            & (wbdf["date"] >= APR15)
            & (wbdf["date"] <= MAY30)
        )
    ]
    if scenario in THRESHOLDS:
        the_threshold = THRESHOLDS[scenario]
    else:
        the_threshold = get_threshold_bypl(scenario, row)
    wbdf3 = wbdf2[wbdf2["sw1"] < the_threshold]
    if len(wbdf3.index) > 0:
        tillage_date = wbdf3.iloc[0]["date"]
    else:
        tillage_date = MAY30
    return tillage_date


def main(argv):
    """Go Main Go."""
    scenario = int(argv[1])
    dbconn = get_dbconn("idep")
    # 0. Loop over flowpaths
    df = read_sql(
        """
        SELECT huc_12, fpath from flowpaths where scenario = %s
    """,
        dbconn,
        params=(scenario,),
    )
    print("Found %s flowpaths" % (len(df.index),))
    dates = []
    for i, row in tqdm(df.iterrows(), total=len(df.index)):
        # 1. Load up scenario 0 WB file
        tillage_date = compute_tillage_date(scenario, row)
        dates.append(tillage_date)
        # 2. load up prj file, figuring out which .rot file to edit
        prjfn = "/i/59/prj/%s/%s/%s_%s.prj" % (
            row["huc_12"][:8],
            row["huc_12"][8:],
            row["huc_12"],
            row["fpath"],
        )
        newprjfn = "/i/%s/%s" % (scenario, prjfn[5:])
        with open(newprjfn, "w") as fp:
            i = 0
            for line in open(prjfn):
                if line.find(".rot") == -1:
                    fp.write(line)
                    continue
                if not line.strip().startswith("File = "):
                    fp.write(line)
                    continue
                rotfn = (
                    "/home/akrherz/projects/dep/prj2wepp/wepp/data/"
                    "managements/SCEN59/%s"
                ) % (line.split("SCEN59/")[1][:-2],)
                newrotfn = "/i/%s/custom_rot/%s_%s_%s.rot" % (
                    scenario,
                    row["huc_12"],
                    row["fpath"],
                    i,
                )
                # 5. mod .prj file to see this new .rot
                fp.write('  File = "%s"\n' % (newrotfn,))
                i += 1
                # 3. Modify 2018 (year 12) .rot dates
                # 4. Save out .rot file somewhere per-flowpath specific
                with open(newrotfn, "w") as fp2:
                    for line2 in open(rotfn):
                        tokens = line2.split()
                        if (
                            len(tokens) > 4
                            and tokens[2] == "12"
                            and tokens[4] in ["Tillage", "Plant-Annual"]
                            and int(tokens[0]) < 7
                        ):
                            date = datetime.date(
                                2018, int(tokens[0]), int(tokens[1])
                            )
                            offset = datetime.date(2018, 4, 10) - date
                            nd = tillage_date - offset
                            newline = "%02i %02i %s" % (
                                nd.month,
                                nd.day,
                                " ".join(tokens[2:]),
                            )
                            fp2.write(newline + "\n")
                        else:
                            fp2.write(line2)

    # 6. cry
    date_diagnostic(scenario, dates)


if __name__ == "__main__":
    main(sys.argv)
