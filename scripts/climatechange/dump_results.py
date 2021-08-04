"""A plot of the deltas for erosion between scenarios."""
import os
import sys

from pyiem.dep import read_env
from pyiem.util import logger, get_dbconn
from tqdm import tqdm
import numpy as np

LOG = logger()


def readfile(fn, lengths):
    """Our env reader."""
    try:
        df = read_env(fn)
    except Exception as exp:
        LOG.info("ABORT: Attempting to read: %s resulted in: %s", fn, exp)
        sys.exit()
    # truncate anything newer than 2020
    df = df[df["year"] < 2021]
    key = int(fn.split("/")[-1].split(".")[0].split("_")[1])
    df["delivery"] = df["sed_del"] / lengths[key]
    return df


def load_lengths(hucs):
    """Build out our flowpath lengths."""
    idep = get_dbconn("idep")
    icursor = idep.cursor()
    res = {}
    icursor.execute(
        "SELECT huc_12, fpath, ST_Length(geom) from flowpaths where "
        "scenario = 0 and huc_12 in %s",
        (tuple(hucs),),
    )
    for row in icursor:
        d = res.setdefault(row[0], dict())
        d[row[1]] = row[2]
    return res


def main():
    """Go Main Go."""
    hucs = open("myhucs.txt").read().strip().split("\n")
    scenarios = [0]
    scenarios.extend(list(range(130, 140)))
    deltas = []
    baseline = None
    lengths = load_lengths(hucs)
    progress = tqdm(scenarios)
    for scenario in progress:
        vals = []
        for huc12 in hucs:
            progress.set_description(f"{scenario} {huc12}")
            mydir = f"/i/{scenario}/env/{huc12[:8]}/{huc12[8:]}"
            data = []
            for fn in os.listdir(mydir):
                res = readfile(os.path.join(mydir, fn), lengths[huc12])
                data.append(res["delivery"].sum())
            if not data:
                LOG.info("no data scenario: %s huc12: %s", scenario, huc12)
                sys.exit()
            vals.append(np.average(data))
        if scenario > 0:
            deltas.append((np.average(vals) - baseline) / baseline)
        else:
            baseline = np.average(vals)
    print(deltas)


if __name__ == "__main__":
    main()
