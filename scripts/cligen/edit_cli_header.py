"""Keep the CLI file headers in sync."""
# stdlib
import os
import sys

# Third Party
import numpy as np
import pandas as pd
from pydep.util import get_cli_fname
from pyiem.iemre import EAST, NORTH, SOUTH, WEST, find_ij, get_dailyc_ncname
from pyiem.util import convert_value, logger, ncopen
from tqdm import tqdm

LOG = logger()
# Untracked here, but this version was used to fix the header column labels
REV = "HeaderRev: v20230605.1"


def monthly_avgs(lon, lat):
    """Do more work."""
    i, j = find_ij(lon, lat)
    with ncopen(get_dailyc_ncname()) as nc:
        highc = convert_value(
            nc.variables["high_tmpk"][:, j, i], "degK", "degC"
        )
        lowc = convert_value(nc.variables["low_tmpk"][:, j, i], "degK", "degC")
        p01d = nc.variables["p01d"][:, j, i]
        # MJ to langleys
        swdn = nc.variables["swdn"][:, j, i] * 23.9
    df = pd.DataFrame(
        {
            "highc": highc,
            "lowc": lowc,
            "p01d": p01d,
            "swdn": swdn,
        },
        index=pd.date_range("2000/01/01", "2000/12/31"),
    )
    return df.resample("m").agg(
        {"highc": "mean", "lowc": "mean", "p01d": "sum", "swdn": "mean"}
    )


def get_elevation(lon, lat):
    """Use opentopo."""
    # API services have limits, so alas
    # http://research.jisao.washington.edu/data_sets/elevation/
    with ncopen("/tmp/elev.americas.5-min.nc") as nc:
        lons = nc.variables["lon"]  # deg E
        lats = nc.variables["lat"]
        i = np.digitize(lon + 360, lons)
        j = np.digitize(lat, lats)
        elev = nc.variables["data"][0, j, i]
    return elev


def process(clifn):
    """Edit the given climate file."""
    lon, lat = [float(x) for x in os.path.basename(clifn)[:-4].split("x")]
    lon = 0 - lon

    with open(clifn, encoding="utf-8") as fh:
        lines = fh.readlines()
    if lines[2].find(REV) > -1:
        return
    # Set Station Name to something descriptive
    lines[2] = f"Station: Daily Erosion Project 0.01deg Grid Cell {REV}\n"
    # Set Lat/Lon from filename
    tokens = lines[4].strip().split()
    # Set Elevation via some web service
    elev = get_elevation(lon, lat)
    lines[4] = (
        f"{lat:.2f}  {lon:.2f}  {elev:.0f} "
        f"{tokens[3]} {tokens[4]} {tokens[5]}\n"
    )
    # Compute monthly avg high, low, radiation, rain
    df = monthly_avgs(lon, lat)
    lines[6] = " ".join(f"{x:-5.1f}" for x in df["highc"].values) + "\n"
    lines[8] = " ".join(f"{x:-5.1f}" for x in df["lowc"].values) + "\n"
    lines[10] = " ".join(f"{x:-5.1f}" for x in df["swdn"].values) + "\n"
    lines[12] = " ".join(f"{x:-5.1f}" for x in df["p01d"].values) + "\n"
    with open(clifn, "w", encoding="utf-8") as fh:
        fh.write("".join(lines))


def omnibus():
    """Do em all."""
    progress = tqdm(np.arange(WEST, EAST + 0.01, 0.01))
    for lon in progress:
        progress.set_description(f"{lon:.2f}")
        for lat in np.arange(SOUTH, NORTH + 0.01, 0.01):
            clifn = get_cli_fname(lon, lat)
            if not os.path.isfile(clifn):
                continue
            process(clifn)


def main(argv):
    """We ride or die."""
    if len(argv) == 1:
        omnibus()
        return
    process(argv[1])


if __name__ == "__main__":
    main(sys.argv)
