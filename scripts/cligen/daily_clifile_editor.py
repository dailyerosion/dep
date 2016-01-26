"""
  This is it, we shall create our gridded weather analysis and edit the
  climate files!

  development laptop has data for 9 Sep 2014

"""
import numpy as np
import datetime
import pytz
import pygrib
import sys
import os
import netCDF4
import osgeo.gdal as gdal
from pyiem import iemre
from scipy.interpolate import NearestNDInterpolator
from pyiem.datatypes import temperature
from multiprocessing import Pool
import unittest

SCENARIO = sys.argv[1]
SOUTH = 36.9
NORTH = 44.9
EAST = -90.0
WEST = -99.2
YS = int((NORTH - SOUTH) * 100.)
XS = int((EAST - WEST) * 100.)
high_temp = np.zeros((YS, XS+1))
low_temp = np.zeros((YS, XS+1))
dewpoint = np.zeros((YS, XS+1))
wind = np.zeros((YS, XS+1))
solar = np.zeros((YS, XS+1))
precip = np.zeros((30*24, YS, XS+1))
stage4 = np.zeros((YS, XS+1))

# used for breakpoint logic
ZEROHOUR = datetime.datetime(2000, 1, 1, 0, 0)


def get_xy_from_lonlat(lon, lat):
    """Get the grid position"""
    x = int((lon - WEST) * 100.)
    y = int((lat - SOUTH) * 100.)
    return [x, y]


def load_iemre(valid):
    """Use IEM Reanalysis RSDS gridded solar radiation"""
    xaxis = np.arange(WEST, EAST, 0.01)
    yaxis = np.arange(SOUTH, NORTH, 0.01)
    xi, yi = np.meshgrid(xaxis, yaxis)

    fn = "/mesonet/data/iemre/%s_mw_daily.nc" % (valid.year,)
    if not os.path.isfile(fn):
        print("Missing %s for load_solar, aborting" % (fn,))
        sys.exit()
    nc = netCDF4.Dataset(fn, 'r')
    offset = iemre.daily_offset(valid)
    lats = nc.variables['lat'][:]
    lons = nc.variables['lon'][:]
    lons, lats = np.meshgrid(lons, lats)

    # Storage is W m-2, we want langleys per day
    data = nc.variables['rsds'][offset, :, :] * 86400. / 1000000. * 23.9
    # Default to a value of 300 when this data is missing, for some reason
    nn = NearestNDInterpolator((np.ravel(lons), np.ravel(lats)),
                               np.ravel(np.where(data > 2000., 300, data)))
    solar[:] = nn(xi, yi)

    data = temperature(nc.variables['high_tmpk'][offset, :, :], 'K').value('C')
    nn = NearestNDInterpolator((np.ravel(lons), np.ravel(lats)),
                               np.ravel(data))
    high_temp[:] = nn(xi, yi)

    data = temperature(nc.variables['low_tmpk'][offset, :, :], 'K').value('C')
    nn = NearestNDInterpolator((np.ravel(lons), np.ravel(lats)),
                               np.ravel(data))
    low_temp[:] = nn(xi, yi)

    data = temperature(nc.variables['avg_dwpk'][offset, :, :], 'K').value('C')
    nn = NearestNDInterpolator((np.ravel(lons), np.ravel(lats)),
                               np.ravel(data))
    dewpoint[:] = nn(xi, yi)

    data = nc.variables['wind_speed'][offset, :, :]
    nn = NearestNDInterpolator((np.ravel(lons), np.ravel(lats)),
                               np.ravel(data))
    wind[:] = nn(xi, yi)

    nc.close()


def load_stage4(valid):
    """ It sucks, but we need to load the stage IV data to give us something
    to benchmark the MRMS data against, to account for two things:
    1) Wind Farms
    2) Over-estimates
    """
    midnight = datetime.datetime(valid.year, valid.month, valid.day, 12, 0)
    midnight = midnight.replace(tzinfo=pytz.timezone("UTC"))
    midnight = midnight.astimezone(pytz.timezone("America/Chicago"))
    midnight = midnight.replace(hour=1, minute=0, second=0)
    # clever hack for CST/CDT
    tomorrow = midnight + datetime.timedelta(hours=36)
    tomorrow = tomorrow.replace(hour=0)

    lats = None
    lons = None
    totals = None
    now = midnight
    while now <= tomorrow:
        utc = now.astimezone(pytz.timezone("UTC"))
        gribfn = utc.strftime(("/mesonet/ARCHIVE/data/%Y/%m/%d/stage4/"
                               "ST4.%Y%m%d%H.01h.grib"))
        if not os.path.isfile(gribfn):
            print("%s is missing" % (gribfn,))
            now += datetime.timedelta(hours=1)
            continue

        grbs = pygrib.open(gribfn)
        grb = grbs[1]
        if totals is None:
            lats, lons = grb.latlons()
            totals = np.zeros(np.shape(lats))
        # Don't take any values over 10 inches, this is bad data
        totals += np.where(grb['values'] < 250, grb['values'], 0)
        now += datetime.timedelta(hours=1)

    if totals is None:
        print('No StageIV data found, aborting...')
        sys.exit()
    # set a small non-zero number to keep things non-zero
    totals = np.where(totals > 0.001, totals, 0.001)

    xaxis = np.arange(WEST, EAST, 0.01)
    yaxis = np.arange(SOUTH, NORTH, 0.01)
    xi, yi = np.meshgrid(xaxis, yaxis)
    nn = NearestNDInterpolator((lons.flatten(), lats.flatten()),
                               totals.flatten())
    stage4[:] = nn(xi, yi)
    # print np.max(stage4)
    # import matplotlib.pyplot as plt
    # (fig, ax) = plt.subplots(2, 1)
    # im = ax[0].imshow(stage4)
    # fig.colorbar(im)
    # im = ax[1].imshow(totals)
    # fig.colorbar(im)
    # fig.savefig('test.png')


def qc_precip():
    """ Do the quality control on the precip product """
    mrms_total = np.sum(precip, 0)
    # So what is our logic here.  We should care about aggregious differences
    # Lets make MRMS be within 33% of stage IV
    ratio = mrms_total / stage4
    print_threshold = 0
    # (myx, myy) = get_xy_from_lonlat(-91.44, 41.28)
    # print myx, myy
    for y in range(YS):
        for x in range(XS+1):
            # if x == myx and y == myy:
            #    print precip[:, y, x]
            if ratio[y, x] < 1.3:
                continue
            # Don't fuss over small differences, if mrms_total is less
            # than 10 mm
            if mrms_total[y, x] < 10:
                continue
            # Pull the functional form down to stage4 total
            precip[:, y, x] = precip[:, y, x] / ratio[y, x]
            # if x == myx and y == myy:
            #    print precip[:, y, x]

            # limit the amount of printout we do, not really useful anyway
            if mrms_total[y, x] > print_threshold:
                print(('QC y: %3i x: %3i stageIV: %5.1f MRMS: %5.1f New: %5.1f'
                       ) % (y, x, stage4[y, x], mrms_total[y, x],
                            np.sum(precip[:, y, x])))
                print_threshold = mrms_total[y, x]

    # basedir = "/mnt/idep2/data/dailyprecip/2015"
    # np.save(valid.strftime(basedir+"/%Y%m%d_ratio.npy"), ratio)
    # np.save(valid.strftime(basedir+"/%Y%m%d_mrms_total.npy"), mrms_total)


def load_precip_legacy(valid):
    """ Compute a Legacy Precip product for dates prior to 1 Jan 2014"""
    ts = 12 * 24  # 5 minute

    midnight = datetime.datetime(valid.year, valid.month, valid.day, 12, 0)
    midnight = midnight.replace(tzinfo=pytz.timezone("UTC"))
    midnight = midnight.astimezone(pytz.timezone("America/Chicago"))
    midnight = midnight.replace(hour=0, minute=0, second=0)
    # clever hack for CST/CDT
    tomorrow = midnight + datetime.timedelta(hours=36)
    tomorrow = tomorrow.replace(hour=0)

    top = int((50. - NORTH) * 100.)
    bottom = int((50. - SOUTH) * 100.)

    right = int((EAST - -126.) * 100.)
    left = int((WEST - -126.) * 100.)

    now = midnight
    m5 = np.zeros((ts, YS, XS+1))
    tidx = 0
    # Load up the n0r data, every 15 minutes
    while now < tomorrow:
        utc = now.astimezone(pytz.timezone("UTC"))
        fn = utc.strftime(("/mesonet/ARCHIVE/data/%Y/%m/%d/GIS/uscomp/"
                           "n0r_%Y%m%d%H%M.png"))
        if os.path.isfile(fn):
            if tidx >= ts:
                # Abort as we are in CST->CDT
                break
            img = gdal.Open(fn, 0)
            imgdata = img.ReadAsArray()
            # Convert the image data to dbz
            dbz = (np.flipud(imgdata[top:bottom, left:right]) - 7.) * 5
            m5[tidx, :, :] = np.where(dbz < 255,
                                      ((10. ** (dbz/10.)) / 200.) ** 0.625,
                                      0)
        else:
            print('daily_clifile_editor missing: %s' % (fn,))

        now += datetime.timedelta(minutes=5)
        tidx += 1

#    for y in range(YS):
#        for x in range(XS + 1):
    for y in [649, ]:
        for x in [688, ]:
            s4total = stage4[y, x]
            # skip 1 mm precipitation
            if s4total < 1:
                continue
            five = m5[:, y, x]
            # TODO unsure of this... Smear the precip out over the first our
            if np.sum(five) < 10:
                precip[0:30, y, x] = s4total / 30.
                continue
            weights = five / np.sum(five) / 2.5
            for t in range(0, 60 * 24, 2):
                precip[int(t/2), y, x] = weights[int(t/5)] * s4total


def load_precip(valid):
    """ Load the 5 minute precipitation data into our ginormus grid """
    ts = 30 * 24  # 2 minute

    midnight = datetime.datetime(valid.year, valid.month, valid.day, 12, 0)
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
    a2m_divisor = 10. if (valid < datetime.date(2015, 1, 1)) else 50.

    now = midnight
    while now < tomorrow:
        utc = now.astimezone(pytz.timezone("UTC"))
        fn = utc.strftime(("/mesonet/ARCHIVE/data/%Y/%m/%d/GIS/mrms/"
                           "a2m_%Y%m%d%H%M.png"))
        if os.path.isfile(fn):
            tidx = int((now - midnight).seconds / 120.)
            if tidx >= ts:
                # Abort as we are in CST->CDT
                return precip
            img = gdal.Open(fn, 0)
            # --------------------------------------------------
            # OK, once and for all, 0,0 is the upper left!
            # units are 0.1mm
            imgdata = img.ReadAsArray()
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
            precip[tidx, :, :] = np.where(data < 255, data / a2m_divisor, 0)

        else:
            print 'daily_clifile_editor missing: %s' % (fn,)

        now += datetime.timedelta(minutes=2)


def compute_breakpoint(ar):
    """ Compute the breakpoint data based on this array of data!

    Values are in 0.1mm increments!

    """
    total = np.sum(ar)
    # Any total less than (1mm) is not of concern, might as well be zero
    if total < 0.1:
        return []
    bp = ["00.00    0.00", ]
    # in mm
    accum = 0
    lastaccum = 0
    lasti = 0
    for i, intensity in enumerate(ar):
        if intensity == 0:
            continue
        accum += intensity
        lasti = i
        if i == 0:  # Can't have immediate accumulation
            continue
        if (accum - lastaccum) > 10:  # record every 10mm
            lastaccum = accum
            # 23.90       0.750
            ts = ZEROHOUR + datetime.timedelta(minutes=(i*2))
            bp.append("%02i.%02i  %6.2f" % (ts.hour, ts.minute / 60.0 * 100.,
                                            accum))
    if accum != lastaccum:
        ts = ZEROHOUR + datetime.timedelta(minutes=(max(lasti, 1)*2))
        bp.append("%02i.%02i  %6.2f" % (ts.hour, ts.minute / 60.0 * 100.,
                                        accum))
    return bp


def myjob(row):
    """ Thread job, yo """
    [x, y] = row
    lon = WEST + x * 0.01
    lat = SOUTH + y * 0.01
    fn = "/i/%s/cli/%03.0fx%03.0f/%06.2fx%06.2f.cli" % (SCENARIO,
                                                        0 - lon,
                                                        lat,
                                                        0 - lon,
                                                        lat)
    if not os.path.isfile(fn):
        return False

    # Okay we have work to do
    data = open(fn, 'r').read()
    pos = data.find(valid.strftime("%-d\t%-m\t%Y"))
    if pos == -1:
        print 'Date find failure for %s' % (fn,)
        return False

    pos2 = data[pos:].find(
            (valid + datetime.timedelta(days=1)).strftime("%-d\t%-m\t%Y"))
    if pos2 == -1:
        print 'Date2 find failure for %s' % (fn,)
        return False

    bpdata = compute_breakpoint(precip[:, y, x])

    thisday = ("%s\t%s\t%s\t%s\t%3.1f\t%3.1f\t%4.0f\t%4.1f\t%s\t%4.1f\n%s%s"
               ) % (valid.day, valid.month, valid.year, len(bpdata),
                    high_temp[y, x], low_temp[y, x], solar[y, x],
                    wind[y, x], 0, dewpoint[y, x], "\n".join(bpdata),
                    "\n" if len(bpdata) > 0 else "")

    o = open(fn, 'w')
    o.write(data[:pos] + thisday + data[(pos+pos2):])
    o.close()
    return True


def save_daily_precip():
    """Save off the daily precip totals for usage later in computing huc_12"""
    data = np.sum(precip, 0)
    basedir = "/mnt/idep2/data/dailyprecip/"+str(valid.year)
    if not os.path.isdir(basedir):
        os.makedirs(basedir)
    np.save(valid.strftime(basedir+"/%Y%m%d.npy"), data)
    # save Stage IV as well, for later hand wringing
    # np.save(valid.strftime(basedir+"/%Y%m%d_stageIV.npy"), stage4)


def workflow():
    """ The workflow to get the weather data variables we want! """

    # 1. Max Temp C
    # 2. Min Temp C
    # 3. Radiation l/d
    # 4. wind mps
    # 6. Mean dewpoint C
    load_iemre(valid)
    # 5. wind direction (always zero)
    # 7. breakpoint precip mm
    load_stage4(valid)
    if valid.year >= 2014:
        load_precip(valid)
    else:
        load_precip_legacy(valid)
    qc_precip()
    save_daily_precip()

    QUEUE = []
    for y in range(YS):
        for x in range(XS):
            QUEUE.append([x, y])

    pool = Pool()  # defaults to cpu-count
    sz = len(QUEUE)
    sts = datetime.datetime.now()
    success = 0
    lsuccess = 0
    for i, res in enumerate(pool.imap_unordered(myjob, QUEUE), 1):
        if res:
            success += 1
        if success > 0 and success % 20000 == 0 and lsuccess != success:
            delta = datetime.datetime.now() - sts
            secs = delta.microseconds / 1000000. + delta.seconds
            rate = success / secs
            remaining = ((sz - i) / rate) / 3600.
            print ('%5.2fh Processed %6s/%6s/%6s [%.2f /sec] '
                   'remaining: %5.2fh') % (secs / 3600., success, i, sz, rate,
                                           remaining)
            lsuccess = success
    print('daily_clifile_editor edited %s files...' % (success,))


if __name__ == '__main__':
    # This is important to keep valid in global scope
    valid = datetime.date.today() - datetime.timedelta(days=1)
    if len(sys.argv) == 5:
        valid = datetime.date(int(sys.argv[2]), int(sys.argv[3]),
                              int(sys.argv[4]))

    workflow()


class test(unittest.TestCase):

    def test_speed(self):
        """Test the speed of the processing"""
        global SCENARIO, valid
        SCENARIO = 0
        valid = datetime.date(2014, 10, 10)
        sts = datetime.datetime.now()
        myjob(get_xy_from_lonlat(-91.44, 41.28))
        ets = datetime.datetime.now()
        delta = (ets - sts).total_seconds()
        print(("Processed 1 file in %.5f secs, %.0f files per sec"
               ) % (delta, 1.0 / delta))
        self.assertEqual(1, 0)

    def test_bp(self):
        """ issue #6 invalid time """
        data = np.zeros([30*24])
        data[0] = 3.2
        bp = compute_breakpoint(data)
        self.assertEqual(bp[1], "00.03    3.20")
