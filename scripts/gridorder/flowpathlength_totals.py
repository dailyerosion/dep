"""Examination of erosion totals vs flowpath length"""
from __future__ import print_function
import os
import datetime
import multiprocessing
import sys

import pandas as pd
import numpy as np
import psycopg2
from tqdm import tqdm
from pyiem import dep as dep_utils


def find_huc12s():
    """yield a listing of huc12s with output!"""
    pgconn = psycopg2.connect(database='idep', host='iemdb', user='nobody')
    cursor = pgconn.cursor()
    cursor.execute("""
        SELECT huc_12 from huc12 WHERE scenario = 0
        and states ~* 'IA'
        """)
    res = []
    for row in cursor:
        res.append(row[0])
    return res


def readfile(huc12, fn):
    try:
        df = dep_utils.read_env(fn)
    except:
        return None
    key = "%s_%s" % (huc12,
                     int(fn.split("/")[-1].split(".")[0].split("_")[1]))
    df['delivery'] = df['sed_del'] / lengths[key]
    df['flowpath'] = key
    df['length'] = lengths[key]
    return df


def do_huc12(huc12):
    """Process a huc12's worth of WEPP output files"""
    basedir = "/i/%s/env/%s/%s" % (SCENARIO, huc12[:8], huc12[8:])
    if not os.path.isdir(basedir):
        return None, huc12, 0
    frames = [readfile(huc12, basedir+"/"+f) for f in os.listdir(basedir)]
    if len(frames) == 0 or any([f is None for f in frames]):
        return None, huc12, 0
    df = pd.concat(frames)
    return df, huc12, len(frames)


def compute_res(df, date, huc12, slopes, qc_precip):
    """Compute things"""
    allhits = (slopes == len(df.index))
    slopes = float(slopes)
    return dict(date=date, huc12=huc12,
                min_precip=(df.precip.min() if allhits else 0),
                avg_precip=(df.precip.sum() / slopes),
                max_precip=df.precip.max(),
                min_loss=(df.av_det.min() if allhits else 0),
                avg_loss=(df.av_det.sum() / slopes),
                max_loss=df.av_det.max(),
                min_runoff=(df.runoff.min() if allhits else 0),
                avg_runoff=(df.runoff.sum() / slopes),
                max_runoff=df.runoff.max(),
                min_delivery=(df.delivery.min() if allhits else 0),
                avg_delivery=(df.delivery.sum() / slopes),
                max_delivery=df.delivery.max(),
                qc_precip=qc_precip
                )


def load_lengths():
    idep = psycopg2.connect(database='idep', host='iemdb')
    icursor = idep.cursor()
    lengths = {}
    icursor.execute("""
    SELECT huc_12, fpath, ST_Length(geom) from flowpaths where
    scenario = %s
    """, (SCENARIO,))
    for row in icursor:
        lengths["%s_%s" % (row[0], row[1])] = row[2]
    print("load_lengths() loaded %s entries" % (len(lengths), ))
    return lengths


if __name__ == '__main__':
    # We are ready to do stuff!
    # We need to keep stuff in the global namespace to keep multiprocessing
    # happy, at least I think that is the reason we do this
    SCENARIO = sys.argv[1]
    lengths = load_lengths()
    huc12s = find_huc12s()

    # Begin the processing work now!
    pool = multiprocessing.Pool()
    for (df, huc12, slopes) in tqdm(pool.imap_unordered(do_huc12, huc12s),
                                    total=len(huc12s),
                                    disable=(not sys.stdout.isatty())):
        if df is None:
            print("ERROR: huc12 %s returned 0 data" % (huc12,))
            continue
        df.to_csv('dfs/%s.csv' % (huc12,))
