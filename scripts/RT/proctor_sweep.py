"""Proctor script for running the SWEEP model.

See dailyerosion/dep#36 for generally more details.
"""
import argparse
import sys
import datetime
import shutil
import subprocess
from multiprocessing import Pool

from pyiem.util import get_dbconn, logger
import pandas as pd
import requests
from tqdm import tqdm
from pandas.io.sql import read_sql

HUC12S = ["090201081101", "090201081102", "090201060605"]
LOG = logger()


def get_wind_obs(date, lon, lat):
    """Get what we need from IEMRE."""
    uri = "http://iem.local/iemre/hourly/%s/%.2f/%.2f/json" % (
        date.strftime("%Y-%m-%d"),
        lat,
        lon,
    )
    try:
        res = requests.get(uri).json()
    except Exception:
        print(uri)
        sys.exit()
    hourly = []
    for entry in res["data"]:
        try:
            vel = (entry["uwnd"] ** 2 + entry["vwnd"] ** 2) ** 0.5
        except Exception:
            vel = 1.0
        hourly.append(vel)
    for _i in range(len(hourly), 24):
        hourly.append(1.0)
    return hourly


def workflow(arg):
    """Do what we need to do."""
    (idx, row) = arg
    # 1. Replace wind information in each sweepin file
    sweepinfn = "/i/%s/sweepin/%s/%s/%s_%s.sweepin" % (
        row["scenario"],
        row["huc_12"][:8],
        row["huc_12"][8:12],
        row["huc_12"],
        row["fpath"],
    )
    sweepoutfn = sweepinfn.replace("sweepin", "sweepout")
    erodfn = "/i/%s/sweepin/%s/%s/%s_%s.erod" % (
        row["scenario"],
        row["huc_12"][:8],
        row["huc_12"][8:12],
        row["huc_12"],
        row["fpath"],
    )
    windobs = get_wind_obs(row["date"], row["lon"], row["lat"])
    lines = list(open(sweepinfn).readlines())
    found = False
    for linenum, line in enumerate(lines):
        if not found and line.find(" awu(i)") > -1:
            found = True
            continue
        if found and not line.startswith("#"):
            for i in range(4):
                sl = slice(i * 6, (i + 1) * 6)
                lines[linenum + i] = (
                    " ".join([str(x) for x in windobs[sl]]) + "\n"
                )
            break
    with open(sweepinfn, "w") as fh:
        fh.write("".join(lines))
    # 2. Run Rscript to replace grph file content
    cmd = "Rscript --vanilla magic.R %s %s %s %s %s >& /dev/null" % (
        sweepinfn,
        sweepinfn.replace("sweepin", "grph"),
        sweepinfn.replace("sweepin", "sol"),
        row["date"].year,
        row["date"].strftime("%j"),
    )
    subprocess.call(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    # 3. Run sweep with given sweepin file, writing to sweepout
    cmd = '~/bin/sweep -i"%s" -Erod' % (sweepinfn,)
    subprocess.call(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    # can't control the Erod output file :/
    shutil.move(erodfn, sweepoutfn)
    # 4. Harvest the result and profit.
    erosion = None
    with open(sweepoutfn) as fh:
        tokens = fh.read().strip().split()
        # total soil loss, saltation loss, suspension loss, PM10 loss
        # TODO: units
        erosion = float(tokens[0])
    return idx, erosion


def usage():
    """Create the argparse instance."""
    parser = argparse.ArgumentParser("Send WEPP env info to the database")
    parser.add_argument("-s", "--scenario", required=True, type=int)
    parser.add_argument("-d", "--date", required=True)
    return parser


def main(argv):
    """Go Main Go."""
    parser = usage()
    args = parser.parse_args(argv[1:])
    pgconn = get_dbconn("idep")
    df = read_sql(
        """
        SELECT huc_12, fpath, scenario,
        ST_x(ST_Transform(ST_PointN(geom, 1), 4326)) as lon,
        ST_y(ST_Transform(ST_PointN(geom, 1), 4326)) as lat
        from flowpaths where scenario = %s
        and huc_12 in %s
    """,
        pgconn,
        params=(args.scenario, tuple(HUC12S)),
        index_col=None,
    )
    date = datetime.datetime.strptime(args.date, "%Y-%m-%d")
    df["date"] = pd.Timestamp(date)
    LOG.debug("found %s flowpaths to run for %s", len(df.index), date)
    jobs = list(df.iterrows())
    with Pool() as pool:
        progress = tqdm(
            pool.imap_unordered(workflow, jobs),
            total=len(df.index),
            disable=not sys.stdout.isatty(),
        )
        for idx, erosion in progress:
            df.at[idx, "erosion"] = erosion

    print(df[["huc_12", "erosion"]].groupby("huc_12").describe())


if __name__ == "__main__":
    main(sys.argv)
