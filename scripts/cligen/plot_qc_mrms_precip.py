"""Plot what was saved from daily_clifile_editor processing"""
from pyiem.plot import MapPlot
import sys
import datetime
import numpy as np
import os
SOUTH = 36.9
NORTH = 44.9
EAST = -90.0
WEST = -99.2
YS = np.arange(SOUTH, NORTH, 0.01)
XS = np.arange(WEST, EAST, 0.01)


def load_precip(date):
    """Load up our QC'd daily precip dataset """
    fn = date.strftime("/mnt/idep2/data/dailyprecip/%Y/%Y%m%d.npy")
    if not os.path.isfile(fn):
        print("load_precip(%s) failed, no such file" % (date,))
        return
    return np.load(fn)


def do(valid):
    """Do Something"""
    precip = load_precip(valid)

    m = MapPlot(sector='midwest', axisbg='white')
    (lats, lons) = np.meshgrid(YS, XS)
    print np.shape(precip), np.shape(lons), np.shape(lats)
    m.pcolormesh(lons, lats, np.transpose(precip), np.arange(20))
    m.postprocess(view=True)


def main(argv):
    valid = datetime.date(int(argv[1]), int(argv[2]),
                          int(argv[3]))
    do(valid)

if __name__ == '__main__':
    main(sys.argv)
