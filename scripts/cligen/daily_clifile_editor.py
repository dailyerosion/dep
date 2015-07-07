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
import osgeo.gdal as gdal
import psycopg2
from pyiem.network import Table as NetworkTable
from scipy.interpolate import NearestNDInterpolator
from pyiem.datatypes import temperature, speed
from multiprocessing import Pool
import unittest

SCENARIO = sys.argv[1]
SOUTH = 36.9
NORTH = 44.9
EAST = -90.0
WEST = -99.2
YS = int((NORTH - SOUTH) * 100.)
XS = int((EAST - WEST) * 100.)
high_temp = np.zeros((YS+1, XS+1))
low_temp = np.zeros((YS+1, XS+1))
dewpoint = np.zeros((YS+1, XS+1))
wind = np.zeros((YS+1, XS+1))
solar = np.zeros((YS+1, XS+1))
precip = np.zeros((30*24, YS+1, XS+1))
stage4 = np.zeros((YS+1, XS+1))

# used for breakpoint logic
ZEROHOUR = datetime.datetime(2000, 1, 1, 0, 0)


def get_xy_from_lonlat(lon, lat):
    """Get the grid position"""
    x = int((lon - WEST) * 100.)
    y = int((lat - SOUTH) * 100.)
    return [x, y]


def load_asos(valid):
    """ Load temps and family """
    xaxis = np.arange(WEST, EAST, 0.01)
    yaxis = np.arange(SOUTH, NORTH, 0.01)
    xi, yi = np.meshgrid(xaxis, yaxis)

    nt = NetworkTable(["IA_ASOS", "AWOS"])
    pgconn = psycopg2.connect(database='asos', host='iemdb', user='nobody')
    cursor = pgconn.cursor()

    cursor.execute("""select station, 
    avg(sknt), avg(dwpf), max(tmpf), min(tmpf) from alldata 
    where valid BETWEEN '%s 00:00' and '%s 00:00' 
    and station in %s GROUP by station
              """ % (valid.strftime("%Y-%m-%d"),
                (valid + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
                str(tuple(nt.sts.keys()))))
    lons = []
    lats = []
    hic = []
    loc = []
    dwpc = []
    smps = []
    for row in cursor:
        if (row[1] is None or row[2] is None or 
            row[3] is None or row[4] is None):
            continue
        lons.append(nt.sts[row[0]]['lon'])
        lats.append(nt.sts[row[0]]['lat'])
        hic.append(temperature(row[3], 'F').value('C'))
        loc.append(temperature(row[4], 'F').value('C'))
        dwpc.append(temperature(row[2], 'F').value('C'))
        smps.append(speed(row[1], 'KT').value('MPS'))


    nn = NearestNDInterpolator((np.array(lons), np.array(lats)), 
                               np.array(hic))
    high_temp[:] = nn(xi, yi)

    nn = NearestNDInterpolator((np.array(lons), np.array(lats)), 
                               np.array(loc))
    low_temp[:] = nn(xi, yi)

    nn = NearestNDInterpolator((np.array(lons), np.array(lats)), 
                               np.array(dwpc))
    dewpoint[:] = nn(xi, yi)

    nn = NearestNDInterpolator((np.array(lons), np.array(lats)), 
                               np.array(smps))
    wind[:] = nn(xi, yi)

def get_isusm_solar(valid):
    """ Retrieve the ISUSM solar radiation data """
    nt = NetworkTable("ISUSM")
    pgconn = psycopg2.connect(database='isuag', host='iemdb', user='nobody')
    cursor = pgconn.cursor()
    
    cursor.execute("""SELECT station, slrmj_tot from sm_daily 
              WHERE valid = %s and slrmj_tot is not null
              """, (valid,))
    lons = []
    lats = []
    vals = []
    for row in cursor:
        # convert mj to langleys
        rad = row[1] * 23.9
        # Crude bounds
        if rad < 0.01 or rad > 800:
            continue
        lons.append( nt.sts[row[0]]['lon'] )
        lats.append( nt.sts[row[0]]['lat'] )
        vals.append( rad )

    return lons, lats, vals

def load_solar( valid ):
    """ Grid out the solar radiation data! """
    xaxis = np.arange(WEST, EAST, 0.01)
    yaxis = np.arange(SOUTH, NORTH, 0.01)
    xi, yi = np.meshgrid(xaxis, yaxis)
    
    lons, lats, vals = get_isusm_solar(valid)
    if len(lons) < 3:
        print('Warning: load_solar() found only %s obs!' % (len(lons),))
        lons, lats, vals = get_isusm_solar(valid - datetime.timedelta(days=1))
        if len(lons) < 3:
            print('Fatal: load_solar() found %s obs for yesterday!' % (
                                                            len(lons),))
            sys.exit()
    
    nn = NearestNDInterpolator((np.array(lons), np.array(lats)), 
                               np.array(vals))
    solar[:] = nn(xi, yi)

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
                               +"ST4.%Y%m%d%H.01h.grib"))
        if not os.path.isfile(gribfn):
            print("%s is missing" % (gribfn,))
            now += datetime.timedelta(hours=1)
            continue
        
        grbs = pygrib.open(gribfn)
        grb = grbs[1]
        if totals is None:
            lats, lons = grb.latlons()
            totals = grb['values'] + 0.001  # Always non-zero this way
        else:
            totals += grb['values']
        
        now += datetime.timedelta(hours=1)

    if totals is None:
        print('No StageIV data found, aborting...')
        sys.exit()
    
    xaxis = np.arange(WEST, EAST, 0.01)
    yaxis = np.arange(SOUTH, NORTH, 0.01)
    xi, yi = np.meshgrid(xaxis, yaxis)
    nn = NearestNDInterpolator((lons.flatten(), lats.flatten()), 
                               totals.flatten())
    stage4[:] = nn(xi, yi)


def qc_precip():
    """ Do the quality control on the precip product """
    mrms_total = np.sum(precip, 0)
    # So what is our logic here.  We should care about aggregious differences
    # Lets make MRMS be within 33% of stage IV
    ratio = mrms_total / stage4
    print_threshold = 0
    (myx, myy) = get_xy_from_lonlat(-91.44, 41.28)
    print myx, myy
    for y in range(YS+1):
        for x in range(XS+1):
            if x == myx and y == myy:
                print precip[:, y, x]
            if ratio[y, x] < 1.3:
                continue
            # Don't fuss over small differences, if mrms_total is less
            # than 10 mm
            if mrms_total[y, x] < 10:
                continue
            # Pull the functional form down to stage4 total
            precip[:, y, x] = precip[:, y, x] / ratio[y, x]
            if x == myx and y == myy:
                print precip[:, y, x]

            # limit the amount of printout we do, not really useful anyway
            if mrms_total[y, x] > print_threshold:
                print(('QC y: %3i x: %3i stageIV: %5.1f MRMS: %5.1f New: %5.1f'
                       ) % (y, x, stage4[y, x], mrms_total[y, x],
                            np.sum(precip[:, y, x])))
                print_threshold = mrms_total[y, x]


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
    bottom = int((55. - SOUTH) * 100. )

    right =  int((EAST - -130.) * 100.)
    left = int((WEST - -130.) * 100.)
    (myx, myy) = get_xy_from_lonlat(-91.44, 41.28)
    #samplex = int((-96.37 - -130.)*100.)
    #sampley = int((55. - 42.71)*100)

    now = midnight
    while now < tomorrow:
        utc = now.astimezone(pytz.timezone("UTC"))
        fn = utc.strftime(("/mesonet/ARCHIVE/data/%Y/%m/%d/GIS/mrms/"
                           +"a2m_%Y%m%d%H%M.png"))
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
            print now, data[myy, myx]
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
            precip[tidx, :, :] = np.where(data < 255, data / 10., 0)

        else:
            print 'daily_clifile_editor missing: %s' % (fn,)


        now += datetime.timedelta(minutes=2)
    return precip


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
        return

    # Okay we have work to do
    data = open(fn, 'r').read()
    pos = data.find(valid.strftime("%-d\t%-m\t%Y"))
    if pos == -1:
        print 'Date find failure for %s' % (fn,)
        return

    pos2 = data[pos:].find(
            (valid + datetime.timedelta(days=1)).strftime("%-d\t%-m\t%Y"))
    if pos2 == -1:
        print 'Date2 find failure for %s' % (fn,)
        return

    bpdata = compute_breakpoint(precip[:, y, x])

    thisday = ("%s\t%s\t%s\t%s\t%3.1f\t%3.1f\t%4.0f\t%4.1f\t%s\t%4.1f\n%s%s"
               ) % (valid.day, valid.month, valid.year, len(bpdata),
                    high_temp[y, x], low_temp[y, x], solar[y, x],
                    wind[y, x], 0, dewpoint[y, x], "\n".join(bpdata),
                    "\n" if len(bpdata) > 0 else "")

    o = open(fn, 'w')
    o.write(data[:pos] + thisday + data[(pos+pos2):])
    o.close()


def save_daily_precip():
    """Save off the daily precip totals for usage later in computing huc_12"""
    data = np.sum(precip, 0)
    basedir = "/mnt/idep2/data/dailyprecip/"+str(valid.year)
    if not os.path.isdir(basedir):
        os.makedirs(basedir)
    np.save(valid.strftime(basedir+"/%Y%m%d.npy"), data)


def workflow():
    """ The workflow to get the weather data variables we want! """

    # 1. Max Temp C
    # 2. Min Temp C
    # 4. wind mps
    # 6. Mean dewpoint C
    load_asos(valid)
    # 3. Radiation l/d
    load_solar(valid)
    # 5. wind direction (always zero)
    # 7. breakpoint precip mm
    load_stage4(valid)
    load_precip(valid)
    #qc_precip()
    save_daily_precip()
    return
    
    QUEUE = []
    for y in range(YS):
        for x in range(XS):
            QUEUE.append([x, y])

    pool = Pool()  # defaults to cpu-count
    sz = len(QUEUE)
    sts = datetime.datetime.now()
    for i, _ in enumerate(pool.imap_unordered(myjob, QUEUE), 1):
        if i > 0 and i % 10000 == 0:
            delta = datetime.datetime.now() - sts
            secs = delta.microseconds / 1000000. + delta.seconds
            rate = i / secs
            remaining = ((sz - i) / rate) / 3600.
            print ('%5.2fh Processed %6s/%6s [%.2f runs per sec] '
                   'remaining: %5.2fh') % (secs / 3600., i, sz, rate,
                                           remaining)


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
