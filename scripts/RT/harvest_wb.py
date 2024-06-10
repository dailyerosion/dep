"""Collect the water balance for a given today"""

import datetime
import multiprocessing
import os
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
from affine import Affine
from pydep.io.dep import read_wb
from pyiem.iemre import NORTH, WEST
from pyiem.util import get_dbconn
from rasterstats import zonal_stats
from tqdm import tqdm

PRECIP_AFF = Affine(0.01, 0.0, WEST, 0.0, -0.01, NORTH)


def find_huc12s():
    """yield a listing of huc12s with output!"""
    res = []
    for huc8 in os.listdir("/i/%s/wb" % (SCENARIO,)):
        for huc12 in os.listdir("/i/%s/wb/%s" % (SCENARIO, huc8)):
            res.append(huc8 + huc12)
    return res


def readfile(huc12, fn):
    """Read one file please"""
    try:
        df = read_wb(fn)
    except Exception as exp:
        print("\nABORT: Attempting to read: %s resulted in: %s\n" % (fn, exp))
        return None
    return df


def determine_dates(argv):
    """Figure out which dates we are interested in processing"""
    res = []
    today = datetime.date.today()
    if len(argv) == 2:
        # Option 1, we have no arguments, so we assume yesterday
        res.append(today - datetime.timedelta(days=1))
    elif len(argv) == 3:
        # Option 2, we are running for an entire year, gulp
        if argv[2] == "all":
            now = datetime.date(2007, 1, 1)
            ets = datetime.date.today()
        else:
            now = datetime.date(int(argv[2]), 1, 1)
            ets = datetime.date(int(argv[2]) + 1, 1, 1)
        while now < ets:
            if now >= today:
                break
            res.append(now)
            now += datetime.timedelta(days=1)
    elif len(argv) == 4:
        # Option 3, we are running for a month
        now = datetime.date(int(argv[2]), int(argv[3]), 1)
        ets = now + datetime.timedelta(days=35)
        ets = ets.replace(day=1)
        while now < ets:
            if now >= today:
                break
            res.append(now)
            now += datetime.timedelta(days=1)
    elif len(argv) == 5:
        # Option 4, we are running for one date
        res.append(datetime.date(int(argv[2]), int(argv[3]), int(argv[4])))
    return res


def load_precip():
    """Compute the HUC12 spatially averaged precip

    This provides the `qc_precip` value stored in the database for each HUC12,
    so that we have complete precipitation accounting as the other database
    table fields are based on WEPP output, which does not report all precip
    events.

    Returns:
      dict of [date][huc12]
    """
    # 1. Build GeoPandas DataFrame of HUC12s of interest
    idep = get_dbconn("idep")
    huc12df = gpd.GeoDataFrame.from_postgis(
        """
        SELECT huc_12, ST_Transform(simple_geom, 4326) as geo
        from huc12 WHERE scenario = 0
    """,
        idep,
        index_col="huc_12",
        geom_col="geo",
    )
    # 2. Loop over dates
    myres = {}
    for mydate in tqdm(DATES, disable=(not sys.stdout.isatty())):
        myres[mydate] = {}
        fn = mydate.strftime("/mnt/idep2/data/dailyprecip/%Y/%Y%m%d.npy")
        if not os.path.isfile(fn):
            print("Missing precip: %s" % (fn,))
            for myhuc12 in huc12df.index.values:
                myres[mydate][myhuc12] = 0
            continue
        pcp = np.flipud(np.load(fn))
        # nodata here represents the value that is set to missing within the
        # source dataset!, setting to zero has strange side affects
        zs = zonal_stats(
            huc12df["geo"], pcp, affine=PRECIP_AFF, nodata=-1, all_touched=True
        )
        i = 0
        for _huc12, _ in huc12df.itertuples():
            myres[mydate][_huc12] = zs[i]["mean"]
            i += 1
    return myres


def do_huc12(_huc12):
    """Process a huc12's worth of WEPP output files"""
    basedir = "/i/%s/wb/%s/%s" % (SCENARIO, _huc12[:8], _huc12[8:])
    frames = [readfile(_huc12, basedir + "/" + f) for f in os.listdir(basedir)]
    rows = []
    if len(frames) == 0 or any([f is None for f in frames]):
        return rows
    # Push all dataframes into one
    df = pd.concat(frames)
    for mydate in DATES:
        df2 = df[df.date == mydate].mean()
        rows.append(
            [mydate, _huc12, df2["ep"] + df2["es"] + df2["er"], df2["runoff"]]
        )
    return rows


if __name__ == "__main__":
    # We are ready to do stuff!
    # We need to keep stuff in the global namespace to keep multiprocessing
    # happy, at least I think that is the reason we do this
    SCENARIO = int(sys.argv[1])
    DATES = determine_dates(sys.argv)
    HUC12S = find_huc12s()
    PRECIP = load_precip()

    # Begin the processing work now!
    POOL = multiprocessing.Pool()
    FPS = {}
    for _date in DATES:
        key = _date.strftime("%Y%m%d")
        FPS[key] = open("%s_wb.csv" % (_date.strftime("%Y%m%d"),), "w")
        FPS[key].write("HUC12,VALID,PRECIP_MM,ET_MM,RUNOFF_MM\n")
    for res in tqdm(
        POOL.imap_unordered(do_huc12, HUC12S),
        total=len(HUC12S),
        disable=(not sys.stdout.isatty()),
    ):
        for date, huc12, et, runoff in res:
            if et is None or np.isnan(et):
                continue
            key = date.strftime("%Y%m%d")
            FPS[key].write(
                ("%s,%s,%.2f,%.2f,%.2f\n")
                % (
                    huc12,
                    date.strftime("%Y-%m-%d"),
                    PRECIP[date][huc12],
                    et,
                    runoff,
                )
            )
    for key in FPS:
        FPS[key].close()
