"""
  This is it, we shall create our gridded weather analysis and edit the
  climate files!

  development laptop has data for 9 Sep 2014, 23 May 2009, and 8 Jun 2009

"""
from __future__ import print_function
import datetime
import sys
import os
import unittest
import logging
from multiprocessing import Pool

import numpy as np
import pytz
import netCDF4
from scipy.interpolate import NearestNDInterpolator
from PIL import Image
from pyiem import iemre
from pyiem.datatypes import temperature
from pyiem.dep import SOUTH, NORTH, EAST, WEST, get_cli_fname
from pyiem.util import ncopen

logging.basicConfig(format='%(asctime)-15s %(message)s')
LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

SCENARIO = sys.argv[1]
YS = int((NORTH - SOUTH) * 100.)
XS = int((EAST - WEST) * 100.)
HIGH_TEMP = np.zeros((YS, XS), np.float16)
LOW_TEMP = np.zeros((YS, XS), np.float16)
DEWPOINT = np.zeros((YS, XS), np.float16)
WIND = np.zeros((YS, XS), np.float16)
SOLAR = np.zeros((YS, XS), np.float16)
# Optimize array for the types of operations we do, since the time axis is
# continuous memory
PRECIP = np.zeros((YS, XS, 30*24), np.float16)
STAGE4 = np.zeros((YS, XS), np.float16)

# used for breakpoint logic
ZEROHOUR = datetime.datetime(2000, 1, 1, 0, 0)


def printt(msg):
    """Print a message with a timestamp included"""
    if sys.stdout.isatty():
        print(("%s %s"
               ) % (datetime.datetime.now().strftime("%H:%M:%S.%f"), msg))


def get_xy_from_lonlat(lon, lat):
    """Get the grid position"""
    xidx = int((lon - WEST) * 100.)
    yidx = int((lat - SOUTH) * 100.)
    return [xidx, yidx]


def iemre_bounds_check(name, val, lower, upper):
    """Make sure our data is within bounds, if not, exit!"""
    minval = np.nanmin(val)
    maxval = np.nanmax(val)
    if np.ma.is_masked(minval) or minval < lower or maxval > upper:
        print(("FATAL: iemre failure %s %.3f to %.3f [%.3f to %.3f]"
               ) % (name, minval, maxval, lower, upper))
        sys.exit()
    return val


def load_iemre():
    """Use IEM Reanalysis for non-precip data

    24km product is smoothed down to the 0.01 degree grid
    """
    printt("load_iemre() called")
    xaxis = np.arange(WEST, EAST, 0.01)
    yaxis = np.arange(SOUTH, NORTH, 0.01)
    xi, yi = np.meshgrid(xaxis, yaxis)

    fn = iemre.get_daily_ncname(VALID.year)
    if not os.path.isfile(fn):
        printt("Missing %s for load_solar, aborting" % (fn,))
        sys.exit()
    nc = netCDF4.Dataset(fn, 'r')
    offset = iemre.daily_offset(VALID)
    lats = nc.variables['lat'][:]
    lons = nc.variables['lon'][:]
    lons, lats = np.meshgrid(lons, lats)

    # Storage is W m-2, we want langleys per day
    data = nc.variables['rsds'][offset, :, :] * 86400. / 1000000. * 23.9
    # Default to a value of 300 when this data is missing, for some reason
    nn = NearestNDInterpolator((np.ravel(lons), np.ravel(lats)),
                               np.ravel(data))
    SOLAR[:] = iemre_bounds_check('rsds', nn(xi, yi), 0, 1000)

    data = temperature(nc.variables['high_tmpk'][offset, :, :], 'K').value('C')
    nn = NearestNDInterpolator((np.ravel(lons), np.ravel(lats)),
                               np.ravel(data))
    HIGH_TEMP[:] = iemre_bounds_check('high_tmpk', nn(xi, yi), -60, 60)

    data = temperature(nc.variables['low_tmpk'][offset, :, :], 'K').value('C')
    nn = NearestNDInterpolator((np.ravel(lons), np.ravel(lats)),
                               np.ravel(data))
    LOW_TEMP[:] = iemre_bounds_check('low_tmpk', nn(xi, yi), -60, 60)

    data = temperature(nc.variables['avg_dwpk'][offset, :, :], 'K').value('C')
    nn = NearestNDInterpolator((np.ravel(lons), np.ravel(lats)),
                               np.ravel(data))
    DEWPOINT[:] = iemre_bounds_check('avg_dwpk', nn(xi, yi), -60, 60)

    data = nc.variables['wind_speed'][offset, :, :]
    nn = NearestNDInterpolator((np.ravel(lons), np.ravel(lats)),
                               np.ravel(data))
    WIND[:] = iemre_bounds_check('wind_speed', nn(xi, yi), 0, 30)

    nc.close()
    printt("load_iemre() finished")


def load_stage4():
    """ It sucks, but we need to load the stage IV data to give us something
    to benchmark the MRMS data against, to account for two things:
    1) Wind Farms
    2) Over-estimates
    """
    printt("load_stage4() called...")
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
    printt(("stage4 sts_tidx:%s[%s] ets_tidx:%s[%s]"
            ) % (sts_tidx, one_am, ets_tidx, tomorrow))
    nc = ncopen("/mesonet/data/stage4/%s_stage4_hourly.nc" % (VALID.year, ))
    p01m = nc.variables['p01m']

    lats = nc.variables['lat'][:]
    lons = nc.variables['lon'][:]
    # crossing jan 1
    if ets_tidx < sts_tidx:
        printt("Exercise special stageIV logic for jan1!")
        totals = np.sum(p01m[sts_tidx:, :, :], axis=0)
        nc.close()
        nc = ncopen(
            "/mesonet/data/stage4/%s_stage4_hourly.nc" % (tomorrow.year, )
        )
        p01m = nc.variables['p01m']
        totals += np.sum(p01m[:ets_tidx, :, :], axis=0)
    else:
        totals = np.sum(p01m[sts_tidx:ets_tidx, :, :], axis=0)
    nc.close()

    if np.ma.max(totals) > 0:
        pass
    else:
        print('No StageIV data found, aborting...')
        sys.exit()
    # set a small non-zero number to keep things non-zero
    totals = np.where(totals > 0.001, totals, 0.001)

    xaxis = np.arange(WEST, EAST, 0.01)
    yaxis = np.arange(SOUTH, NORTH, 0.01)
    xi, yi = np.meshgrid(xaxis, yaxis)
    nn = NearestNDInterpolator((lons.flatten(), lats.flatten()),
                               totals.flatten())
    STAGE4[:] = nn(xi, yi)
    write_grid(STAGE4, 'stage4')
    printt("load_stage4() finished...")


def qc_precip():
    """Make some adjustments to the `precip` grid

    Not very sophisticated here, if the hires precip grid is within 33% of
    Stage IV, then we consider it good.  If not, then we apply a multiplier to
    bring it to near the stage IV value.
    """
    printt("qc_precip() called...")
    hires_total = np.sum(PRECIP, 2)
    printt("qc_precip() computed hires_total")
    # prevent zeros
    hires_total = np.where(hires_total < 0.01, 0.01, hires_total)
    printt("qc_precip() computed hires total and floored it to 0.01")
    write_grid(hires_total, 'inqcprecip')
    multiplier = STAGE4 / hires_total
    printt("qc_precip() computed the multiplier")

    # Anything close to 1, set it to 1
    multiplier = np.where(np.logical_and(multiplier > 0.67, multiplier < 1.33),
                          1., multiplier)
    write_grid(multiplier, 'multiplier')
    printt("qc_precip() bounded the multiplier")
    PRECIP[:] *= multiplier[:, :, None]
    printt("qc_precip() 4 done")
    PRECIP[np.isnan(PRECIP)] = 0.
    write_grid(np.sum(PRECIP, 2), 'outqcprecip')
    printt("qc_precip() finished...")


def _reader(arr):
    top = int((50. - NORTH) * 100.)
    bottom = int((50. - SOUTH) * 100.)

    right = int((EAST - -126.) * 100.)
    left = int((WEST - -126.) * 100.)

    (index, filename) = arr
    img = Image.open(filename)
    imgdata = np.array(img)
    # Convert the image data to dbz
    dbz = (np.flipud(imgdata[top:bottom, left:right]) - 7.) * 5.
    return (index,
            np.where(dbz < 255, ((10. ** (dbz/10.)) / 200.) ** 0.625, 0))


def load_precip_legacy():
    """ Compute a Legacy Precip product for dates prior to 1 Jan 2014"""
    printt("load_precip_legacy() called...")
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
        fn = utc.strftime(("/mesonet/ARCHIVE/data/%Y/%m/%d/GIS/uscomp/"
                           "n0r_%Y%m%d%H%M.png"))
        if os.path.isfile(fn):
            if tidx >= ts:
                # Abort as we are in CST->CDT
                break
            filenames.append(fn)
            indices.append(tidx)
        else:
            print('daily_clifile_editor missing: %s' % (fn,))

        now += datetime.timedelta(minutes=5)
        tidx += 1

    pool = Pool()
    for tidx, data in pool.imap_unordered(_reader, zip(indices, filenames)):
        m5[tidx, :, :] = data
    printt("load_precip_legacy() finished loading N0R Composites")
    m5 = np.transpose(m5, (1, 2, 0)).copy()
    printt("load_precip_legacy() transposed the data!")
    m5total = np.sum(m5, 2)
    printt("load_precip_legacy() computed sum(m5)")
    wm5 = m5 / m5total[:, :, None]
    printt("load_precip_legacy() computed weights of m5")

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

    _ = [_compute(y, x) for y in range(YS) for x in range(XS)]

    printt("load_precip_legacy() finished precip calculation")


def load_precip():
    """ Load the 5 minute precipitation data into our ginormus grid """
    ts = 30 * 24  # 2 minute

    midnight = datetime.datetime(VALID.year, VALID.month, VALID.day, 12, 0)
    midnight = midnight.replace(tzinfo=pytz.timezone("UTC"))
    midnight = midnight.astimezone(pytz.timezone("America/Chicago"))
    midnight = midnight.replace(hour=0, minute=0, second=0)
    # clever hack for CST/CDT
    tomorrow = midnight + datetime.timedelta(hours=36)
    tomorrow = tomorrow.replace(hour=0)

    top = int((55. - NORTH) * 100.)
    bottom = int((55. - SOUTH) * 100.)

    right = int((EAST - -130.) * 100.)
    left = int((WEST - -130.) * 100.)
    # (myx, myy) = get_xy_from_lonlat(-93.6, 41.99)
    # samplex = int((-96.37 - -130.)*100.)
    # sampley = int((55. - 42.71)*100)

    # Oopsy we discovered a problem
    a2m_divisor = 10. if (VALID < datetime.date(2015, 1, 1)) else 50.

    now = midnight
    # Require at least 75% data coverage, if not, we will abort back to legacy
    quorum = 720 * 0.75
    while now < tomorrow:
        utc = now.astimezone(pytz.timezone("UTC"))
        fn = utc.strftime(("/mesonet/ARCHIVE/data/%Y/%m/%d/GIS/mrms/"
                           "a2m_%Y%m%d%H%M.png"))
        if os.path.isfile(fn):
            quorum -= 1
            tidx = int((now - midnight).seconds / 120.)
            if tidx >= ts:
                # Abort as we are in CST->CDT
                return
            img = Image.open(fn)
            # --------------------------------------------------
            # OK, once and for all, 0,0 is the upper left!
            # units are 0.1mm
            imgdata = np.array(img)
            # sample out and then flip top to bottom!
            data = np.flipud(imgdata[top:bottom, left:right])
            # print now, data[myy, myx]
            # print np.shape(imgdata), bottom, top, left, right
            # print now, imgdata[sampley, samplex]
            # if imgdata[sampley, samplex] > 0:
            #    import matplotlib.pyplot as plt
            #    (fig, ax) = plt.subplots(2,1)
            #    ax[0].imshow(imgdata[0:3000, :])
            #    ax[1].imshow(data)
            #    fig.savefig('test.png')
            #    sys.exit()
            # Turn 255 (missing) into zeros
            PRECIP[:, :, tidx] = np.where(data < 255, data / a2m_divisor, 0)

        else:
            print('daily_clifile_editor missing: %s' % (fn,))

        now += datetime.timedelta(minutes=2)
    if quorum > 0:
        print(("WARNING: Failed quorum with MRMS a2m %.1f, loading legacy"
               ) % (quorum,))
        PRECIP[:] = 0
        load_precip_legacy()


def bpstr(ts, accum):
    """Make a string representation of this breakpoint and accumulation"""
    return "%02i.%02i  %6.2f" % (ts.hour, ts.minute / 60.0 * 100.,
                                 accum)


def compute_breakpoint(ar, accumThreshold=2., intensityThreshold=1.):
    """ Compute the breakpoint data based on this array of data!

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
            ts = ZEROHOUR + datetime.timedelta(minutes=(i*2))
            bp = [bpstr(ts, 0), ]
        accum += intensity
        lasti = i
        if ((accum - lastaccum) > accumThreshold or
                intensity > intensityThreshold):
            lastaccum = accum
            if (i + 1) == len(ar):
                ts = ZEROHOUR.replace(hour=23, minute=59)
            else:
                ts = ZEROHOUR + datetime.timedelta(minutes=((i+1)*2))
            bp.append(bpstr(ts, accum))
    if accum != lastaccum:
        # print("accum: %.5f lastaccum: %.5f lasti: %s" % (accum, lastaccum,
        #                                                 lasti))
        if (lasti + 1) == len(ar):
            ts = ZEROHOUR.replace(hour=23, minute=59)
        else:
            ts = ZEROHOUR + datetime.timedelta(minutes=((lasti + 1)*2))
        bp.append("%02i.%02i  %6.2f" % (ts.hour, ts.minute / 60.0 * 100.,
                                        accum))
    return bp


def myjob(row):
    """ Thread job, yo """
    [xidx, yidx] = row
    lon = WEST + xidx * 0.01
    lat = SOUTH + yidx * 0.01
    fn = get_cli_fname(lon, lat, SCENARIO)
    if not os.path.isfile(fn):
        return False

    # Okay we have work to do
    data = open(fn, 'r').read()
    pos = data.find(VALID.strftime("%-d\t%-m\t%Y"))
    if pos == -1:
        print('Date find failure for %s' % (fn,))
        return False

    pos2 = data[pos:].find(
            (VALID + datetime.timedelta(days=1)).strftime("%-d\t%-m\t%Y"))
    if pos2 == -1:
        print('Date2 find failure for %s' % (fn,))
        return False

    bpdata = compute_breakpoint(PRECIP[yidx, xidx, :])
    if bpdata is None:
        bpdata = []

    thisday = ("%s\t%s\t%s\t%s\t%3.1f\t%3.1f\t%4.0f\t%4.1f\t%s\t%4.1f\n%s%s"
               ) % (VALID.day, VALID.month, VALID.year, len(bpdata),
                    HIGH_TEMP[yidx, xidx], LOW_TEMP[yidx, xidx],
                    SOLAR[yidx, xidx],
                    WIND[yidx, xidx], 0, DEWPOINT[yidx, xidx],
                    "\n".join(bpdata),
                    "\n" if len(bpdata) > 0 else "")

    fp = open(fn, 'w')
    fp.write(data[:pos] + thisday + data[(pos+pos2):])
    fp.close()
    return True


def write_grid(grid, fnadd=''):
    """Save off the daily precip totals for usage later in computing huc_12"""
    printt("write_grid() called...")
    if fnadd != '' and not sys.stdout.isatty():
        printt("not writting extra grid to disk")
        return
    basedir = "/mnt/idep2/data/dailyprecip/%s" % (VALID.year, )
    if not os.path.isdir(basedir):
        os.makedirs(basedir)
    np.save("%s/%s%s.npy" % (basedir, VALID.strftime("%Y%m%d"), fnadd), grid)
    printt("write_grid() finished...")


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

    # 1. Max Temp C
    # 2. Min Temp C
    # 3. Radiation l/d
    # 4. wind mps
    # 6. Mean dewpoint C
    load_iemre()
    # 5. wind direction (always zero)
    # 7. breakpoint precip mm
    precip_workflow()

    printt("building queue")
    queue = []
    for yidx in range(YS):
        for xidx in range(XS):
            queue.append([xidx, yidx])

    printt("starting pool")
    pool = Pool()  # defaults to cpu-count
    sz = len(queue)
    sts = datetime.datetime.now()
    success = 0
    lsuccess = 0
    for i, res in enumerate(pool.imap_unordered(myjob, queue), 1):
        if res:
            success += 1
        if success > 0 and success % 20000 == 0 and lsuccess != success:
            delta = datetime.datetime.now() - sts
            secs = delta.microseconds / 1000000. + delta.seconds
            rate = success / secs
            remaining = ((sz - i) / rate) / 3600.
            printt(('%5.2fh Processed %6s/%6s/%6s [%.2f /sec] '
                    'remaining: %5.2fh') % (secs / 3600., success, i, sz, rate,
                                            remaining))
            lsuccess = success
    del pool
    printt('daily_clifile_editor edited %s files...' % (success,))


if __name__ == '__main__':
    # This is important to keep valid in global scope
    VALID = datetime.date.today() - datetime.timedelta(days=1)
    if len(sys.argv) == 5:
        VALID = datetime.date(int(sys.argv[2]), int(sys.argv[3]),
                              int(sys.argv[4]))

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
        print(("Processed 1 file in %.5f secs, %.0f files per sec"
               ) % (delta, 1.0 / delta))
        self.assertTrue(1 == 0)

    def test_bp(self):
        """ issue #6 invalid time """
        data = np.zeros([30*24])
        data[0] = 3.2
        bp = compute_breakpoint(data)
        self.assertEqual(bp[0], "00.00    0.00")
        self.assertEqual(bp[1], "00.03    3.20")
        data[0] = 0
        data[24*30 - 1] = 9.99
        bp = compute_breakpoint(data)
        self.assertEqual(bp[0], "23.96    0.00")
        self.assertEqual(bp[1], "23.98    9.99")

        data[24*30 - 1] = 10.99
        bp = compute_breakpoint(data)
        self.assertEqual(bp[0], "23.96    0.00")
        self.assertEqual(bp[1], "23.98   10.99")

        # Do some random futzing
        for _ in range(1000):
            data = np.random.randint(20, size=(30*24,))
            bp = compute_breakpoint(data)
            lastts = -1
            lastaccum = -1
            for b in bp:
                tokens = b.split()
                if float(tokens[0]) <= lastts or float(tokens[1]) <= lastaccum:
                    print(data)
                    print(bp)
                    self.assertTrue(1 == 0)
                lastts = float(tokens[0])
                lastaccum = float(tokens[1])
                self.assertTrue(True)
