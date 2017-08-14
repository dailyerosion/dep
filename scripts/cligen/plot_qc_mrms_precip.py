"""Plot what was saved from daily_clifile_editor processing"""
from __future__ import print_function
import sys
import datetime
import os

from pyiem.plot import MapPlot
from pyiem.iemre import daily_offset
from pyiem.dep import SOUTH, NORTH, EAST, WEST
import netCDF4
import numpy as np
import matplotlib.pyplot as plt
YS = np.arange(SOUTH, NORTH, 0.01)
XS = np.arange(WEST, EAST, 0.01)
SECTOR = 'iowa'


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
    stage4 = load_precip(valid, 'stage4')
    inqcprecip = load_precip(valid, 'inqcprecip')
    outqcprecip = load_precip(valid, 'outqcprecip')
    multiplier = load_precip(valid, 'multiplier')

    yidx = int((43.27 - SOUTH) / 0.01)
    xidx = int((-94.39 - WEST) / 0.01)
    print(("yidx:%s xidx:%s precip:%.2f stage4: %.2f inqc: %.2f outqc: %.2f "
           "mul: %.2f"
           ) % (yidx, xidx, precip[yidx, xidx], stage4[yidx, xidx],
                inqcprecip[yidx, xidx], outqcprecip[yidx, xidx],
                multiplier[yidx, xidx]))

    mp = MapPlot(sector=SECTOR, axisbg='white',
                 title=('%s DEP Quality Controlled Precip Totals'
                        ) % (valid.strftime("%-d %b %Y"), ))
    (lons, lats) = np.meshgrid(XS, YS)
    mp.pcolormesh(lons, lats, precip / 25.4, clevs,
                  units='inch')
    mp.drawcounties()
    mp.postprocess(filename='qc.png')
    mp.close()

    mp = MapPlot(sector=SECTOR, axisbg='white',
                 title=('%s Stage IV Precip Totals'
                        ) % (valid.strftime("%-d %b %Y"), ))
    mp.pcolormesh(lons, lats, stage4 / 25.4, clevs,
                  units='inch')
    mp.drawcounties()
    mp.postprocess(filename='stageIV.png')
    mp.close()

    mp = MapPlot(sector=SECTOR, axisbg='white',
                 title=('%s High-res total prior to QC'
                        ) % (valid.strftime("%-d %b %Y"), ))
    mp.pcolormesh(lons, lats, inqcprecip / 25.4, clevs,
                  units='inch')
    mp.drawcounties()
    mp.postprocess(filename='inqcprecip.png')
    mp.close()

    mp = MapPlot(sector=SECTOR, axisbg='white',
                 title=('%s High-res total after QC'
                        ) % (valid.strftime("%-d %b %Y"), ))
    mp.pcolormesh(lons, lats, outqcprecip / 25.4, clevs,
                  units='inch')
    mp.drawcounties()
    mp.postprocess(filename='outqcprecip.png')
    mp.close()

    mp = MapPlot(sector=SECTOR, axisbg='white',
                 title=('%s QC Change in Precip Out - In'
                        ) % (valid.strftime("%-d %b %Y"), ))
    diff = (outqcprecip - inqcprecip) / 25.4
    mp.pcolormesh(lons, lats, diff,
                  np.arange(-1.4, 1.5, 0.1),
                  cmap=plt.get_cmap('BrBG'),
                  units='inch')
    mp.drawcounties()
    mp.postprocess(filename='qcprecipdiff.png')
    mp.close()

    mp = MapPlot(sector=SECTOR, axisbg='white',
                 title=('%s multiplier'
                        ) % (valid.strftime("%-d %b %Y"), ))
    mp.pcolormesh(lons, lats, multiplier,
                  np.arange(0.0, 2.5, 0.2),
                  cmap=plt.get_cmap('jet'),
                  units='ratio')
    mp.drawcounties()
    mp.postprocess(filename='multiplier.png')
    mp.close()

    mp = MapPlot(sector=SECTOR, axisbg='white',
                 title=('%s manually computed QC Precip  mul * stage4'
                        ) % (valid.strftime("%-d %b %Y"), ))
    mp.pcolormesh(lons, lats, multiplier * stage4 / 25.4,
                  clevs,
                  units='inch')
    mp.drawcounties()
    mp.postprocess(filename='qcmancalc.png')
    mp.close()

    # Go MRMS
    ncfn = "/mesonet/data/iemre/%s_mw_mrms_daily.nc" % (valid.year, )
    if not os.path.isfile(ncfn):
        return
    nc = netCDF4.Dataset(ncfn, 'r')
    xidx = int((WEST - nc.variables['lon'][0]) * 100.)
    yidx = int((SOUTH - nc.variables['lat'][0]) * 100.)
    idx = daily_offset(valid)
    mrms = nc.variables['p01d'][idx, yidx:(yidx+800), xidx:(xidx+921)]
    nc.close()


def main(argv):
    """Do Magic"""
    valid = datetime.date(int(argv[1]), int(argv[2]),
                          int(argv[3]))
    do(valid)


if __name__ == '__main__':
    main(sys.argv)
