"""
Bootstrap and Add a Climate File.

    python add_clifile.py <scenario> <lon> <lat>
"""

import os
import shutil
import subprocess
import sys

import pandas as pd
import requests
from pyiem.util import convert_value, logger

from pydep.io.wepp import read_cli
from pydep.util import get_cli_fname

LOG = logger()


def finder(lon, lat, clscenario):
    """The logic of finding a file."""
    # https://stackoverflow.com/questions/398299/looping-in-a-spiral
    x = y = 0
    dx = 0
    dy = -1
    # points near the domain edge need to seach a bit further than 0.25deg
    X = 40
    Y = 40
    for _ in range(40**2):
        if (-X / 2 < x <= X / 2) and (-Y / 2 < y <= Y / 2):
            newfn = get_cli_fname(lon + x * 0.01, lat + y * 0.01, clscenario)
            if os.path.isfile(newfn):
                return newfn
        if x == y or (x < 0 and x == -y) or (x > 0 and x == 1 - y):
            dx, dy = -dy, dx
        x, y = x + dx, y + dy
    return None


def missing_logic(scenario, fn):
    """Figure out what to do when this filename is missing"""
    print("Searching for replacement for '%s'" % (fn,))
    lon = float(fn[17:23])
    lat = float(fn[24:30])
    if not os.path.isdir(os.path.dirname(fn)):
        os.makedirs(os.path.dirname(fn))
    # So there should be a file at an interval of 0.25
    lon2 = lon - (lon * 100 % 25) / 100.0
    lat2 = lat - (lat * 100 % 25) / 100.0
    testfn = get_cli_fname(lon2, lat2, scenario)
    if not os.path.isfile(testfn):
        print("Whoa, why doesn't %s exist?" % (testfn,))
        sys.exit()
    print("%s->%s" % (testfn, fn))
    shutil.copyfile(testfn, fn)


def main(argv):
    """Go Main Go!"""
    scenario = argv[1]
    lon = float(argv[2])
    lat = float(argv[3])
    newfn = get_cli_fname(lon, lat, scenario)
    if os.path.isfile(newfn):
        LOG.info("Exiting, file %s already exists", newfn)
        return
    # Locate neighbor, copy file
    oldfn = finder(lon, lat, scenario)
    LOG.info("%s -> %s", oldfn, newfn)
    shutil.copyfile(oldfn, newfn)
    # Edit Header to correct location
    cmd = ["python", "edit_cli_header.py", newfn]
    subprocess.call(cmd)
    # Read file, query MRMS webservice to look for biggest variances
    clidf = read_cli(newfn)
    dfs = []
    for year in range(2007, 2024):
        req = requests.get(
            f"https://mesonet.agron.iastate.edu/iemre/multiday/{year}-01-01/"
            f"{year}-12-31/{lat}/{lon}/json"
        )
        dfs.append(pd.DataFrame(req.json()["data"]))
    obs = (
        pd.concat(dfs)
        .assign(
            date=lambda df_: pd.to_datetime(df_["date"]),
            daily_precip_mm=(
                lambda df_: convert_value(df_["mrms_precip_in"], "in", "mm")
            ),
        )
        .set_index("date")
    )
    clidf["mrms"] = obs["daily_precip_mm"]
    clidf["diff"] = (clidf["pcpn"] - clidf["mrms"]).abs().fillna(0)
    queue = ""
    for dt, row in (
        clidf.sort_values("diff", ascending=False).head(15).iterrows()
    ):
        LOG.info("Do %s pcpn: %s mrms: %s", dt, row["pcpn"], row["mrms"])
        queue += f"python daily_clifile_editor.py 4 3 5 0 {dt:%Y %m %d}\n"
    print(queue)


if __name__ == "__main__":
    main(sys.argv)
