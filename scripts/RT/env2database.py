import pandas as pd
import os
import datetime
import multiprocessing
import sys
import unittest
import numpy as np
import psycopg2


def find_huc12s():
    """yield a listing of huc12s with output!"""
    res = []
    for huc8 in os.listdir("/i/%s/env" % (SCENARIO, )):
        for huc12 in os.listdir("/i/%s/env/%s" % (SCENARIO, huc8)):
            res.append(huc8+huc12)
    return res


def readfile(fn):
    df = pd.read_table(fn,
                       skiprows=3, index_col=False, delim_whitespace=True,
                       header=None,
                       names=['day', 'month', 'year', 'precip', 'runoff',
                              'ir_det', 'av_det', 'mx_det', 'point',
                              'av_dep', 'max_dep', 'point2', 'sed_del',
                              'er'])
    df['hsid'] = int(fn.split("/")[-1].split(".")[0].split("_")[1])
    return df


def do_huc12(huc12):
    """Process a huc12's worth of WEPP output files"""
    basedir = "/i/%s/env/%s/%s" % (SCENARIO, huc12[:8], huc12[8:])
    frames = [readfile(basedir+"/"+f) for f in os.listdir(basedir)]
    if len(frames) == 0:
        return None, huc12, 0
    df = pd.concat(frames)
    df['year'] += 2006
    df['date'] = df[['year', 'month', 'day']].apply(
        lambda sx: datetime.date(*[int(s) for s in sx]), axis=1)
    return df, huc12, len(frames)


def determine_dates(argv):
    """Figure out which dates we are interested in processing"""
    res = []
    today = datetime.date.today()
    if len(argv) == 2:
        # Option 1, we have no arguments, so we assume yesterday
        res.append(today - datetime.timedelta(days=1))
    elif len(argv) == 3:
        # Option 2, we are running for an entire year, gulp
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
    """Load up the precip please """
    idep = psycopg2.connect(database='idep', host='iemdb')
    icursor = idep.cursor()
    huc12_centroids = {}
    icursor.execute("""
        WITH centers as (
         SELECT huc_12, ST_Transform(ST_Centroid(geom),4326) as g
         from ia_huc12
        )

        SELECT huc_12, ST_x(g), ST_y(g) from centers
    """)
    SOUTH = 36.9
    WEST = -99.2
    for row in icursor:
        y = int((row[2] - SOUTH) * 100.)
        x = int((row[1] - WEST) * 100.)
        huc12_centroids[row[0]] = [y, x]
    res = {}
    for date in dates:
        res[date] = {}
        fn = date.strftime("/mnt/idep2/data/dailyprecip/%Y/%Y%m%d.npy")
        precip = np.load(fn)
        for huc12 in huc12s:
            y, x = huc12_centroids[huc12]
            res[date][huc12] = precip[y, x]
    return res


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
    return lengths


def save_results(df, dates):
    """Save our output to the database"""
    pgconn = psycopg2.connect(database='idep', host='iemdb')
    icursor = pgconn.cursor()
    for date in dates:
        icursor.execute("""
            DELETE from results_by_huc12
            WHERE valid = %s and scenario = %s
            """, (date, SCENARIO))
        if icursor.rowcount > 0:
            print("DELETED %s rows for date %s" % (icursor.rowcount,
                                                   date))
        inserts = 0
        skipped = 0
        for _, row in df[df.date == date].iterrows():
            if (row.qc_precip < 1 or row.avg_loss < 0.01 or
                    row.avg_delivery < 0.01 or row.avg_runoff < 1):
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
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s)""", (row.huc12, date, SCENARIO,
                     row.min_precip, row.avg_precip, row.max_precip,
                     row.min_loss, row.avg_loss, row.max_loss,
                     row.min_runoff, row.avg_runoff, row.max_runoff,
                     row.min_delivery, row.avg_delivery, row.max_delivery,
                     row.qc_precip))
        print("ENTERED %s rows for date %s, skipped %s" % (inserts, date,
                                                           skipped))
    icursor.close()
    pgconn.commit()


def update_metadata(dates):
    pgconn = psycopg2.connect(database='idep', host='iemdb')
    icursor = pgconn.cursor()
    maxdate = max(dates)
    icursor.execute("""SELECT value from properties where
    key = 'last_date_%s'""" % (SCENARIO, ))
    if icursor.rowcount == 0:
        icursor.execute("""INSERT into properties(key, value)
        ('last_date_%s', '%s')""" % (SCENARIO, maxdate.strftime("%Y-%m-%d")))
    icursor.execute("""UPDATE properties
    SET value = '%s' WHERE key = 'last_date_%s' and value < '%s'
    """ % (maxdate.strftime("%Y-%m-%d"), SCENARIO,
           maxdate.strftime("%Y-%m-%d")))
    icursor.close()
    pgconn.commit()

if __name__ == '__main__':
    # We are ready to do stuff!
    SCENARIO = sys.argv[1]
    lengths = load_lengths()
    dates = determine_dates(sys.argv)
    pool = multiprocessing.Pool()
    huc12s = find_huc12s()[:201]
    precip = load_precip(dates, huc12s)
    result = []
    sz = len(huc12s)
    tm = datetime.datetime.now()
    for i, (df, huc12, slopes) in enumerate(
                                    pool.imap_unordered(do_huc12, huc12s), 1):
        if df is None:
            print("ERROR: huc12 %s returned 0 data" % (huc12,))
            continue
        for date in dates:
            df2 = df[df.date == date].copy()
            df2['length'] = df2['hsid'].apply(
                lambda s: lengths['%s_%s' % (huc12, s)])
            df2['delivery'] = df2['sed_del'] / df2['length']
            qc_precip = precip[date][huc12]
            result.append(compute_res(df2, date, huc12, slopes, qc_precip))
        if i > 0 and i % 100 == 0:
            secs = (datetime.datetime.now() - tm).total_seconds()
            tm = datetime.datetime.now()
            print(("  %s %4i/%4i %.2f huc12/s"
                   ) % (tm.strftime("%H:%M:%S%p"), i, sz, 100. / secs))
    df = pd.DataFrame(result)
    save_results(df, dates)
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
