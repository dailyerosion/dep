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
from multiprocessing.pool import ThreadPool
import sys
import numpy as np
import pandas as pd
from tqdm import tqdm
import geopandas as gpd
from rasterstats import zonal_stats
from affine import Affine
from pyiem import dep as dep_utils
from pyiem.util import get_dbconn


def find_huc12s(scenario):
    """yield a listing of huc12s with output!"""
    res = []
    for huc8 in os.listdir("/i/%s/env" % (scenario, )):
        for huc12 in os.listdir("/i/%s/env/%s" % (scenario, huc8)):
            res.append(huc8+huc12)
    return res


def readfile(huc12, fn, lengths):
    """Our env reader."""
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


def compute_res(df, date, slopes, qc_precip):
    """Compute things"""
    allhits = (slopes == len(df.index))
    slopes = float(slopes)
    return dict(
        date=date,
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


def load_precip(scenario, dates):
    """Compute the HUC12 spatially averaged precip

    This provides the `qc_precip` value stored in the database for each HUC12,
    so that we have complete precipitation accounting as the other database
    table fields are based on WEPP output, which does not report all precip
    events.

    Args:
      scenario (int): our scenario of interest
      dates (list): the dates we need precip data for

    Returns:
      dict of [huc12][[ordered precip values]]
    """
    precip_aff = Affine(0.01, 0., dep_utils.WEST, 0., -0.01, dep_utils.NORTH)
    # 1. Build GeoPandas DataFrame of HUC12s of interest
    idep = get_dbconn('idep')
    sdf = dep_utils.load_scenarios()
    sql = """
        SELECT huc_12, ST_Transform(simple_geom, 4326) as geo
        from huc12 WHERE scenario = %s
    """
    huc12df = gpd.GeoDataFrame.from_postgis(
        sql, idep, params=(int(sdf.at[scenario, 'huc12_scenario']), ),
        index_col='huc_12', geom_col='geo'
    )
    # 2. Loop over dates
    res = dict(zip(huc12df.index.values, [[]]*len(huc12df.index)))
    for date in tqdm(dates, disable=(not sys.stdout.isatty())):
        fn = date.strftime("/mnt/idep2/data/dailyprecip/%Y/%Y%m%d.npy")
        if not os.path.isfile(fn):
            print("Missing precip: %s" % (fn,))
            for huc12 in huc12df.index.values:
                res[huc12].append(0)
            continue
        pcp = np.flipud(np.load(fn))
        # nodata here represents the value that is set to missing within the
        # source dataset!, setting to zero has strange side affects
        zs = zonal_stats(
            huc12df['geo'], pcp, affine=precip_aff, nodata=-1,
            all_touched=True
        )
        i = 0
        for huc12, _ in huc12df.itertuples():
            res[huc12].append(zs[i]['mean'])
            i += 1
    return res


def load_lengths(icursor, scenario):
    """Load hillslope lengths from the database."""
    _lengths = {}
    icursor.execute("""
        SELECT huc_12, fpath, ST_Length(geom) from flowpaths where
        scenario = %s
    """, (scenario,))
    for row in icursor:
        _lengths["%s_%s" % (row[0], row[1])] = row[2]
    return _lengths


def delete_previous_entries(icursor, huc12, dates, scenario):
    """Remove whatever previous data we have for this huc12 and dates"""
    icursor.execute("""
        DELETE from results_by_huc12 WHERE
        valid in %s and scenario = %s and huc_12 = %s
    """, (tuple(dates), scenario, huc12))

    deleted = icursor.rowcount
    return deleted


def save_results(icursor, huc12, df, dates, scenario):
    """Save our output to the database"""
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
        icursor.execute("""
            INSERT into results_by_huc12
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
            coalesce(%s, 0), coalesce(%s, 0), coalesce(%s, 0), %s)
        """, (huc12, row['date'], scenario,
              row.min_precip, row.avg_precip, row.max_precip,
              row.min_loss, row.avg_loss, row.max_loss,
              row.min_runoff, row.avg_runoff, row.max_runoff,
              row.min_delivery, row.avg_delivery, row.max_delivery,
              row.qc_precip)
        )
    return inserts, skipped


def update_metadata(icursor, dates, scenario):
    """update database for when we ran."""
    maxdate = max(dates)
    icursor.execute("""
        SELECT value from properties where
        key = 'last_date_%s'
    """ % (scenario, ))
    if icursor.rowcount == 0:
        icursor.execute("""
            INSERT into properties(key, value)
            values ('last_date_%s', '%s')
        """ % (scenario, maxdate.strftime("%Y-%m-%d")))
    icursor.execute("""
        UPDATE properties
        SET value = '%s' WHERE key = 'last_date_%s' and value < '%s'
    """ % (maxdate.strftime("%Y-%m-%d"), scenario,
           maxdate.strftime("%Y-%m-%d")))


def do_huc12(huc12, scenario, dates, huc12_precip, lengths):
    """Process a huc12's worth of WEPP output files"""
    basedir = "/i/%s/env/%s/%s" % (scenario, huc12[:8], huc12[8:])
    frames = [readfile(huc12, basedir+"/"+f, lengths)
              for f in os.listdir(basedir)]
    if not frames or any([f is None for f in frames]):
        return huc12, pd.DataFrame([])
    # Push all dataframes into one
    df = pd.concat(frames)
    df.fillna(0, inplace=True)
    hillslopes = len(frames)
    rows = []
    for i, date in enumerate(dates):
        # df['date'] is datetime64, so need to cast
        df2 = df[df['date'].dt.date == date]
        # We have no data, any previous entries were deleted above already
        qc_precip = huc12_precip[i]
        if df2.empty and qc_precip == 0:
            continue
        # Do computation
        rows.append(compute_res(df2, date, hillslopes, qc_precip))
    # save results
    df = pd.DataFrame(rows)
    # Prevent any NaN values
    df.fillna(0, inplace=True)
    return huc12, df


def main(argv):
    """Go Main Go."""
    scenario = int(argv[1])
    pgconn = get_dbconn('idep')
    icursor = pgconn.cursor()
    lengths = load_lengths(icursor, scenario)
    dates = determine_dates(sys.argv)
    huc12s = find_huc12s(scenario)
    precip = load_precip(scenario, dates)

    # Begin the processing work now!
    pool = ThreadPool()
    totalinserts = 0
    totalskipped = 0
    totaldeleted = 0

    def _do_huc12(huc12):
        """Proxy."""
        return do_huc12(huc12, scenario, dates, precip[huc12], lengths)

    errors = 0
    for huc12, df in tqdm(
            pool.imap_unordered(_do_huc12, huc12s), total=len(huc12s),
            disable=(not sys.stdout.isatty())):
        if df.empty:
            print("ERROR: huc12 %s returned 0 data" % (huc12,))
            errors += 1
            if errors > 100:
                print("ABORT due to errors > 100")
                sys.exit()
            continue

        deleted = delete_previous_entries(icursor, huc12, dates, scenario)
        inserts, skipped = save_results(icursor, huc12, df, dates, scenario)

        totalinserts += inserts
        totalskipped += skipped
        totaldeleted += deleted
    print("env2database.py inserts: %s skips: %s deleted: %s" % (
        totalinserts, totalskipped, totaldeleted)
    )
    update_metadata(icursor, dates, scenario)
    icursor.close()
    pgconn.commit()


def test_load_precip():
    """Can we load precip?"""
    res = load_precip(0, [datetime.date(2014, 9, 9)])
    assert res


def test_dohuc12():
    """Test something."""
    myhuc = '102400130105'
    lengths = {}
    for i in range(500):
        lengths["%s_%s" % (myhuc, i)] = 100.
    sts = datetime.datetime.utcnow()
    loops = 10
    for _ in range(loops):
        huc12, df = do_huc12(
            myhuc, 0, [datetime.date(2014, 9, 9)], [0], lengths)
    ets = datetime.datetime.utcnow()
    print("Did %s loops in %.3f per sec" % (
        loops, (ets - sts).total_seconds() / float(loops)))
    assert huc12 == myhuc
    assert len(df.index) == 1


def test_dates():
    """ Make sure we can properly parse dates """
    dates = determine_dates([None, 0])
    assert len(dates) == 1
    dates = determine_dates([None, 0, "2012"])
    assert len(dates) == 366
    dates = determine_dates([None, 0, "2015", "02"])
    assert len(dates) == 28
    dates = determine_dates([None, 0, "2015", "02", "01"])
    assert dates[0] == datetime.date(2015, 2, 1)


if __name__ == '__main__':
    main(sys.argv)
