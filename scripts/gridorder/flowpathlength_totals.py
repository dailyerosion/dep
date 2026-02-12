"""Examination of erosion totals vs flowpath length"""

import multiprocessing
import os
import sys

import pandas as pd
import psycopg
from pyiem.database import get_dbconn
from tqdm import tqdm

from pydep.io.wepp import read_env


def find_huc12s():
    """yield a listing of huc12s with output!"""
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()
    cursor.execute(
        """
        SELECT huc_12 from huc12 WHERE scenario = 0
        and states ~* 'IA'
        """
    )
    res = []
    for row in cursor:
        res.append(row[0])
    return res


def readfile(huc12, fn):
    """Read the file."""
    try:
        df = read_env(fn)
    except Exception:
        return None
    key = "%s_%s" % (huc12, int(fn.split("/")[-1].split(".")[0].split("_")[1]))
    df["delivery"] = df["sed_del"] / lengths[key]
    df["flowpath"] = key
    df["length"] = lengths[key]
    return df


def do_huc12(huc12):
    """Process a huc12's worth of WEPP output files"""
    basedir = "/i/%s/env/%s/%s" % (SCENARIO, huc12[:8], huc12[8:])
    if not os.path.isdir(basedir):
        return None, huc12, 0
    frames = [readfile(huc12, basedir + "/" + f) for f in os.listdir(basedir)]
    if len(frames) == 0 or any([f is None for f in frames]):
        return None, huc12, 0
    df = pd.concat(frames)
    return df, huc12, len(frames)


def load_lengths():
    """Placeholder."""
    idep = psycopg.connect(dname="idep", host="iemdb")
    icursor = idep.cursor()
    res = {}
    icursor.execute(
        """
    SELECT huc_12, fpath, ST_Length(geom) from flowpaths where
    scenario = %s
    """,
        (SCENARIO,),
    )
    for row in icursor:
        res["%s_%s" % (row[0], row[1])] = row[2]
    print("load_lengths() loaded %s entries" % (len(lengths),))
    return res


if __name__ == "__main__":
    # We are ready to do stuff!
    # We need to keep stuff in the global namespace to keep multiprocessing
    # happy, at least I think that is the reason we do this
    SCENARIO = sys.argv[1]
    lengths = load_lengths()
    huc12s = find_huc12s()

    # Begin the processing work now!
    pool = multiprocessing.Pool()
    for _df, _huc12, _slopes in tqdm(
        pool.imap_unordered(do_huc12, huc12s),
        total=len(huc12s),
        disable=(not sys.stdout.isatty()),
    ):
        if _df is None:
            print("ERROR: huc12 %s returned 0 data" % (_huc12,))
            continue
        _df.to_csv("dfs/%s.csv" % (_huc12,))
