"""Proctor script for running the SWEEP model.

See dailyerosion/dep#36 for generally more details.
"""
import sys
import shutil
import subprocess
from multiprocessing import Pool

from pyiem.util import get_dbconn, logger
from pyiem.iemre import find_ij
from tqdm import tqdm
from pandas.io.sql import read_sql

HUC12S = ["090201081101", "090201081102", "090201060605"]
LOG = logger()


def get_wind_obs(lon, lat):
    """Get what we need from IEMRE."""
    i, j = find_ij(lon, lat)
    # TODO in m/s
    return [20.0] * 24


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
    windobs = get_wind_obs(row["lon"], row["lat"])
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
        # TODO unsure which value yet
        erosion = float(tokens[3])
    return idx, erosion


def main():
    """Go Main Go."""
    pgconn = get_dbconn("idep")
    df = read_sql(
        """
        SELECT huc_12, fpath, scenario,
        ST_x(ST_Transform(ST_PointN(geom, 1), 4326)) as lon,
        ST_x(ST_Transform(ST_PointN(geom, 1), 4326)) as lat
        from flowpaths where scenario = 0
        and huc_12 in %s
    """,
        pgconn,
        params=(tuple(HUC12S),),
        index_col=None,
    )
    LOG.debug("found %s flowpaths to run for", len(df.index))
    jobs = list(df.iterrows())
    pool = Pool()
    progress = tqdm(
        pool.imap_unordered(workflow, jobs),
        total=len(df.index),
        disable=not sys.stdout.isatty(),
    )
    for idx, erosion in progress:
        df.at[idx, "erosion"] = erosion

    print(df[["huc_12", "erosion"]].groupby("huc_12").describe())


if __name__ == "__main__":
    main()
