"""
  This is it, we shall create our gridded weather analysis and edit the
  climate files!
"""
import numpy as np
import datetime
import pytz 
import sys
import os
import osgeo.gdal as gdal

SOUTH = 40.28
NORTH = 43.69
EAST = -91.01
WEST = -96.73
YS = int((NORTH - SOUTH) * 100.)
XS = int((EAST - WEST) * 100.)

def load_precip( valid ):
    """ Load the 5 minute precipitation data into our ginormus grid """
    ts = 30 * 24  # 2 minute

    precip = np.zeros( (ts, YS, XS ), np.uint8)

    midnight = datetime.datetime(valid.year, valid.month, valid.day, 12, 0)
    midnight = midnight.replace(tzinfo=pytz.timezone("UTC"))
    midnight = midnight.astimezone(pytz.timezone("America/Chicago"))
    midnight = midnight.replace(hour=0, minute=0, second=0)
    # clever hack for CST/CDT
    tomorrow = midnight + datetime.timedelta(hours=36)
    tomorrow = tomorrow.replace(hour=0)

    top = int((55. - NORTH) * 100.)
    left = int((WEST - -130) * 100.)
    bottom = int((55. - SOUTH) * 100. )-1
    right =  int((EAST - -130) * 100.)-1
    

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
            # this is y,x with start in upper left -130 55
            # units are 0.1mm
            imgdata = img.ReadAsArray()
            precip[tidx,:,:] = imgdata[top:bottom,left:right]
            
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
    print ar
    midnight = datetime.datetime(2000,1,1,0,0)
    bp = []
    for i, intensity in enumerate( ar ):
        if ar[i] > 1:
            bp.append("hi")
    return bp

def workflow( valid ):
    """ The workflow to get the weather data variables we want! """
    
    # 1. Max Temp C
    # 2. Min Temp C
    # 3. Radiation l/d
    # 4. wind mps
    # 5. wind direction
    # 6. Mean dewpoint C
    # 7. breakpoint precip mm
    precip = load_precip( valid )
    
    for y in range(YS):
        for x in range(XS):
            breakpoint = compute_breakpoint( precip[:, y, x] )

    
if __name__ == '__main__':
    valid = datetime.date.today() - datetime.timedelta(days=1)
    if len(sys.argv) == 4:
        valid = datetime.date( int(sys.argv[1]), int(sys.argv[2]),
                               int(sys.argv[3]))

    workflow( valid )