"""DEP WEPP cli editor. One "tile" at a time.

Usage:
    python daily_climate_editor.py <xtile> <ytile> <tilesz>
        <scenario> <YYYY> <mm> <dd>

Where tiles start in the lower left corner and are 5x5 deg in size

development laptop has data for 3 March 2019

"""

try:
    from zoneinfo import ZoneInfo  # type: ignore
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore
import datetime
import os
import sys
import traceback
from collections import namedtuple
from io import StringIO
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool

import numpy as np
from osgeo import gdal
from pydep.io.cli import daily_formatter
from pydep.util import get_cli_fname
from pyiem import iemre
from pyiem.iemre import EAST, NORTH, SOUTH, WEST
from pyiem.util import convert_value, logger, ncopen
from scipy.interpolate import NearestNDInterpolator
from tqdm import tqdm

gdal.UseExceptions()
LOG = logger()
CENTRAL = ZoneInfo("America/Chicago")
UTC = datetime.timezone.utc
ST4PATH = "/mesonet/data/stage4"
# used for breakpoint logic
ZEROHOUR = datetime.datetime(2000, 1, 1, 0, 0)
# How many CPUs are we going to burn
CPUCOUNT = min([4, int(cpu_count() / 4)])
MEMORY = {"stamp": datetime.datetime.now()}
BOUNDS = namedtuple("Bounds", ["south", "north", "east", "west"])
# An estimate of the number of years of data we have in our climate files
ESTIMATED_YEARS = datetime.date.today().year - 2007 + 1


def check_has_clifiles(bounds: BOUNDS):
    """Check that a directory exists, which likely indicates clifiles exist."""
    for lon in np.arange(bounds.west, bounds.east, 1):
        for lat in np.arange(bounds.south, bounds.north, 1):
            ckdir = f"/i/0/cli/{(0 - lon):03.0f}x{(lat):03.0f}"
            if os.path.isdir(ckdir):
                return True
    return False


def get_sts_ets_at_localhour(date, local_hour):
    """Return a Day Interval in UTC for the given date at CST/CDT hour."""
    # ZoneInfo is supposed to get this right at instanciation
    sts = datetime.datetime(
        date.year,
        date.month,
        date.day,
        local_hour,
        tzinfo=CENTRAL,
    )
    date2 = datetime.date(
        date.year, date.month, date.day
    ) + datetime.timedelta(days=1)
    ets = datetime.datetime(
        date2.year,
        date2.month,
        date2.day,
        local_hour,
        tzinfo=CENTRAL,
    )
    return (
        sts.replace(hour=local_hour).astimezone(UTC),
        ets.replace(hour=local_hour).astimezone(UTC),
    )


def iemre_bounds_check(name, val, lower, upper):
    """Make sure our data is within bounds, if not, exit!"""
    if np.isnan(val).all():
        LOG.warning("FATAL: iemre %s all NaN", name)
        sys.exit(3)
    minval = np.nanmin(val)
    maxval = np.nanmax(val)
    if minval < lower or maxval > upper:
        LOG.warning(
            "FATAL: iemre failure %s %.3f to %.3f [%.3f to %.3f]",
            name,
            minval,
            maxval,
            lower,
            upper,
        )
        sys.exit(3)
    return val


def load_iemre(nc, data, valid):
    """Use IEM Reanalysis for non-precip data

    24km product is smoothed down to the 0.01 degree grid
    """
    offset = iemre.daily_offset(valid)
    lats = nc.variables["lat"][:]
    lons = nc.variables["lon"][:]
    lons, lats = np.meshgrid(lons, lats)

    # Storage is W m-2, we want langleys per day
    ncdata = (
        nc.variables["rsds"][offset, :, :].filled(np.nan)
        * 86400.0
        / 1_000_000.0
        * 23.9
    )
    # Default to a value of 300 when this data is missing, for some reason
    nn = NearestNDInterpolator(
        (np.ravel(lons), np.ravel(lats)), np.ravel(ncdata)
    )
    # What's a reasonable max bounts?  Well, 50 MJ/d should be an extreme high
    data["solar"][:] = iemre_bounds_check(
        "rsds", nn(data["lon"], data["lat"]), 0, 50.0 * 23.9
    )

    ncdata = convert_value(
        nc.variables["high_tmpk"][offset, :, :].filled(np.nan), "degK", "degC"
    )
    nn = NearestNDInterpolator(
        (np.ravel(lons), np.ravel(lats)), np.ravel(ncdata)
    )
    data["high"][:] = iemre_bounds_check(
        "high_tmpk", nn(data["lon"], data["lat"]), -60, 60
    )

    ncdata = convert_value(
        nc.variables["low_tmpk"][offset, :, :].filled(np.nan), "degK", "degC"
    )
    nn = NearestNDInterpolator(
        (np.ravel(lons), np.ravel(lats)), np.ravel(ncdata)
    )
    data["low"][:] = iemre_bounds_check(
        "low_tmpk", nn(data["lon"], data["lat"]), -60, 60
    )

    ncdata = convert_value(
        nc.variables["avg_dwpk"][offset, :, :].filled(np.nan), "degK", "degC"
    )
    nn = NearestNDInterpolator(
        (np.ravel(lons), np.ravel(lats)), np.ravel(ncdata)
    )
    data["dwpt"][:] = iemre_bounds_check(
        "avg_dwpk", nn(data["lon"], data["lat"]), -60, 60
    )

    # Wind is already in m/s, but could be masked
    ncdata = nc.variables["wind_speed"][offset, :, :].filled(np.nan)
    nn = NearestNDInterpolator(
        (np.ravel(lons), np.ravel(lats)), np.ravel(ncdata)
    )
    # 30 found to be too high (13 Sep 2008)
    data["wind"][:] = iemre_bounds_check(
        "wind_speed", nn(data["lon"], data["lat"]), 0, 40
    )


def load_stage4(data, valid, xtile, ytile):
    """It sucks, but we need to load the stage IV data to give us something
    to benchmark the MRMS data against, to account for two things:
    1) Wind Farms
    2) Over-estimates
    """
    LOG.debug("called")
    # The stage4 files store precip in the rears, so compute 1 AM
    one_am, tomorrow = get_sts_ets_at_localhour(valid, 1)

    sts_tidx = iemre.hourly_offset(one_am)
    ets_tidx = iemre.hourly_offset(tomorrow)
    LOG.debug(
        "stage4 sts_tidx:%s[%s] ets_tidx:%s[%s]",
        sts_tidx,
        one_am,
        ets_tidx,
        tomorrow,
    )
    with ncopen(f"{ST4PATH}/{valid.year}_stage4_hourly.nc", "r") as nc:
        p01m = nc.variables["p01m"]

        lats = nc.variables["lat"][:]
        lons = nc.variables["lon"][:]
        # crossing jan 1
        if ets_tidx < sts_tidx:
            LOG.debug("Exercise special stageIV logic for jan1!")
            totals = np.sum(p01m[sts_tidx:, :, :], axis=0)
            with ncopen(f"{ST4PATH}/{tomorrow.year}_stage4_hourly.nc") as nc2:
                p01m = nc2.variables["p01m"]
                totals += np.sum(p01m[:ets_tidx, :, :], axis=0)
        else:
            totals = np.sum(p01m[sts_tidx:ets_tidx, :, :], axis=0)

    if np.ma.max(totals) > 0:
        pass
    else:
        LOG.warning("No StageIV data found, aborting...")
        sys.exit(3)
    # set a small non-zero number to keep things non-zero
    totals[totals < 0.001] = 0.001

    nn = NearestNDInterpolator(
        (lons.flatten(), lats.flatten()), totals.flatten()
    )
    data["stage4"][:] = nn(data["lon"], data["lat"])
    write_grid(data["stage4"], valid, xtile, ytile, "stage4")
    LOG.debug("finished")


def qc_precip(data, valid, xtile, ytile, tile_bounds):
    """Make some adjustments to the `precip` grid

    Not very sophisticated here, if the hires precip grid is within 33% of
    Stage IV, then we consider it good.  If not, then we apply a multiplier to
    bring it to near the stage IV value.
    """
    hires_total = np.sum(data["precip"], 2)
    # Only do this check for tiles west of -101, likely too crude for east
    if valid.year >= 2015 and xtile < 5:
        # Do an assessment of the hires_total (A2M MRMS), it may have too many
        # zeros where stage IV has actual data.
        a2m_zeros = hires_total < 0.01
        s4 = data["stage4"] > 5  # arb
        score = np.sum(np.logical_and(a2m_zeros, s4)) / np.multiply(*s4.shape)
        if score > 0.005:  # 0.5% is arb, but good enough?
            LOG.warning("MRMS had %.2f%% bad zeros, using legacy", score * 100)
            load_precip_legacy(data, valid, tile_bounds)
            hires_total = np.sum(data["precip"], 2)

    # prevent zeros
    hires_total[hires_total < 0.01] = 0.01
    write_grid(hires_total, valid, xtile, ytile, "inqcprecip")
    multiplier = data["stage4"] / hires_total

    # Anything close to 1, set it to 1
    multiplier = np.where(
        np.logical_and(multiplier > 0.67, multiplier < 1.33), 1.0, multiplier
    )
    write_grid(multiplier, valid, xtile, ytile, "multiplier")
    data["precip"][:] *= multiplier[:, :, None]
    data["precip"][np.isnan(data["precip"])] = 0.0
    write_grid(np.sum(data["precip"], 2), valid, xtile, ytile, "outqcprecip")


def _reader(filename, tile_bounds):
    top = int((50.0 - tile_bounds.north) * 100.0)
    bottom = int((50.0 - tile_bounds.south) * 100.0)

    right = int((tile_bounds.east - -126.0) * 100.0)
    left = int((tile_bounds.west - -126.0) * 100.0)

    imgdata = gdal.Open(filename, 0).ReadAsArray()
    # Convert the image data to dbz
    dbz = (np.flipud(imgdata[top:bottom, left:right]) - 7.0) * 5.0
    return np.where(dbz < 255, ((10.0 ** (dbz / 10.0)) / 200.0) ** 0.625, 0)


def load_precip_legacy(data, valid, tile_bounds):
    """Compute a Legacy Precip product for dates prior to 1 Jan 2014"""
    LOG.debug("called")
    ts = 12 * 24  # 5 minute

    midnight, tomorrow = get_sts_ets_at_localhour(valid, 0)

    now = midnight
    # To avoid division by zero below when we have the strip of no-data 23-24N
    m5 = np.ones((ts, *data["solar"].shape), np.float16) * 0.01
    tidx = 0
    filenames = []
    indices = []
    # Load up the n0r data, every 5 minutes
    while now < tomorrow:
        utcvalid = now.astimezone(UTC)
        fn = utcvalid.strftime(
            "/mesonet/ARCHIVE/data/%Y/%m/%d/GIS/uscomp/n0r_%Y%m%d%H%M.png"
        )
        if os.path.isfile(fn):
            if tidx >= ts:
                # Abort as we are in CST->CDT
                break
            filenames.append(fn)
            indices.append(tidx)
        else:
            LOG.warning("missing: %s", fn)

        now += datetime.timedelta(minutes=5)
        tidx += 1

    for tidx, filename in zip(indices, filenames):
        # Legacy product may not go far enough south :/
        yslice = slice(100, 500) if tile_bounds.south == 23 else slice(0, 500)
        m5[tidx, yslice, :] = _reader(filename, tile_bounds)
    LOG.debug("finished loading N0R Composites")
    m5 = np.transpose(m5, (1, 2, 0)).copy()
    LOG.debug("transposed the data!")
    # Prevent overflow with likely bad data leading to value > np.float16
    m5total = np.sum(m5, 2, dtype=np.float32)
    LOG.debug("computed sum(m5)")
    wm5 = m5 / m5total[:, :, None]
    LOG.debug("computed weights of m5")

    minute2 = np.arange(0, 60 * 24, 2)
    minute5 = np.arange(0, 60 * 24, 5)

    def _compute(yidx, xidx):
        """expensive computation that needs vectorized, somehow"""
        s4total = data["stage4"][yidx, xidx]
        # any stage IV totals less than 0.4mm are ignored, so effectively 0
        if s4total < 0.4:
            return
        # Interpolate weights to a 2 minute interval grid
        # we divide by 2.5 to downscale the 5 minute values to 2 minute
        weights = np.interp(minute2, minute5, wm5[yidx, xidx, :]) / 2.5
        # Now apply the weights to the s4total
        data["precip"][yidx, xidx, :] = weights * s4total

    for x in range(data["solar"].shape[1]):
        for y in range(data["solar"].shape[0]):
            _compute(y, x)

    LOG.debug("finished precip calculation")


def load_precip(data, valid, tile_bounds):
    """Load the 5 minute precipitation data into our ginormus grid"""
    LOG.debug("called")
    ts = 30 * 24  # 2 minute

    midnight, tomorrow = get_sts_ets_at_localhour(valid, 0)

    top = int((55.0 - tile_bounds.north) * 100.0)
    bottom = int((55.0 - tile_bounds.south) * 100.0)

    right = int((tile_bounds.east - -130.0) * 100.0)
    left = int((tile_bounds.west - -130.0) * 100.0)

    # Oopsy we discovered a problem
    a2m_divisor = 10.0 if (valid < datetime.date(2015, 1, 1)) else 50.0

    now = midnight
    # Require at least 75% data coverage, if not, we will abort back to legacy
    quorum = ts * 0.75
    fns = []
    while now < tomorrow:
        fn = now.astimezone(UTC).strftime(
            "/mesonet/ARCHIVE/data/%Y/%m/%d/GIS/mrms/a2m_%Y%m%d%H%M.png"
        )
        if os.path.isfile(fn):
            quorum -= 1
            fns.append(fn)
        else:
            fns.append(None)
            # TODO log this from proctor to cut down on noise
            LOG.info("missing: %s", fn)

        now += datetime.timedelta(minutes=2)
    if quorum > 0:
        LOG.warning(
            "Failed 75%% quorum with MRMS a2m %.1f, loading legacy", quorum
        )
        load_precip_legacy(data, valid, tile_bounds)
        return
    LOG.debug("fns[0]: %s fns[-1]: %s", fns[0], fns[-1])

    def _reader(tidx, fn):
        """Reader."""
        if fn is None:
            return tidx, 0
        # PIL is not thread safe, so we need to use GDAL
        imgdata = gdal.Open(fn, 0).ReadAsArray()
        # sample out and then flip top to bottom!
        imgdata = np.flipud(np.array(imgdata)[top:bottom, left:right])
        return tidx, imgdata

    def _cb(args):
        """write data."""
        tidx, pdata = args
        data["precip"][:, :, tidx] = np.where(
            pdata < 255,
            pdata / a2m_divisor,
            0,
        )

    LOG.debug("starting %s threads to read a2m", CPUCOUNT)
    with ThreadPool(CPUCOUNT) as pool:
        for tidx, fn in enumerate(fns):
            # we ignore an hour for CDT->CST, meh
            if tidx >= ts:
                continue
            pool.apply_async(_reader, (tidx, fn), callback=_cb)
        pool.close()
        pool.join()


def bpstr(ts, accum):
    """Make a string representation of this breakpoint and accumulation"""
    # Need four decimals for accurate reproduction
    return f"{ts.hour:02.0f}.{(ts.minute / 60. * 10000.):04.0f} {accum:.2f}"


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
    # To append a last accumulation, we need to have something meaningful
    # so to not have redundant values, which bombs WEPP
    if accum - lastaccum > 0.02:
        if (lasti + 1) == len(ar):
            ts = ZEROHOUR.replace(hour=23, minute=59)
        else:
            ts = ZEROHOUR + datetime.timedelta(minutes=((lasti + 1) * 2))
        bp.append(bpstr(ts, accum))
    return bp


def write_grid(grid, valid, xtile, ytile, fnadd=""):
    """Save off the daily precip totals for usage later in computing huc_12"""
    if fnadd != "" and not sys.stdout.isatty():
        LOG.debug("not writting extra grid to disk")
        return
    basedir = f"/mnt/idep2/data/dailyprecip/{valid.year}"
    if not os.path.isdir(basedir):
        os.makedirs(basedir)
    np.save(f"{basedir}/{valid:%Y%m%d}{fnadd}.tile_{xtile}_{ytile}", grid)


def precip_workflow(data, valid, xtile, ytile, tile_bounds):
    """Drive the precipitation workflow"""
    load_stage4(data, valid, xtile, ytile)
    # We have MRMS a2m RASTER files prior to 1 Jan 2015, but these files used
    # a very poor choice of data interval of 0.1mm, which is not large enough
    # to capture low intensity events.  Files after 1 Jan 2015 used a better
    # 0.02mm resolution
    if valid.year < 2015:
        load_precip_legacy(data, valid, tile_bounds)
    else:
        load_precip(data, valid, tile_bounds)
    qc_precip(data, valid, xtile, ytile, tile_bounds)
    write_grid(np.sum(data["precip"], 2), valid, xtile, ytile)


def edit_clifile(xidx, yidx, clifn, data, valid) -> bool:
    """Edit the climate file, run from thread."""
    # Okay we have work to do
    with open(clifn, "r", encoding="utf8") as fh:
        clidata = fh.read()
    pos = clidata.find(valid.strftime("%-d\t%-m\t%Y"))
    if pos == -1:
        LOG.warning("Date find failure for %s", clifn)
        return False

    pos2 = clidata[pos:].find(
        (valid + datetime.timedelta(days=1)).strftime("%-d\t%-m\t%Y")
    )
    if pos2 == -1:
        LOG.warning("Date2 find failure for %s", clifn)
        return False

    intensity_threshold = 1.0
    bpdata = compute_breakpoint(
        data["precip"][yidx, xidx, :],
    )
    if bpdata is None:
        bpdata = []
    while len(bpdata) >= 100:
        intensity_threshold += 2
        LOG.debug("len(bpdata) %s>100 t:%s", len(bpdata), intensity_threshold)
        bpdata = compute_breakpoint(
            data["precip"][yidx, xidx, :],
            accumThreshold=intensity_threshold,
            intensityThreshold=intensity_threshold,
        )

    high = data["high"][yidx, xidx]
    low = data["low"][yidx, xidx]
    solar = data["solar"][yidx, xidx]
    wind = data["wind"][yidx, xidx]
    dwpt = data["dwpt"][yidx, xidx]
    if np.isnan([high, low, solar, wind, dwpt]).any():
        msg = []
        for v, n in zip(
            [high, low, solar, wind, dwpt],
            "hi lo sol wnd dpt".split(),
        ):
            if np.isnan(v):
                msg.append(f"{n}={v}")
        LOG.warning("Missing data[%s] for %s", ",".join(msg), clifn)
        return False
    thisday = daily_formatter(
        valid,
        bpdata,
        high,
        low,
        solar,
        wind,
        dwpt,
    )

    with open(clifn, "w", encoding="utf8") as fh:
        fh.write(clidata[:pos] + thisday + clidata[(pos + pos2) :])
    return True


def compute_tile_bounds(xtile, ytile, tilesize) -> BOUNDS:
    """Return a BOUNDS namedtuple."""
    south = SOUTH + ytile * tilesize
    west = WEST + xtile * tilesize
    return BOUNDS(
        south=south,
        north=min([south + tilesize, NORTH]),
        west=west,
        east=min([west + tilesize, EAST]),
    )


def main(argv):
    """The workflow to get the weather data variables we want!"""
    if len(argv) != 8:
        print(
            "Usage: python daily_climate_editor.py <xtile> <ytile> <tilesz> "
            "<scenario> <YYYY> <mm> <dd>"
        )
        return
    xtile = int(argv[1])
    ytile = int(argv[2])
    tilesize = int(argv[3])
    scenario = int(argv[4])
    valid = datetime.date(int(argv[5]), int(argv[6]), int(argv[7]))

    tile_bounds = compute_tile_bounds(xtile, ytile, tilesize)
    LOG.info("bounds %s", tile_bounds)
    shp = (
        int((tile_bounds.north - tile_bounds.south) * 100),
        int((tile_bounds.east - tile_bounds.west) * 100),
    )
    data = {}
    for vname in "high low dwpt wind solar stage4".split():
        data[vname] = np.zeros(shp, np.float16)

    # Optimize for continuous memory
    data["precip"] = np.zeros((*shp, 30 * 24), np.float16)

    # We could be outside conus, if so, just write out zeros
    if not check_has_clifiles(tile_bounds):
        LOG.info("Exiting as tile %s %s is outside CONUS", xtile, ytile)
        write_grid(np.sum(data["precip"], 2), valid, xtile, ytile)
        return

    xaxis = np.arange(tile_bounds.west, tile_bounds.east, 0.01)
    yaxis = np.arange(tile_bounds.south, tile_bounds.north, 0.01)
    data["lon"], data["lat"] = np.meshgrid(xaxis, yaxis)

    # 1. Max Temp C
    # 2. Min Temp C
    # 3. Radiation l/d
    # 4. wind mps
    # 6. Mean dewpoint C
    with ncopen(iemre.get_daily_ncname(valid.year)) as nc:
        load_iemre(nc, data, valid)
    # 5. wind direction (always zero)
    # 7. breakpoint precip mm
    precip_workflow(data, valid, xtile, ytile, tile_bounds)

    queue = []
    for yidx in range(shp[0]):
        for xidx in range(shp[1]):
            lon = tile_bounds.west + xidx * 0.01
            lat = tile_bounds.south + yidx * 0.01
            clifn = get_cli_fname(lon, lat, scenario)
            if not os.path.isfile(clifn):
                continue
            queue.append([xidx, yidx, clifn])

    progress = tqdm(total=len(queue), disable=not sys.stdout.isatty())
    errors = {"cnt": 0}

    with ThreadPool(CPUCOUNT) as pool:

        def _callback(res):
            """We got a result."""
            if not res:
                errors["cnt"] += 1
            progress.update(1)

        def _proxy(xidx, yidx, clifn, data, valid):
            """Proxy."""
            if errors["cnt"] > 10:
                return False
            try:
                return edit_clifile(xidx, yidx, clifn, data, valid)
            except Exception as _exp:
                with StringIO() as sio:
                    traceback.print_exc(file=sio)
                    LOG.error(
                        "edit_clifile(%s, %s, %s) failed: %s",
                        xidx,
                        yidx,
                        clifn,
                        sio.getvalue(),
                    )
            return False

        for _, (xidx, yidx, clifn) in enumerate(queue):
            pool.apply_async(
                _proxy,
                (xidx, yidx, clifn, data, valid),
                callback=_callback,
            )
        pool.close()
        pool.join()


if __name__ == "__main__":
    # Go Main Go
    main(sys.argv)
