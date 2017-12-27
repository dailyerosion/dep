"""My purpose in life is to harvest the WEPP env (erosion output) files

The arguments to call me require the SCENARIO to be provided, but you can
also do any of the following:

    # default to yesterday
    python env2database.py 0
    # reprocess all of 2015
    python env2database.py 0 2015
    # reprocess all of Feb 2015
    python env2database.py 0 2015 02
    # reprocess 21 Feb 2015
    python env2database.py 0 2015 02 21
    # reprocess it all
    python env2database.py 0 all

"""
from __future__ import print_function
import os
import datetime
import multiprocessing
import sys
import unittest
import numpy as np
import pandas as pd
from tqdm import tqdm
import geopandas as gpd
from rasterstats import zonal_stats
from affine import Affine
from pyiem import dep as dep_utils
from pyiem.util import get_dbconn

PRECIP_AFF = Affine(0.01, 0., dep_utils.WEST, 0., -0.01, dep_utils.NORTH)


def find_huc12s():
    """yield a listing of huc12s with output!"""
    res = []
    for huc8 in os.listdir("/i/%s/env" % (SCENARIO, )):
        for huc12 in os.listdir("/i/%s/env/%s" % (SCENARIO, huc8)):
            res.append(huc8+huc12)
    return res


def readfile(huc12, fn):
    try:
        df = dep_utils.read_env(fn)
    except Exception as exp:
        print("\nABORT: Attempting to read: %s resulted in: %s\n" % (fn, exp))
        return None
    key = "%s_%s" % (huc12,
                     int(fn.split("/")[-1].split(".")[0].split("_")[1]))
    df['delivery'] = df['sed_del'] / lengths[key]
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
        if argv[2] == 'all':
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


def load_precip(dates, huc12s):
    """Compute the HUC12 spatially averaged precip

    This provides the `qc_precip` value stored in the database for each HUC12,
    so that we have complete precipitation accounting as the other database
    table fields are based on WEPP output, which does not report all precip
    events.

    Args:
      dates (list): the dates we need precip data for

    Returns:
      dict of [date][huc12]
    """
    # 1. Build GeoPandas DataFrame of HUC12s of interest
    idep = get_dbconn('idep')
    huc12df = gpd.GeoDataFrame.from_postgis("""
        SELECT huc_12, ST_Transform(simple_geom, 4326) as geo
        from huc12 WHERE scenario = 0
    """, idep, index_col='huc_12', geom_col='geo')
    # 2. Loop over dates
    res = {}
    for date in tqdm(dates, disable=(not sys.stdout.isatty())):
        res[date] = {}
        fn = date.strftime("/mnt/idep2/data/dailyprecip/%Y/%Y%m%d.npy")
        if not os.path.isfile(fn):
            print("Missing precip: %s" % (fn,))
            for huc12 in huc12df.index.values:
                res[date][huc12] = 0
            continue
        pcp = np.flipud(np.load(fn))
        # nodata here represents the value that is set to missing within the
        # source dataset!, setting to zero has strange side affects
        zs = zonal_stats(huc12df['geo'], pcp, affine=PRECIP_AFF, nodata=-1,
                         all_touched=True)
        i = 0
        for huc12, _ in huc12df.itertuples():
            res[date][huc12] = zs[i]['mean']
            i += 1
    return res


def load_lengths():
    idep = get_dbconn('idep')
    icursor = idep.cursor()
    _lengths = {}
    icursor.execute("""
    SELECT huc_12, fpath, ST_Length(geom) from flowpaths where
    scenario = %s
    """, (SCENARIO,))
    for row in icursor:
        _lengths["%s_%s" % (row[0], row[1])] = row[2]
    return _lengths


def delete_previous_entries(huc12):
    """Remove whatever previous data we have for this huc12 and dates"""
    pgconn = get_dbconn('idep')
    icursor = pgconn.cursor()
    icursor.execute("""
        DELETE from results_by_huc12 WHERE
        valid in %s and scenario = %s and huc_12 = %s
    """, (tuple(dates), SCENARIO, huc12))

    deleted = icursor.rowcount
    icursor.close()
    pgconn.commit()
    pgconn.close()
    return deleted


def save_results(huc12, df):
    """Save our output to the database"""
    pgconn = get_dbconn('idep')
    icursor = pgconn.cursor()
    inserts = 0
    skipped = len(dates) - len(df.index)
    for _, row in df.iterrows():
        # We don't care about the output when the follow conditions
        # are not meet
        if (row.qc_precip < 0.254 and row.avg_loss < 0.01 and
                row.avg_delivery < 0.01 and row.avg_runoff < 1):
            skipped += 1
            continue
        inserts += 1
        icursor.execute("""INSERT into results_by_huc12
        (huc_12, valid, scenario,
        min_precip, avg_precip, max_precip,
        min_loss, avg_loss, max_loss,
        min_runoff, avg_runoff, max_runoff,
        min_delivery, avg_delivery, max_delivery,
        qc_precip) VALUES
        (%s, %s, %s,
        coalesce(%s, 0), coalesce(%s, 0), coalesce(%s, 0),
        coalesce(%s, 0), coalesce(%s, 0), coalesce(%s, 0),
        coalesce(%s, 0), coalesce(%s, 0), coalesce(%s, 0),
        coalesce(%s, 0), coalesce(%s, 0), coalesce(%s, 0),
        %s)""", (row.huc12, row['date'], SCENARIO,
                 row.min_precip, row.avg_precip, row.max_precip,
                 row.min_loss, row.avg_loss, row.max_loss,
                 row.min_runoff, row.avg_runoff, row.max_runoff,
                 row.min_delivery, row.avg_delivery, row.max_delivery,
                 row.qc_precip))
    icursor.close()
    pgconn.commit()
    return inserts, skipped


def update_metadata(dates):
    pgconn = get_dbconn('idep')
    icursor = pgconn.cursor()
    maxdate = max(dates)
    icursor.execute("""SELECT value from properties where
    key = 'last_date_%s'""" % (SCENARIO, ))
    if icursor.rowcount == 0:
        icursor.execute("""INSERT into properties(key, value)
        values ('last_date_%s', '%s')
        """ % (SCENARIO, maxdate.strftime("%Y-%m-%d")))
    icursor.execute("""UPDATE properties
    SET value = '%s' WHERE key = 'last_date_%s' and value < '%s'
    """ % (maxdate.strftime("%Y-%m-%d"), SCENARIO,
           maxdate.strftime("%Y-%m-%d")))
    icursor.close()
    pgconn.commit()


def do_huc12(huc12):
    """Process a huc12's worth of WEPP output files"""
    basedir = "/i/%s/env/%s/%s" % (SCENARIO, huc12[:8], huc12[8:])
    frames = [readfile(huc12, basedir+"/"+f) for f in os.listdir(basedir)]
    if len(frames) == 0 or any([f is None for f in frames]):
        return huc12, None, None, None
    # Push all dataframes into one
    df = pd.concat(frames)
    df.fillna(0, inplace=True)
    hillslopes = len(frames)
    rows = []
    deleted = delete_previous_entries(huc12)
    for date in dates:
        df2 = df[df.date == date]
        # We have no data, any previous entries were deleted above already
        qc_precip = 0 if SCENARIO > 0 else precip[date][huc12]
        if len(df2.index) == 0 and qc_precip == 0:
            continue
        # Do computation
        rows.append(
            compute_res(df2, date, huc12, hillslopes, qc_precip))
    if not rows:
        return huc12, 0, len(dates), deleted
    # save results
    df = pd.DataFrame(rows)
    # Prevent any NaN values
    df.fillna(0, inplace=True)
    _inserts, _skipped = save_results(huc12, df)

    return huc12, _inserts, _skipped, deleted


if __name__ == '__main__':
    # We are ready to do stuff!
    # We need to keep stuff in the global namespace to keep multiprocessing
    # happy, at least I think that is the reason we do this
    SCENARIO = int(sys.argv[1])
    lengths = load_lengths()
    global dates  # unsure why this is needed to make pydev happy
    dates = determine_dates(sys.argv)
    huc12s = find_huc12s()
    if SCENARIO == 0:
        precip = load_precip(dates, huc12s)
    else:
        print("WARNING: qc_precip will be zero in the database")

    # Begin the processing work now!
    pool = multiprocessing.Pool()
    totalinserts = 0
    totalskipped = 0
    for huc12, inserts, skipped, deleted in tqdm(
            pool.imap_unordered(do_huc12, huc12s), total=len(huc12s),
            disable=(not sys.stdout.isatty())):
        if inserts is None:
            print("ERROR: huc12 %s returned 0 data" % (huc12,))
            continue
        totalinserts += inserts
        totalskipped += skipped
    print("env2database.py inserts: %s skips: %s deleted: %s" % (totalinserts,
                                                                 totalskipped,
                                                                 deleted))
    update_metadata(dates)


class Tests(unittest.TestCase):

    def setUp(self):
        global SCENARIO
        SCENARIO = 0

    def test_dohuc12(self):
        res, _, _ = do_huc12('102400130105')
        self.assertTrue(len(res.index) > 2)

    def test_dates(self):
        """ Make sure we can properly parse dates """
        dates = determine_dates([None, 0])
        self.assertEquals(len(dates), 1)
        dates = determine_dates([None, 0, "2012"])
        self.assertEquals(len(dates), 366)
        dates = determine_dates([None, 0, "2015", "02"])
        self.assertEquals(len(dates), 28)
        dates = determine_dates([None, 0, "2015", "02", "01"])
        self.assertEquals(dates[0], datetime.date(2015, 2, 1))
