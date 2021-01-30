"""Edit a DEP Climate file.

Usage:
    python daily_climate_editor.py <xtile> <ytile> <tilesz> \
        <scenario> <YYYY> <mm> <dd>

Where tiles start in the lower left corner and are 2x2 deg in size, TODO

development laptop has data for 3 March 2019, 23 May 2009, and 8 Jun 2009

"""
import datetime
import sys
import os
import unittest
from multiprocessing import Pool, cpu_count
from multiprocessing.pool import ThreadPool

import numpy as np
import pytz
from scipy.interpolate import NearestNDInterpolator
from PIL import Image
from pyiem import iemre
from pyiem.dep import SOUTH, WEST, NORTH, EAST, get_cli_fname
from pyiem.util import ncopen, logger, convert_value

LOG = logger()
XTILE = int(sys.argv[1])
YTILE = int(sys.argv[2])
# Tilesize was arrived at thru non-scientific testing
TILESIZE = int(sys.argv[3])
SCENARIO = int(sys.argv[4])
MYSOUTH = SOUTH + YTILE * TILESIZE
MYNORTH = min([MYSOUTH + TILESIZE, NORTH])
MYWEST = WEST + XTILE * TILESIZE
MYEAST = min([MYWEST + TILESIZE, EAST])
YS = int((MYNORTH - MYSOUTH) * 100)
XS = int((MYEAST - MYWEST) * 100)
HIGH_TEMP = np.zeros((YS, XS), np.float16)
LOW_TEMP = np.zeros((YS, XS), np.float16)
DEWPOINT = np.zeros((YS, XS), np.float16)
WIND = np.zeros((YS, XS), np.float16)
SOLAR = np.zeros((YS, XS), np.float16)
# Optimize array for the types of operations we do, since the time axis is
# continuous memory
PRECIP = np.zeros((YS, XS, 30 * 24), np.float16)
STAGE4 = np.zeros((YS, XS), np.float16)
ST4PATH = "/mesonet/data/stage4"

# used for breakpoint logic
ZEROHOUR = datetime.datetime(2000, 1, 1, 0, 0)

# How many CPUs are we going to burn
CPUCOUNT = max([4, int(cpu_count() / 4)])
MEMORY = {"stamp": datetime.datetime.now()}


def get_xy_from_lonlat(lon, lat):
    """Get the grid position"""
    xidx = int((lon - MYWEST) * 100.0)
    yidx = int((lat - MYSOUTH) * 100.0)
    return [xidx, yidx]


def iemre_bounds_check(name, val, lower, upper):
    """Make sure our data is within bounds, if not, exit!"""
    minval = np.nanmin(val)
    maxval = np.nanmax(val)
    if np.ma.is_masked(minval) or minval < lower or maxval > upper:
        LOG.info(
            "FATAL: iemre failure %s %.3f to %.3f [%.3f to %.3f]",
            name,
            minval,
            maxval,
            lower,
            upper,
        )
        sys.exit(3)
    return val


def load_iemre():
    """Use IEM Reanalysis for non-precip data

    24km product is smoothed down to the 0.01 degree grid
    """
    LOG.debug("load_iemre() called")
    xaxis = np.arange(MYWEST, MYEAST, 0.01)
    yaxis = np.arange(MYSOUTH, MYNORTH, 0.01)
    xi, yi = np.meshgrid(xaxis, yaxis)

    fn = iemre.get_daily_ncname(VALID.year)
    if not os.path.isfile(fn):
        LOG.debug("Missing %s for load_solar, aborting", fn)
        sys.exit(3)
    with ncopen(fn) as nc:
        offset = iemre.daily_offset(VALID)
        lats = nc.variables["lat"][:]
        lons = nc.variables["lon"][:]
        lons, lats = np.meshgrid(lons, lats)

        # Storage is W m-2, we want langleys per day
        data = nc.variables["rsds"][offset, :, :] * 86400.0 / 1000000.0 * 23.9
        # Default to a value of 300 when this data is missing, for some reason
        nn = NearestNDInterpolator(
            (np.ravel(lons), np.ravel(lats)), np.ravel(data)
        )
        SOLAR[:] = iemre_bounds_check("rsds", nn(xi, yi), 0, 1000)

        data = convert_value(
            nc.variables["high_tmpk"][offset, :, :], "degK", "degC"
        )
        nn = NearestNDInterpolator(
            (np.ravel(lons), np.ravel(lats)), np.ravel(data)
        )
        HIGH_TEMP[:] = iemre_bounds_check("high_tmpk", nn(xi, yi), -60, 60)

        data = convert_value(
            nc.variables["low_tmpk"][offset, :, :], "degK", "degC"
        )
        nn = NearestNDInterpolator(
            (np.ravel(lons), np.ravel(lats)), np.ravel(data)
        )
        LOW_TEMP[:] = iemre_bounds_check("low_tmpk", nn(xi, yi), -60, 60)

        data = convert_value(
            nc.variables["avg_dwpk"][offset, :, :], "degK", "degC"
        )
        nn = NearestNDInterpolator(
            (np.ravel(lons), np.ravel(lats)), np.ravel(data)
        )
        DEWPOINT[:] = iemre_bounds_check("avg_dwpk", nn(xi, yi), -60, 60)

        data = nc.variables["wind_speed"][offset, :, :]
        nn = NearestNDInterpolator(
            (np.ravel(lons), np.ravel(lats)), np.ravel(data)
        )
        WIND[:] = iemre_bounds_check("wind_speed", nn(xi, yi), 0, 30)
    LOG.debug("load_iemre() finished")


def load_stage4():
    """It sucks, but we need to load the stage IV data to give us something
    to benchmark the MRMS data against, to account for two things:
    1) Wind Farms
    2) Over-estimates
    """
    LOG.debug("load_stage4() called...")
    # The stage4 files store precip in the rears, so compute 1 AM
    one_am = datetime.datetime(VALID.year, VALID.month, VALID.day, 12, 0)
    one_am = one_am.replace(tzinfo=pytz.timezone("UTC"))
    one_am = one_am.astimezone(pytz.timezone("America/Chicago"))
    # stage4 data is stored in the rears, so 1am
    one_am = one_am.replace(hour=1, minute=0, second=0)
    # clever hack for CST/CDT
    tomorrow = one_am + datetime.timedelta(hours=36)
    tomorrow = tomorrow.replace(hour=1)

    sts_tidx = iemre.hourly_offset(one_am)
    ets_tidx = iemre.hourly_offset(tomorrow)
    LOG.debug(
        "stage4 sts_tidx:%s[%s] ets_tidx:%s[%s]",
        sts_tidx,
        one_am,
        ets_tidx,
        tomorrow,
    )
    with ncopen("%s/%s_stage4_hourly.nc" % (ST4PATH, VALID.year)) as nc:
        p01m = nc.variables["p01m"]

        lats = nc.variables["lat"][:]
        lons = nc.variables["lon"][:]
        # crossing jan 1
        if ets_tidx < sts_tidx:
            LOG.debug("Exercise special stageIV logic for jan1!")
            totals = np.sum(p01m[sts_tidx:, :, :], axis=0)
            with ncopen(
                "%s/%s_stage4_hourly.nc" % (ST4PATH, tomorrow.year)
            ) as nc2:
                p01m = nc2.variables["p01m"]
                totals += np.sum(p01m[:ets_tidx, :, :], axis=0)
        else:
            totals = np.sum(p01m[sts_tidx:ets_tidx, :, :], axis=0)

    if np.ma.max(totals) > 0:
        pass
    else:
        LOG.info("No StageIV data found, aborting...")
        sys.exit(3)
    # set a small non-zero number to keep things non-zero
    totals = np.where(totals > 0.001, totals, 0.001)

    xaxis = np.arange(MYWEST, MYEAST, 0.01)
    yaxis = np.arange(MYSOUTH, MYNORTH, 0.01)
    xi, yi = np.meshgrid(xaxis, yaxis)
    nn = NearestNDInterpolator(
        (lons.flatten(), lats.flatten()), totals.flatten()
    )
    STAGE4[:] = nn(xi, yi)
    write_grid(STAGE4, "stage4")
    LOG.debug("load_stage4() finished...")


def qc_precip():
    """Make some adjustments to the `precip` grid

    Not very sophisticated here, if the hires precip grid is within 33% of
    Stage IV, then we consider it good.  If not, then we apply a multiplier to
    bring it to near the stage IV value.
    """
    LOG.debug("qc_precip() called...")
    hires_total = np.sum(PRECIP, 2)
    LOG.debug("qc_precip() computed hires_total")
    # prevent zeros
    hires_total = np.where(hires_total < 0.01, 0.01, hires_total)
    LOG.debug("qc_precip() computed hires total and floored it to 0.01")
    write_grid(hires_total, "inqcprecip")
    multiplier = STAGE4 / hires_total
    LOG.debug("qc_precip() computed the multiplier")

    # Anything close to 1, set it to 1
    multiplier = np.where(
        np.logical_and(multiplier > 0.67, multiplier < 1.33), 1.0, multiplier
    )
    write_grid(multiplier, "multiplier")
    LOG.debug("qc_precip() bounded the multiplier")
    PRECIP[:] *= multiplier[:, :, None]
    LOG.debug("qc_precip() 4 done")
    PRECIP[np.isnan(PRECIP)] = 0.0
    write_grid(np.sum(PRECIP, 2), "outqcprecip")
    LOG.debug("qc_precip() finished...")


def _reader(arr):
    top = int((50.0 - MYNORTH) * 100.0)
    bottom = int((50.0 - MYSOUTH) * 100.0)

    right = int((MYEAST - -126.0) * 100.0)
    left = int((MYWEST - -126.0) * 100.0)

    (index, filename) = arr
    img = Image.open(filename)
    imgdata = np.array(img)
    # Convert the image data to dbz
    dbz = (np.flipud(imgdata[top:bottom, left:right]) - 7.0) * 5.0
    return (
        index,
        np.where(dbz < 255, ((10.0 ** (dbz / 10.0)) / 200.0) ** 0.625, 0),
    )


def load_precip_legacy():
    """ Compute a Legacy Precip product for dates prior to 1 Jan 2014"""
    LOG.debug("load_precip_legacy() called...")
    ts = 12 * 24  # 5 minute

    midnight = datetime.datetime(VALID.year, VALID.month, VALID.day, 12, 0)
    midnight = midnight.replace(tzinfo=pytz.timezone("UTC"))
    midnight = midnight.astimezone(pytz.timezone("America/Chicago"))
    midnight = midnight.replace(hour=0, minute=0, second=0)
    # clever hack for CST/CDT
    tomorrow = midnight + datetime.timedelta(hours=36)
    tomorrow = tomorrow.replace(hour=0)

    now = midnight
    m5 = np.zeros((ts, YS, XS), np.float16)
    tidx = 0
    filenames = []
    indices = []
    # Load up the n0r data, every 5 minutes
    while now < tomorrow:
        utc = now.astimezone(pytz.timezone("UTC"))
        fn = utc.strftime(
            ("/mesonet/ARCHIVE/data/%Y/%m/%d/GIS/uscomp/" "n0r_%Y%m%d%H%M.png")
        )
        if os.path.isfile(fn):
            if tidx >= ts:
                # Abort as we are in CST->CDT
                break
            filenames.append(fn)
            indices.append(tidx)
        else:
            LOG.info("daily_clifile_editor missing: %s", fn)

        now += datetime.timedelta(minutes=5)
        tidx += 1

    with Pool() as pool:
        for tidx, data in pool.imap_unordered(
            _reader, zip(indices, filenames)
        ):
            m5[tidx, :, :] = data
    LOG.debug("load_precip_legacy() finished loading N0R Composites")
    m5 = np.transpose(m5, (1, 2, 0)).copy()
    LOG.debug("load_precip_legacy() transposed the data!")
    m5total = np.sum(m5, 2)
    LOG.debug("load_precip_legacy() computed sum(m5)")
    wm5 = m5 / m5total[:, :, None]
    LOG.debug("load_precip_legacy() computed weights of m5")

    minute2 = np.arange(0, 60 * 24, 2)
    minute5 = np.arange(0, 60 * 24, 5)

    def _compute(yidx, xidx):
        """expensive computation that needs vectorized, somehow"""
        s4total = STAGE4[yidx, xidx]
        # any stage IV totals less than 0.4mm are ignored, so effectively 0
        if s4total < 0.4:
            return
        # Interpolate weights to a 2 minute interval grid
        # we divide by 2.5 to downscale the 5 minute values to 2 minute
        weights = np.interp(minute2, minute5, wm5[yidx, xidx, :]) / 2.5
        # Now apply the weights to the s4total
        PRECIP[yidx, xidx, :] = weights * s4total

    for x in range(XS):
        for y in range(YS):
            _compute(y, x)

    LOG.debug("load_precip_legacy() finished precip calculation")


def load_precip():
    """ Load the 5 minute precipitation data into our ginormus grid """
    LOG.debug("load_precip() called...")
    ts = 30 * 24  # 2 minute

    midnight = datetime.datetime(VALID.year, VALID.month, VALID.day, 12, 0)
    midnight = midnight.replace(tzinfo=pytz.timezone("UTC"))
    midnight = midnight.astimezone(pytz.timezone("America/Chicago"))
    midnight = midnight.replace(hour=0, minute=0, second=0)
    # clever hack for CST/CDT
    tomorrow = midnight + datetime.timedelta(hours=36)
    tomorrow = tomorrow.replace(hour=0)

    top = int((55.0 - MYNORTH) * 100.0)
    bottom = int((55.0 - MYSOUTH) * 100.0)

    right = int((MYEAST - -130.0) * 100.0)
    left = int((MYWEST - -130.0) * 100.0)
    # (myx, myy) = get_xy_from_lonlat(-93.6, 41.99)
    # samplex = int((-96.37 - -130.)*100.)
    # sampley = int((55. - 42.71)*100)

    # Oopsy we discovered a problem
    a2m_divisor = 10.0 if (VALID < datetime.date(2015, 1, 1)) else 50.0

    now = midnight
    # Require at least 75% data coverage, if not, we will abort back to legacy
    quorum = 720 * 0.75
    fns = []
    while now < tomorrow:
        utc = now.astimezone(pytz.UTC)
        fn = utc.strftime(
            ("/mesonet/ARCHIVE/data/%Y/%m/%d/GIS/mrms/" "a2m_%Y%m%d%H%M.png")
        )
        if os.path.isfile(fn):
            quorum -= 1
            fns.append(fn)
        else:
            fns.append(None)
            LOG.info("daily_clifile_editor missing: %s", fn)

        now += datetime.timedelta(minutes=2)
    if quorum > 0:
        LOG.info(
            "WARNING: Failed quorum with MRMS a2m %.1f, loading legacy", quorum
        )
        PRECIP[:] = 0
        load_precip_legacy()

    def _reader(tidx, fn):
        """Reader."""
        if fn is None:
            return tidx, 0
        img = Image.open(fn)
        imgdata = np.array(img)
        # sample out and then flip top to bottom!
        return tidx, np.flipud(imgdata[top:bottom, left:right])

    def _cb(args):
        """write data."""
        tidx, data = args
        PRECIP[:, :, tidx] = np.where(data < 255, data / a2m_divisor, 0)

    LOG.debug("load_precip() starting %s threads to read a2m", CPUCOUNT)
    with ThreadPool(CPUCOUNT) as pool:
        for tidx, fn in enumerate(fns):
            # we ignore an hour for CDT->CST, meh
            if tidx >= ts:
                continue
            pool.apply_async(_reader, (tidx, fn), callback=_cb)
        pool.close()
        pool.join()
    LOG.debug("load_precip() finished...")


def bpstr(ts, accum):
    """Make a string representation of this breakpoint and accumulation"""
    return "%02i.%02i  %6.2f" % (ts.hour, ts.minute / 60.0 * 100.0, accum)


def compute_breakpoint(ar, accumThreshold=2.0, intensityThreshold=1.0):
    """Compute the breakpoint data based on this array of data!

    To prevent massive ASCII text files, we do some simplification to the
    precipitation dataset.  We want to retain the significant rates though.

    Args:
      ar (array-like): precipitation accumulations every 2 minutes...
      accumThreshold (float): ammount of accumulation before writing bp
      intensityThreshold (float): ammount of intensity before writing bp

    Returns:
        list(str) of breakpoint precipitation
    """
    total = np.sum(ar)
    # Any total less than (0.01in) is not of concern, might as well be zero
    if total < 0.254:
        return []
    bp = None
    # in mm
    accum = 0
    lastaccum = 0
    lasti = 0
    for i, intensity in enumerate(ar):
        if intensity < 0.001:
            continue
        # Need to initialize the breakpoint data
        if bp is None:
            ts = ZEROHOUR + datetime.timedelta(minutes=(i * 2))
            bp = [bpstr(ts, 0)]
        accum += intensity
        lasti = i
        if (
            accum - lastaccum
        ) > accumThreshold or intensity > intensityThreshold:
            lastaccum = accum
            if (i + 1) == len(ar):
                ts = ZEROHOUR.replace(hour=23, minute=59)
            else:
                ts = ZEROHOUR + datetime.timedelta(minutes=((i + 1) * 2))
            bp.append(bpstr(ts, accum))
    if accum != lastaccum:
        if (lasti + 1) == len(ar):
            ts = ZEROHOUR.replace(hour=23, minute=59)
        else:
            ts = ZEROHOUR + datetime.timedelta(minutes=((lasti + 1) * 2))
        bp.append(
            "%02i.%02i  %6.2f" % (ts.hour, ts.minute / 60.0 * 100.0, accum)
        )
    return bp


def myjob(row):
    """ Thread job, yo """
    [xidx, yidx] = row
    lon = MYWEST + xidx * 0.01
    lat = MYSOUTH + yidx * 0.01
    fn = get_cli_fname(lon, lat, SCENARIO)
    if not os.path.isfile(fn):
        return False

    # Okay we have work to do
    data = open(fn, "r").read()
    pos = data.find(VALID.strftime("%-d\t%-m\t%Y"))
    if pos == -1:
        LOG.info("Date find failure for %s", fn)
        return False

    pos2 = data[pos:].find(
        (VALID + datetime.timedelta(days=1)).strftime("%-d\t%-m\t%Y")
    )
    if pos2 == -1:
        LOG.info("Date2 find failure for %s", fn)
        return False

    bpdata = compute_breakpoint(PRECIP[yidx, xidx, :])
    if bpdata is None:
        bpdata = []

    thisday = (
        "%s\t%s\t%s\t%s\t%3.1f\t%3.1f\t%4.0f\t%4.1f\t%s\t%4.1f\n%s%s"
    ) % (
        VALID.day,
        VALID.month,
        VALID.year,
        len(bpdata),
        HIGH_TEMP[yidx, xidx],
        LOW_TEMP[yidx, xidx],
        SOLAR[yidx, xidx],
        WIND[yidx, xidx],
        0,
        DEWPOINT[yidx, xidx],
        "\n".join(bpdata),
        "\n" if bpdata else "",
    )

    with open(fn, "w") as fh:
        fh.write(data[:pos] + thisday + data[(pos + pos2) :])
    return True


def write_grid(grid, fnadd=""):
    """Save off the daily precip totals for usage later in computing huc_12"""
    LOG.debug("write_grid() called...")
    if fnadd != "" and not sys.stdout.isatty():
        LOG.debug("not writting extra grid to disk")
        return
    basedir = "/mnt/idep2/data/dailyprecip/%s" % (VALID.year,)
    if not os.path.isdir(basedir):
        os.makedirs(basedir)
    np.save(
        "%s/%s%s.tile_%s_%s"
        % (basedir, VALID.strftime("%Y%m%d"), fnadd, XTILE, YTILE),
        grid,
    )
    LOG.debug("write_grid() finished...")


def precip_workflow():
    """Drive the precipitation workflow

    Args:
      valid (date): The date that we care about
    """
    # zero out precip in the case of rerunning this code segment
    PRECIP[:] = 0
    STAGE4[:] = 0
    load_stage4()
    # We have MRMS a2m RASTER files prior to 1 Jan 2015, but these files used
    # a very poor choice of data interval of 0.1mm, which is not large enough
    # to capture low intensity events.  Files after 1 Jan 2015 used a better
    # 0.02mm resolution
    if VALID.year < 2015:
        load_precip_legacy()
    else:
        load_precip()
    qc_precip()
    write_grid(np.sum(PRECIP, 2))


def workflow():
    """ The workflow to get the weather data variables we want! """
    LOG.debug(
        "Domain south: %s north: %s west: %s east: %s",
        MYSOUTH,
        MYNORTH,
        MYWEST,
        MYEAST,
    )
    # 1. Max Temp C
    # 2. Min Temp C
    # 3. Radiation l/d
    # 4. wind mps
    # 6. Mean dewpoint C
    load_iemre()
    # 5. wind direction (always zero)
    # 7. breakpoint precip mm
    precip_workflow()

    LOG.debug("building queue")
    queue = []
    for yidx in range(YS):
        for xidx in range(XS):
            queue.append([xidx, yidx])

    LOG.debug("starting pool")
    sz = len(queue)
    sts = datetime.datetime.now()
    success = 0
    lsuccess = 0
    with Pool(CPUCOUNT) as pool:
        for i, res in enumerate(pool.imap_unordered(myjob, queue), 1):
            if res:
                success += 1
            if success > 0 and success % 20000 == 0 and lsuccess != success:
                delta = datetime.datetime.now() - sts
                secs = delta.microseconds / 1000000.0 + delta.seconds
                rate = success / secs
                remaining = ((sz - i) / rate) / 3600.0
                LOG.debug(
                    (
                        "%5.2fh Processed %6s/%6s/%6s [%.2f /sec] "
                        "remaining: %5.2fh"
                    ),
                    secs / 3600.0,
                    success,
                    i,
                    sz,
                    rate,
                    remaining,
                )
                lsuccess = success

    LOG.debug("daily_clifile_editor edited %s files...", success)


if __name__ == "__main__":
    # This is important to keep valid in global scope
    VALID = datetime.date(int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7]))

    workflow()


class test(unittest.TestCase):
    """Some tests are better than no tests?"""

    def test_speed(self):
        """Test the speed of the processing"""
        global SCENARIO, VALID
        SCENARIO = 0
        VALID = datetime.date(2014, 10, 10)
        sts = datetime.datetime.now()
        myjob(get_xy_from_lonlat(-91.44, 41.28))
        ets = datetime.datetime.now()
        delta = (ets - sts).total_seconds()
        LOG.info(
            "Processed 1 file in %.5f secs, %.0f files per sec",
            delta,
            1.0 / delta,
        )
        self.assertTrue(1 == 0)

    def test_bp(self):
        """ issue #6 invalid time """
        data = np.zeros([30 * 24])
        data[0] = 3.2
        bp = compute_breakpoint(data)
        self.assertEqual(bp[0], "00.00    0.00")
        self.assertEqual(bp[1], "00.03    3.20")
        data[0] = 0
        data[24 * 30 - 1] = 9.99
        bp = compute_breakpoint(data)
        self.assertEqual(bp[0], "23.96    0.00")
        self.assertEqual(bp[1], "23.98    9.99")

        data[24 * 30 - 1] = 10.99
        bp = compute_breakpoint(data)
        self.assertEqual(bp[0], "23.96    0.00")
        self.assertEqual(bp[1], "23.98   10.99")

        # Do some random futzing
        for _ in range(1000):
            data = np.random.randint(20, size=(30 * 24,))
            bp = compute_breakpoint(data)
            lastts = -1
            lastaccum = -1
            for b in bp:
                tokens = b.split()
                if float(tokens[0]) <= lastts or float(tokens[1]) <= lastaccum:
                    LOG.info(data)
                    LOG.info(bp)
                    self.assertTrue(1 == 0)
                lastts = float(tokens[0])
                lastaccum = float(tokens[1])
