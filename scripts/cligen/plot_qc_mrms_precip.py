"""Plot what was saved from daily_clifile_editor processing"""
from pyiem.plot import MapPlot
from pyiem.iemre import daily_offset
import sys
import netCDF4
import datetime
import numpy as np
import os
import matplotlib.cm as cm
SOUTH = 36.9
NORTH = 44.9
EAST = -90.0
WEST = -99.2
YS = np.arange(SOUTH, NORTH, 0.01)
XS = np.arange(WEST, EAST, 0.01)


def load_precip(date, extra=''):
    """Load up our QC'd daily precip dataset """
    fn = date.strftime("/mnt/idep2/data/dailyprecip/%Y/%Y%m%d"+extra+".npy")
    if not os.path.isfile(fn):
        print("load_precip(%s) failed, no such file %s" % (date, fn))
        return
    return np.load(fn)


def do(valid):
    """Do Something"""
    clevs = np.arange(0, 0.25, 0.05)
    clevs = np.append(clevs, np.arange(0.25, 3., 0.25))
    clevs = np.append(clevs, np.arange(3., 10.0, 1))
    clevs[0] = 0.01

    precip = load_precip(valid)
    stageIV = load_precip(valid, '_stageIV')
    mrms_total = load_precip(valid, '_mrms_total')
    ratio = load_precip(valid, '_ratio')

    # Go MRMS
    idx = daily_offset(valid)
    nc = netCDF4.Dataset(("/mesonet/data/iemre/%s_mw_mrms_daily.nc"
                          ) % (valid.year, ),
                         'r')
    xidx = int((WEST - nc.variables['lon'][0]) * 100.)
    yidx = int((SOUTH - nc.variables['lat'][0]) * 100.)
    mrms = nc.variables['p01d'][idx, yidx:(yidx+800), xidx:(xidx+921)]
    nc.close()

    # Print out some debug
    y = int((41.99 - SOUTH) * 100.)
    x = int((-93.6 - WEST) * 100.)
    print "%7s %7s %7s %7s %7s" % ('DEP', 'stageIV', 'MRMS_TOT', 'Ratio',
                                   'MRMS')
    print "%7.3s %7.3s %7.3s %7.3s %7.3s" % (precip[y, x], stageIV[y, x],
                                             mrms_total[y, x], ratio[y, x],
                                             mrms[y, x])

    m = MapPlot(sector='iowa', axisbg='white',
                title=('%s DEP Quality Controlled Precip Totals'
                       ) % (valid.strftime("%-d %b %Y"), ))
    (lons, lats) = np.meshgrid(XS, YS)
    print np.shape(precip), np.shape(lons), np.shape(lats)
    m.pcolormesh(lons, lats, precip / 25.4, clevs,
                 units='inch')
    m.drawcounties()
    m.postprocess(filename='qc.png')
    m.close()

    m = MapPlot(sector='iowa', axisbg='white',
                title=('%s Stage IV Precip Totals'
                       ) % (valid.strftime("%-d %b %Y"), ))
    print np.shape(stageIV), np.shape(lons), np.shape(lats)
    m.pcolormesh(lons, lats, stageIV / 25.4, clevs,
                 units='inch')
    m.drawcounties()
    m.postprocess(filename='stageIV.png')
    m.close()

    m = MapPlot(sector='iowa', axisbg='white',
                title=('%s ORIG MRMS TOTAL Precip Totals'
                       ) % (valid.strftime("%-d %b %Y"), ))
    print np.shape(stageIV), np.shape(lons), np.shape(lats)
    m.pcolormesh(lons, lats, mrms_total / 25.4, clevs,
                 units='inch')
    m.drawcounties()
    m.postprocess(filename='mrms_total.png')
    m.close()

    m = MapPlot(sector='iowa', axisbg='white',
                title=('%s Ratio Totals'
                       ) % (valid.strftime("%-d %b %Y"), ))
    print np.shape(stageIV), np.shape(lons), np.shape(lats)
    m.pcolormesh(lons, lats, ratio, np.arange(0, 3, 0.25),
                 units='inch')
    m.drawcounties()
    m.postprocess(filename='ratio.png')
    m.close()

    m = MapPlot(sector='iowa', axisbg='white',
                title=('%s MRMS Precip Totals'
                       ) % (valid.strftime("%-d %b %Y"), ))
    print np.shape(mrms), np.shape(lons), np.shape(lats)
    m.pcolormesh(lons, lats, mrms / 25.4, clevs,
                 units='inch')
    m.drawcounties()
    m.postprocess(filename='mrms.png')
    m.close()

    m = MapPlot(sector='iowa', axisbg='white',
                title=('%s DEP - MRMS Precip Totals'
                       ) % (valid.strftime("%-d %b %Y"), ))
    clevs = np.arange(-3, 3.1, 0.5)
    m.pcolormesh(lons, lats, (precip - mrms_total) / 25.4, clevs,
                 units='inch', cmap=cm.get_cmap("BrBG"))
    m.drawcounties()
    m.postprocess(filename='diff.png')
    m.close()


def main(argv):
    valid = datetime.date(int(argv[1]), int(argv[2]),
                          int(argv[3]))
    do(valid)

if __name__ == '__main__':
    main(sys.argv)
