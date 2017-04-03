"""Collect the water balance for a given today"""
import pandas as pd
import os
import datetime
import multiprocessing
import sys
import numpy as np
import psycopg2
from tqdm import tqdm
from pyiem import dep as dep_utils
import geopandas as gpd
from rasterstats import zonal_stats
from affine import Affine

PRECIP_AFF = Affine(0.01, 0., dep_utils.WEST, 0., -0.01, dep_utils.NORTH)


def find_huc12s():
    """yield a listing of huc12s with output!"""
    res = []
    for huc8 in os.listdir("/i/%s/wb" % (SCENARIO, )):
        for huc12 in os.listdir("/i/%s/wb/%s" % (SCENARIO, huc8)):
            res.append(huc8+huc12)
    return res


def readfile(huc12, fn):
    try:
        df = dep_utils.read_wb(fn)
    except Exception as exp:
        print("\nABORT: Attempting to read: %s resulted in: %s\n" % (fn, exp))
        return None
    return df


def determine_date(argv):
    """Figure out which date we are interested in processing"""
    today = datetime.date.today()
    if len(argv) == 2:
        # Option 1, we have no arguments, so we assume yesterday
        return today - datetime.timedelta(days=1)
    return datetime.date(int(argv[2]), int(argv[3]), int(argv[4]))


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
    idep = psycopg2.connect(database='idep', host='iemdb')
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


def do_huc12(huc12):
    """Process a huc12's worth of WEPP output files"""
    basedir = "/i/%s/wb/%s/%s" % (SCENARIO, huc12[:8], huc12[8:])
    frames = [readfile(huc12, basedir+"/"+f) for f in os.listdir(basedir)]
    if len(frames) == 0 or any([f is None for f in frames]):
        return huc12, None, None
    # Push all dataframes into one
    df = pd.concat(frames)
    df2 = df[df.date == date].mean()

    return huc12, df2['ep'] + df2['es'] + df2['er'], df2['runoff']


if __name__ == '__main__':
    # We are ready to do stuff!
    # We need to keep stuff in the global namespace to keep multiprocessing
    # happy, at least I think that is the reason we do this
    SCENARIO = int(sys.argv[1])
    date = determine_date(sys.argv)
    huc12s = find_huc12s()
    precip = load_precip([date], huc12s)

    # Begin the processing work now!
    pool = multiprocessing.Pool()
    totalinserts = 0
    totalskipped = 0
    o = open("%s_wb.csv" % (date.strftime("%Y%m%d"),), 'w')
    o.write("HUC12,VALID,PRECIP_MM,ET_MM,RUNOFF_MM\n")
    stamp = date.strftime("%Y-%m-%d")
    for huc12, et, runoff in tqdm(
            pool.imap_unordered(do_huc12, huc12s), total=len(huc12s),
            disable=(not sys.stdout.isatty())):
        if et is not None:
            if not np.isnan(et):
                o.write("%s,%s,%.2f,%.2f,%.2f\n" % (huc12, stamp,
                                                    precip[date][huc12],
                                                    et, runoff))
    o.close()
