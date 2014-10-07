"""
  This is it, we shall create our gridded weather analysis and edit the
  climate files!

  development laptop has data for 9 Sep 2014

"""
import numpy as np
import datetime
import pytz
import sys
import os
import osgeo.gdal as gdal
import psycopg2
from pyiem.network import Table as NetworkTable
from scipy.interpolate import NearestNDInterpolator
from pyiem.datatypes import temperature, speed
from multiprocessing import Pool

SCENARIO = sys.argv[1]
SOUTH = 40.28
NORTH = 43.69
EAST = -91.01
WEST = -96.73
YS = int((NORTH - SOUTH) * 100.)
XS = int((EAST - WEST) * 100.)
high_temp = np.zeros((YS+1, XS+1))
low_temp = np.zeros((YS+1, XS+1))
dewpoint = np.zeros((YS+1, XS+1))
wind = np.zeros((YS+1, XS+1))
solar = np.zeros((YS+1, XS+1))
precip = np.zeros((30*24, YS, XS), np.uint8)

# used for breakpoint logic
ZEROHOUR = datetime.datetime(2000, 1, 1, 0, 0)

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


def load_solar( valid ):
    """ Grid out the solar radiation data! """
    xaxis = np.arange(WEST, EAST, 0.01)
    yaxis = np.arange(SOUTH, NORTH, 0.01)
    xi, yi = np.meshgrid(xaxis, yaxis)
    
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
    nn = NearestNDInterpolator((np.array(lons), np.array(lats)), 
                               np.array(vals))
    solar[:] = nn(xi, yi)

def load_precip( valid ):
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
    bottom = int((55. - SOUTH) * 100. )-1

    right =  int((EAST - -130.) * 100.)-1
    left = int((WEST - -130.) * 100.)
    
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
            data = np.flipud( imgdata[top:bottom,left:right] )
            #print np.shape(imgdata), bottom, top, left, right
            #print now, imgdata[sampley, samplex]
            #if imgdata[sampley, samplex] > 0:
            #    import matplotlib.pyplot as plt
            #    (fig, ax) = plt.subplots(2,1)
            #    ax[0].imshow(imgdata[0:3000, :])
            #    ax[1].imshow(data)
            #    fig.savefig('test.png')
            #    sys.exit()
            # Turn 255 (missing) into zeros
            precip[tidx,:,:] = np.where( data < 255, data, 0)
            
        else:
            print 'daily_clifile_editor missing: %s' % (fn,)
            
        
        now += datetime.timedelta(minutes=2)
    return precip

def compute_breakpoint( ar ):
    """ Compute the breakpoint data based on this array of data! 
    
    Values are in 0.1mm increments!
    
    """
    total = np.sum( ar )
    # Any total less than 10 (1mm) is not of concern, might as well be zero
    if total < 10:
        return []
    bp = None
    # in mm
    accum = 0
    lastaccum = 0
    lasti = 0
    for i, intensity in enumerate( ar ):
        if intensity == 0:
            continue
        if bp is None:
            bp = ["00.00    0.00",]
        accum += (float(intensity) / 10.)
        lasti = i
        if i == 0: # Can't have immediate accumulation
            continue
        if (accum - lastaccum) > 10: # record every 10mm
            lastaccum = accum
            # 23.90       0.750
            ts = ZEROHOUR + datetime.timedelta(minutes=(i*2))
            bp.append("%02i.%02i  %6.2f" % (ts.hour, ts.minute / 60.0 * 100.,
                                          accum))
    if accum != lastaccum:
        ts = ZEROHOUR + datetime.timedelta(minutes=(lasti*2))
        bp.append("%02i.%02i  %6.2f" % (ts.hour, ts.minute / 60.0 * 100.,
                                      accum))
    return bp

def myjob( row ):
    """ Thread job, yo """
    [x, y] = row 
    lon = WEST + x * 0.01
    lat = SOUTH + y * 0.01
    fn =  "/i/%s/cli/%03.0fx%03.0f/%06.2fx%06.2f.cli" % (SCENARIO,
                                                0 - lon,
                                                lat,
                                                0 - lon,
                                                lat)
    if not os.path.isfile(fn):
        return
    
    
    # Okay we have work to do
    data = open(fn, 'r').read()
    pos = data.find( valid.strftime("%-d\t%-m\t%Y") )
    if pos == -1:
        print 'Date find failure for %s' % (fn,)
        return
    
    pos2 = data.find( 
            (valid + datetime.timedelta(days=1)).strftime("%-d\t%-m\t%Y") )
    if pos2 == -1:
        print 'Date2 find failure for %s' % (fn,)
        return
    
    bpdata = compute_breakpoint( precip[:,y,x] )
    
    thisday = "%s\t%s\t%s\t%s\t%3.1f\t%3.1f\t%4.0f\t%4.1f\t%s\t%4.1f\n%s%s" % (                                                                     
        valid.day, valid.month, valid.year, len(bpdata), high_temp[y,x], 
        low_temp[y,x], solar[y,x], wind[y,x], 0, dewpoint[y,x], 
        "\n".join(bpdata), "\n" if len(bpdata) > 0 else "" )

    o = open(fn, 'w')
    o.write( data[:pos] + thisday + data[pos2:])
    o.close()

def workflow():
    """ The workflow to get the weather data variables we want! """
    
    # 1. Max Temp C
    # 2. Min Temp C
    # 4. wind mps
    # 6. Mean dewpoint C
    load_asos( valid )
    # 3. Radiation l/d
    load_solar( valid )
    # 5. wind direction (always zero)
    # 7. breakpoint precip mm
    load_precip( valid )



    QUEUE = []
    for y in range(YS):
        for x in range(XS):
            QUEUE.append( [x, y] )

    pool = Pool() # defaults to cpu-count
    sz = len(QUEUE)
    sts = datetime.datetime.now()
    for i,_ in enumerate(pool.imap_unordered(myjob, QUEUE),1):
        if i > 0 and i % 10000 == 0:
            delta = datetime.datetime.now() - sts
            secs = delta.microseconds / 1000000. + delta.seconds
            rate = i / secs
            remaining = ((sz - i) / rate) / 3600.
            print ('%5.2fh Processed %6s/%6s [%.2f runs per sec] '
                   +'remaining: %5.2fh') % (secs /3600., i, sz, rate,
                                            remaining )


    
if __name__ == '__main__':
    # This is important to keep valid in global scope
    valid = datetime.date.today() - datetime.timedelta(days=1)
    if len(sys.argv) == 5:
        valid = datetime.date( int(sys.argv[2]), int(sys.argv[3]),
                               int(sys.argv[4]))

    workflow()