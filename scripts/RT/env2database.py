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
from multiprocessing import Pool
import sys
import numpy as np
import pandas as pd
from tqdm import tqdm
import geopandas as gpd
from rasterstats import zonal_stats
from affine import Affine
from pyiem import dep as dep_utils
from pyiem.util import get_dbconn, logger

LOG = logger()
PRECIP_AFF = Affine(0.01, 0.0, dep_utils.WEST, 0.0, -0.01, dep_utils.NORTH)
CONFIG = {"subset": False}


def find_huc12s(scenario):
    """yield a listing of huc12s with output!"""
    if os.path.isfile("myhucs.txt"):
        LOG.warning("Using myhucs.txt to guide processing...")
        CONFIG["subset"] = True
        return [s.strip() for s in open("myhucs.txt").readlines()]

    res = []
    for huc8 in os.listdir("/i/%s/env" % (scenario,)):
        for huc12 in os.listdir("/i/%s/env/%s" % (scenario, huc8)):
            res.append(huc8 + huc12)
    return res


def readfile(fn, lengths):
    """Our env reader."""
    try:
        df = dep_utils.read_env(fn)
    except Exception as exp:
        print("\nABORT: Attempting to read: %s resulted in: %s\n" % (fn, exp))
        return None
    key = int(fn.split("/")[-1].split(".")[0].split("_")[1])
    df["delivery"] = df["sed_del"] / lengths[key]
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


def compute_res(df, date, slopes, qc_precip):
    """Compute things"""
    allhits = slopes == len(df.index)
    slopes = float(slopes)
    # NB: code was added to WEPP to output every precipitation/runoff event,
    # so the average precip here is more accurate than before.
    return dict(
        date=date,
        count=len(df.index),
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
        qc_precip=qc_precip,
    )


def load_precip(dates, huc12s):
    """Compute the HUC12 spatially averaged precip

    This provides the `qc_precip` value stored in the database for each HUC12,
    so that we have complete precipitation accounting as the other database
    table fields are based on WEPP output, which does not report all precip
    events.

    Args:
      dates (list): the dates we need precip data for
      huc12s (list): listing of huc12s of interest, use if CONFIG['subset']

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
    if CONFIG["subset"]:
        huc12df = huc12df.loc[huc12s]
    # 2. Loop over dates
    res = {}
    for date in tqdm(dates, disable=(not sys.stdout.isatty())):
        fn = date.strftime("/mnt/idep2/data/dailyprecip/%Y/%Y%m%d.npy")
        if not os.path.isfile(fn):
            print("Missing precip: %s" % (fn,))
            for huc12 in huc12df.index.values:
                d = res.setdefault(huc12, [])
                d.append(0)
            continue
        pcp = np.flipud(np.load(fn))
        # nodata here represents the value that is set to missing within the
        # source dataset!, setting to zero has strange side affects
        zs = zonal_stats(
            huc12df["geo"], pcp, affine=PRECIP_AFF, nodata=-1, all_touched=True
        )
        i = 0
        for huc12, _ in huc12df.itertuples():
            d = res.setdefault(huc12, [])
            d.append(zs[i]["mean"])
            i += 1
    return res


def load_lengths(scenario):
    """Build out our flowpath lengths."""
    sdf = dep_utils.load_scenarios()
    idep = get_dbconn("idep")
    icursor = idep.cursor()
    res = {}
    icursor.execute(
        """
        SELECT huc_12, fpath, ST_Length(geom) from flowpaths where
        scenario = %s
    """,
        (int(sdf.loc[scenario, "flowpath_scenario"]),),
    )
    for row in icursor:
        d = res.setdefault(row[0], dict())
        d[row[1]] = row[2]
    return res


def delete_previous_entries(icursor, scenario, huc12, dates):
    """Remove whatever previous data we have for this huc12 and dates"""
    if len(dates) > 366:
        # Means we are running for 'all'
        icursor.execute(
            """
            DELETE from results_by_huc12 WHERE
            scenario = %s and huc_12 = %s
        """,
            (scenario, huc12),
        )
    else:
        icursor.execute(
            """
            DELETE from results_by_huc12 WHERE
            valid in %s and scenario = %s and huc_12 = %s
        """,
            (tuple(dates), scenario, huc12),
        )
    return icursor.rowcount


def save_results(icursor, scenario, huc12, df, dates):
    """Save our output to the database"""
    inserts = 0
    skipped = len(dates) - len(df.index)
    for _, row in df.iterrows():
        # test both sides of the coin to see that we can indeed skip dumping
        # this date to the databse.
        if row["qc_precip"] < 0.254 and row["count"] == 0:
            skipped += 1
            continue
        inserts += 1
        icursor.execute(
            """
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
        """,
            (
                huc12,
                row["date"],
                scenario,
                row["min_precip"],
                row["avg_precip"],
                row["max_precip"],
                row["min_loss"],
                row["avg_loss"],
                row["max_loss"],
                row["min_runoff"],
                row["avg_runoff"],
                row["max_runoff"],
                row["min_delivery"],
                row["avg_delivery"],
                row["max_delivery"],
                row["qc_precip"],
            ),
        )
    return inserts, skipped


def update_metadata(scenario, dates):
    """Update database property for this scenario."""
    pgconn = get_dbconn("idep")
    icursor = pgconn.cursor()
    maxdate = max(dates)
    icursor.execute(
        """
        SELECT value from properties where
        key = 'last_date_%s'
    """
        % (scenario,)
    )
    if icursor.rowcount == 0:
        icursor.execute(
            """
            INSERT into properties(key, value)
            values ('last_date_%s', '%s')
        """
            % (scenario, maxdate.strftime("%Y-%m-%d"))
        )
    icursor.execute(
        """
        UPDATE properties
        SET value = '%s' WHERE key = 'last_date_%s' and value < '%s'
    """
        % (
            maxdate.strftime("%Y-%m-%d"),
            scenario,
            maxdate.strftime("%Y-%m-%d"),
        )
    )
    icursor.close()
    pgconn.commit()


def do_huc12(arg):
    """Process a huc12's worth of WEPP output files"""
    scenario, huc12, lengths, dates, precip = arg
    pgconn = get_dbconn("idep")
    icursor = pgconn.cursor()
    basedir = "/i/%s/env/%s/%s" % (scenario, huc12[:8], huc12[8:])
    frames = [
        readfile(basedir + "/" + f, lengths) for f in os.listdir(basedir)
    ]
    if not frames or any([f is None for f in frames]):
        return huc12, None, None, None
    # Push all dataframes into one
    df = pd.concat(frames)
    if df.empty:
        print("FAIL huc12: %s resulted in empty data frame" % (huc12,))
        return huc12, None, None, None
    df.fillna(0, inplace=True)
    hillslopes = len(frames)
    rows = []
    deleted = delete_previous_entries(icursor, scenario, huc12, dates)
    for i, date in enumerate(dates):
        # df['date'] is datetime64, so need to cast
        df2 = df[df["date"].dt.date == date]
        # We have no data, any previous entries were deleted above already
        qc_precip = precip[i]
        if df2.empty and qc_precip == 0:
            continue
        # Do computation
        rows.append(compute_res(df2, date, hillslopes, qc_precip))
    if not rows:
        icursor.close()
        pgconn.commit()
        return huc12, 0, len(dates), deleted
    # save results
    df = pd.DataFrame(rows)
    # Prevent any NaN values
    df.fillna(0, inplace=True)
    inserts, skipped = save_results(icursor, scenario, huc12, df, dates)
    icursor.close()
    pgconn.commit()

    return huc12, inserts, skipped, deleted


def main(argv):
    """Go Main Go."""
    scenario = int(argv[1])
    lengths = load_lengths(scenario)
    dates = determine_dates(sys.argv)
    huc12s = find_huc12s(scenario)
    precip = load_precip(dates, huc12s)
    jobs = []
    for huc12 in huc12s:
        if huc12 not in precip:
            LOG.info("Skipping huc12 %s with no precip", huc12)
            continue
        jobs.append([scenario, huc12, lengths[huc12], dates, precip[huc12]])

    # Begin the processing work now!
    # NB: Usage of a ThreadPool here ended in tears (so slow)
    pool = Pool()
    totalinserts = 0
    totalskipped = 0
    totaldeleted = 0
    for huc12, inserts, skipped, deleted in tqdm(
        pool.imap_unordered(do_huc12, jobs),
        total=len(jobs),
        disable=(not sys.stdout.isatty()),
    ):
        if inserts is None:
            print("ERROR: huc12 %s returned 0 data" % (huc12,))
            continue
        totalinserts += inserts
        totalskipped += skipped
        totaldeleted += deleted
    print(
        "env2database.py inserts: %s skips: %s deleted: %s"
        % (totalinserts, totalskipped, totaldeleted)
    )
    update_metadata(scenario, dates)


if __name__ == "__main__":
    main(sys.argv)


def test_dohuc12():
    """Can we process a huc12"""
    lengths = load_lengths(0)
    myhuc = "102400130105"
    res, _, _, _ = do_huc12(
        [0, myhuc, lengths[myhuc], [datetime.date(2014, 9, 9)], [0]]
    )
    assert res == myhuc


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
