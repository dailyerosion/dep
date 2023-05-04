"""Plot what was saved from daily_clifile_editor processing"""
import datetime
import os
import sys

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import netCDF4
import numpy as np
from geopandas import read_postgis
from matplotlib.patches import Polygon
from pyiem.iemre import (
    EAST,
    NORTH,
    SOUTH,
    WEST,
    daily_offset,
    get_daily_mrms_ncname,
)
from pyiem.plot import MapPlot
from pyiem.util import get_dbconn

YS = np.arange(SOUTH, NORTH, 0.01)
XS = np.arange(WEST, EAST, 0.01)
SECTOR = "iowa"


def load_precip(date, extra=""):
    """Load up our QC'd daily precip dataset"""
    fn = date.strftime(
        "/mnt/idep2/data/dailyprecip/%Y/%Y%m%d" + extra + ".npy"
    )
    if not os.path.isfile(fn):
        print("load_precip(%s) failed, no such file %s" % (date, fn))
        return
    return np.load(fn)


def do(valid):
    """Do Something"""
    clevs = np.arange(0, 0.25, 0.05)
    clevs = np.append(clevs, np.arange(0.25, 3.0, 0.25))
    clevs = np.append(clevs, np.arange(3.0, 10.0, 1))
    clevs[0] = 0.01

    precip = load_precip(valid)
    stage4 = load_precip(valid, "stage4")
    inqcprecip = load_precip(valid, "inqcprecip")
    outqcprecip = load_precip(valid, "outqcprecip")
    multiplier = load_precip(valid, "multiplier")

    yidx = int((43.27 - SOUTH) / 0.01)
    xidx = int((-94.39 - WEST) / 0.01)
    projection = ccrs.Mercator()
    pgconn = get_dbconn("idep")
    df = read_postgis(
        """
        SELECT ST_Transform(simple_geom, %s) as geom, huc_12,
        ST_x(ST_Transform(ST_Centroid(geom), 4326)) as centroid_x,
        ST_y(ST_Transform(ST_Centroid(geom), 4326)) as centroid_y, name
        from huc12 i WHERE i.scenario = 0 and huc_12 = '071100010901'
    """,
        pgconn,
        params=(projection.proj4_init,),
        geom_col="geom",
        index_col="huc_12",
    )

    mp = MapPlot(
        sector="custom",
        axisbg="white",
        west=-92.0,
        south=40.24,
        east=-91.69,
        north=40.4,
        subtitle="Flowpath numbers are labelled.",
        title=("%s DEP Quality Controlled Precip Totals for 071100010901")
        % (valid.strftime("%-d %b %Y"),),
    )
    (lons, lats) = np.meshgrid(XS, YS)
    mp.pcolormesh(lons, lats, precip / 25.4, clevs, units="inch")
    mp.drawcounties()
    for _huc12, row in df.iterrows():
        p = Polygon(row["geom"].exterior, ec="k", fc="None", zorder=100, lw=2)
        mp.ax.add_patch(p)
    df = read_postgis(
        """
        SELECT ST_Transform(geom, %s) as geom, fpath
        from flowpaths WHERE scenario = 0 and huc_12 = '071100010901'
    """,
        pgconn,
        params=(projection.proj4_init,),
        geom_col="geom",
        index_col="fpath",
    )
    for fpath, row in df.iterrows():
        mp.ax.plot(row["geom"].xy[0], row["geom"].xy[1], c="k")

    df = read_postgis(
        """
        SELECT ST_Transform(st_pointn(geom, 1), %s) as geom, fpath
        from flowpaths WHERE scenario = 0 and huc_12 = '071100010901'
    """,
        pgconn,
        params=(projection.proj4_init,),
        geom_col="geom",
        index_col="fpath",
    )
    for fpath, row in df.iterrows():
        mp.ax.text(row["geom"].x, row["geom"].y, str(fpath), fontsize=12)

    mp.postprocess(filename="qc.png")
    mp.close()

    mp = MapPlot(
        sector=SECTOR,
        axisbg="white",
        title=("%s Stage IV Precip Totals") % (valid.strftime("%-d %b %Y"),),
    )
    mp.pcolormesh(lons, lats, stage4 / 25.4, clevs, units="inch")
    mp.drawcounties()
    mp.postprocess(filename="stageIV.png")
    mp.close()

    mp = MapPlot(
        sector=SECTOR,
        axisbg="white",
        title=("%s High-res total prior to QC")
        % (valid.strftime("%-d %b %Y"),),
    )
    mp.pcolormesh(lons, lats, inqcprecip / 25.4, clevs, units="inch")
    mp.drawcounties()
    mp.postprocess(filename="inqcprecip.png")
    mp.close()

    mp = MapPlot(
        sector=SECTOR,
        axisbg="white",
        title=("%s High-res total after QC") % (valid.strftime("%-d %b %Y"),),
    )
    mp.pcolormesh(lons, lats, outqcprecip / 25.4, clevs, units="inch")
    mp.drawcounties()
    mp.postprocess(filename="outqcprecip.png")
    mp.close()

    mp = MapPlot(
        sector=SECTOR,
        axisbg="white",
        title=("%s QC Change in Precip Out - In")
        % (valid.strftime("%-d %b %Y"),),
    )
    diff = (outqcprecip - inqcprecip) / 25.4
    mp.pcolormesh(
        lons,
        lats,
        diff,
        np.arange(-1.4, 1.5, 0.1),
        cmap=plt.get_cmap("BrBG"),
        units="inch",
    )
    mp.drawcounties()
    mp.postprocess(filename="qcprecipdiff.png")
    mp.close()

    mp = MapPlot(
        sector=SECTOR,
        axisbg="white",
        title=("%s multiplier") % (valid.strftime("%-d %b %Y"),),
    )
    mp.pcolormesh(
        lons,
        lats,
        multiplier,
        np.arange(0.0, 2.5, 0.2),
        cmap=plt.get_cmap("jet"),
        units="ratio",
    )
    mp.drawcounties()
    mp.postprocess(filename="multiplier.png")
    mp.close()

    mp = MapPlot(
        sector=SECTOR,
        axisbg="white",
        title=("%s manually computed QC Precip  mul * stage4")
        % (valid.strftime("%-d %b %Y"),),
    )
    mp.pcolormesh(lons, lats, multiplier * stage4 / 25.4, clevs, units="inch")
    mp.drawcounties()
    mp.postprocess(filename="qcmancalc.png")
    mp.close()

    # Go MRMS
    ncfn = get_daily_mrms_ncname(valid.year)
    if not os.path.isfile(ncfn):
        return
    nc = netCDF4.Dataset(ncfn, "r")
    xidx = int((WEST - nc.variables["lon"][0]) * 100.0)
    yidx = int((SOUTH - nc.variables["lat"][0]) * 100.0)
    idx = daily_offset(valid)
    nc.variables["p01d"][idx, yidx : (yidx + 800), xidx : (xidx + 921)]
    nc.close()


def main(argv):
    """Do Magic"""
    valid = datetime.date(int(argv[1]), int(argv[2]), int(argv[3]))
    do(valid)


if __name__ == "__main__":
    main(sys.argv)
