"""DEP WEPP cli editor. One "tile" at a time.

Usage:
    python daily_climate_editor.py <xtile> <ytile> <tilesz>
        <scenario> <YYYY> <mm> <dd>

Where tiles start in the lower left corner and are 5x5 deg in size

development laptop has data for 3 March 2019, 23 May 2009, and 8 Jun 2009

"""
from collections import namedtuple
import datetime
import sys
import os
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool

from tqdm import tqdm
import numpy as np
import pytz
from scipy.interpolate import NearestNDInterpolator
from PIL import Image
from pyiem import iemre
from pyiem.dep import SOUTH, WEST, NORTH, EAST, get_cli_fname
from pyiem.util import ncopen, logger, convert_value, utc

LOG = logger()
ST4PATH = "/mesonet/data/stage4"
# used for breakpoint logic
ZEROHOUR = datetime.datetime(2000, 1, 1, 0, 0)
# How many CPUs are we going to burn
CPUCOUNT = max([4, int(cpu_count() / 4)])
MEMORY = {"stamp": datetime.datetime.now()}
BOUNDS = namedtuple("Bounds", ["south", "north", "east", "west"])


def iemre_bounds_check(name, val, lower, upper):
    """Make sure our data is within bounds, if not, exit!"""
    minval = np.nanmin(val)
    maxval = np.nanmax(val)
    if np.ma.is_masked(minval) or minval < lower or maxval > upper:
        LOG.info(
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
    LOG.debug("called")

    offset = iemre.daily_offset(valid)
    lats = nc.variables["lat"][:]
    lons = nc.variables["lon"][:]
    lons, lats = np.meshgrid(lons, lats)

    # Storage is W m-2, we want langleys per day
    ncdata = nc.variables["rsds"][offset, :, :] * 86400.0 / 1000000.0 * 23.9
    # Default to a value of 300 when this data is missing, for some reason
    nn = NearestNDInterpolator(
        (np.ravel(lons), np.ravel(lats)), np.ravel(ncdata)
    )
    data["solar"][:] = iemre_bounds_check(
        "rsds", nn(data["lon"], data["lat"]), 0, 1000
    )

    ncdata = convert_value(
        nc.variables["high_tmpk"][offset, :, :], "degK", "degC"
    )
    nn = NearestNDInterpolator(
        (np.ravel(lons), np.ravel(lats)), np.ravel(ncdata)
    )
    data["high"][:] = iemre_bounds_check(
        "high_tmpk", nn(data["lon"], data["lat"]), -60, 60
    )

    ncdata = convert_value(
        nc.variables["low_tmpk"][offset, :, :], "degK", "degC"
    )
    nn = NearestNDInterpolator(
        (np.ravel(lons), np.ravel(lats)), np.ravel(ncdata)
    )
    data["low"][:] = iemre_bounds_check(
        "low_tmpk", nn(data["lon"], data["lat"]), -60, 60
    )

    ncdata = convert_value(
        nc.variables["avg_dwpk"][offset, :, :], "degK", "degC"
    )
    nn = NearestNDInterpolator(
        (np.ravel(lons), np.ravel(lats)), np.ravel(ncdata)
    )
    data["dwpt"][:] = iemre_bounds_check(
        "avg_dwpk", nn(data["lon"], data["lat"]), -60, 60
    )

    ncdata = nc.variables["wind_speed"][offset, :, :]
    nn = NearestNDInterpolator(
        (np.ravel(lons), np.ravel(lats)), np.ravel(ncdata)
    )
    data["wind"][:] = iemre_bounds_check(
        "wind_speed", nn(data["lon"], data["lat"]), 0, 30
    )
    LOG.debug("finished")


def load_stage4(data, valid, xtile, ytile):
    """It sucks, but we need to load the stage IV data to give us something
    to benchmark the MRMS data against, to account for two things:
    1) Wind Farms
    2) Over-estimates
    """
    LOG.debug("called")
    # The stage4 files store precip in the rears, so compute 1 AM
    one_am = utc(valid.year, valid.month, valid.day, 12)
    one_am = one_am.astimezone(pytz.timezone("America/Chicago"))
    # stage4 data is stored in the rears, so 1am
    one_am = one_am.replace(hour=1, minute=0, second=0)
    # clever hack for CST/CDT
    tomorrow = one_am + datetime.timedelta(hours=36)
    tomorrow = tomorrow.replace(hour=1)

    sts_tidx = iemre.hourly_offset(one_am)
    ets_tidx = iemre.hourly_offset(tomorrow)
    LOG.debug(
        "stage4 sts_tidx:%s[%s] ets_tidx:%s[%s]",
        sts_tidx,
        one_am,
        ets_tidx,
        tomorrow,
    )
    with ncopen("%s/%s_stage4_hourly.nc" % (ST4PATH, valid.year)) as nc:
        p01m = nc.variables["p01m"]

        lats = nc.variables["lat"][:]
        lons = nc.variables["lon"][:]
        # crossing jan 1
        if ets_tidx < sts_tidx:
            LOG.debug("Exercise special stageIV logic for jan1!")
            totals = np.sum(p01m[sts_tidx:, :, :], axis=0)
            with ncopen(
                "%s/%s_stage4_hourly.nc" % (ST4PATH, tomorrow.year)
            ) as nc2:
                p01m = nc2.variables["p01m"]
                totals += np.sum(p01m[:ets_tidx, :, :], axis=0)
        else:
            totals = np.sum(p01m[sts_tidx:ets_tidx, :, :], axis=0)

    if np.ma.max(totals) > 0:
        pass
    else:
        LOG.info("No StageIV data found, aborting...")
        sys.exit(3)
    # set a small non-zero number to keep things non-zero
    totals = np.where(totals > 0.001, totals, 0.001)

    nn = NearestNDInterpolator(
        (lons.flatten(), lats.flatten()), totals.flatten()
    )
    data["stage4"][:] = nn(data["lon"], data["lat"])
    write_grid(data["stage4"], valid, xtile, ytile, "stage4")
    LOG.debug("finished")


def qc_precip(data, valid, xtile, ytile):
    """Make some adjustments to the `precip` grid

    Not very sophisticated here, if the hires precip grid is within 33% of
    Stage IV, then we consider it good.  If not, then we apply a multiplier to
    bring it to near the stage IV value.
    """
    hires_total = np.sum(data["precip"], 2)
    # prevent zeros
    hires_total = np.where(hires_total < 0.01, 0.01, hires_total)
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

    img = Image.open(filename)
    imgdata = np.array(img)
    # Convert the image data to dbz
    dbz = (np.flipud(imgdata[top:bottom, left:right]) - 7.0) * 5.0
    return np.where(dbz < 255, ((10.0 ** (dbz / 10.0)) / 200.0) ** 0.625, 0)


def load_precip_legacy(data, valid, tile_bounds):
    """Compute a Legacy Precip product for dates prior to 1 Jan 2014"""
    LOG.debug("called")
    ts = 12 * 24  # 5 minute

    midnight = utc(valid.year, valid.month, valid.day, 12)
    midnight = midnight.astimezone(pytz.timezone("America/Chicago"))
    midnight = midnight.replace(hour=0, minute=0, second=0)
    # clever hack for CST/CDT
    tomorrow = midnight + datetime.timedelta(hours=36)
    tomorrow = tomorrow.replace(hour=0)

    now = midnight
    m5 = np.zeros((ts, *data["solar"].shape), np.float16)
    tidx = 0
    filenames = []
    indices = []
    # Load up the n0r data, every 5 minutes
    while now < tomorrow:
        utcvalid = now.astimezone(pytz.timezone("UTC"))
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
            LOG.info("missing: %s", fn)

        now += datetime.timedelta(minutes=5)
        tidx += 1

    for tidx, filename in zip(indices, filenames):
        m5[tidx, :, :] = _reader(filename, tile_bounds)
    LOG.debug("finished loading N0R Composites")
    m5 = np.transpose(m5, (1, 2, 0)).copy()
    LOG.debug("transposed the data!")
    m5total = np.sum(m5, 2)
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

    midnight = utc(valid.year, valid.month, valid.day)
    midnight = midnight.astimezone(pytz.timezone("America/Chicago"))
    midnight = midnight.replace(hour=0, minute=0, second=0)
    # clever hack for CST/CDT
    tomorrow = midnight + datetime.timedelta(hours=36)
    tomorrow = tomorrow.replace(hour=0)

    top = int((55.0 - tile_bounds.north) * 100.0)
    bottom = int((55.0 - tile_bounds.south) * 100.0)

    right = int((tile_bounds.east - -130.0) * 100.0)
    left = int((tile_bounds.west - -130.0) * 100.0)

    # Oopsy we discovered a problem
    a2m_divisor = 10.0 if (valid < datetime.date(2015, 1, 1)) else 50.0

    now = midnight
    # Require at least 75% data coverage, if not, we will abort back to legacy
    quorum = 720 * 0.75
    fns = []
    while now < tomorrow:
        utcvalid = now.astimezone(pytz.UTC)
        fn = utcvalid.strftime(
            "/mesonet/ARCHIVE/data/%Y/%m/%d/GIS/mrms/a2m_%Y%m%d%H%M.png"
        )
        if os.path.isfile(fn):
            quorum -= 1
            fns.append(fn)
        else:
            fns.append(None)
            LOG.info("daily_clifile_editor missing: %s", fn)

        now += datetime.timedelta(minutes=2)
    if quorum > 0:
        LOG.info(
            "WARNING: Failed quorum with MRMS a2m %.1f, loading legacy", quorum
        )
        data["precip"][:] = 0
        load_precip_legacy(data, valid, tile_bounds)

    def _reader(tidx, fn):
        """Reader."""
        if fn is None:
            return tidx, 0
        img = Image.open(fn)
        imgdata = np.array(img)
        # sample out and then flip top to bottom!
        return tidx, np.flipud(imgdata[top:bottom, left:right])

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
    LOG.debug("finished")


def bpstr(ts, accum):
    """Make a string representation of this breakpoint and accumulation"""
    # Need four decimals for accurate reproduction
    return "%02i.%04i %.2f" % (ts.hour, ts.minute / 60.0 * 10000.0, accum)


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
    if accum != lastaccum:
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
    np.save(
        "%s/%s%s.tile_%s_%s"
        % (basedir, valid.strftime("%Y%m%d"), fnadd, xtile, ytile),
        grid,
    )


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
    qc_precip(data, valid, xtile, ytile)
    write_grid(np.sum(data["precip"], 2), valid, xtile, ytile)


def edit_clifile(xidx, yidx, clifn, data, valid):
    """Edit the climate file, run from thread."""
    # Okay we have work to do
    clidata = open(clifn, "r").read()
    pos = clidata.find(valid.strftime("%-d\t%-m\t%Y"))
    if pos == -1:
        LOG.info("Date find failure for %s", clifn)
        return False

    pos2 = clidata[pos:].find(
        (valid + datetime.timedelta(days=1)).strftime("%-d\t%-m\t%Y")
    )
    if pos2 == -1:
        LOG.info("Date2 find failure for %s", clifn)
        return False

    bpdata = compute_breakpoint(data["precip"][yidx, xidx, :])
    if bpdata is None:
        bpdata = []

    thisday = (
        "%s\t%s\t%s\t%s\t%3.1f\t%3.1f\t%4.0f\t%4.1f\t%s\t%4.1f\n%s%s"
    ) % (
        valid.day,
        valid.month,
        valid.year,
        len(bpdata),
        data["high"][yidx, xidx],
        data["low"][yidx, xidx],
        data["solar"][yidx, xidx],
        data["wind"][yidx, xidx],
        0,
        data["dwpt"][yidx, xidx],
        "\n".join(bpdata),
        "\n" if bpdata else "",
    )

    with open(clifn, "w") as fh:
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
    LOG.debug("bounds %s", tile_bounds)
    shp = (
        int((tile_bounds.north - tile_bounds.south) * 100),
        int((tile_bounds.east - tile_bounds.west) * 100),
    )
    data = {}
    for vname in "high low dwpt wind solar stage4".split():
        data[vname] = np.zeros(shp, np.float16)
    # Optimize for continuous memory
    data["precip"] = np.zeros((*shp, 30 * 24), np.float16)

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

    def _callback(_res):
        """We got a result."""
        progress.update(1)

    def _errorback(exp):
        """We hit trouble."""
        LOG.exception(exp)

    with ThreadPool(CPUCOUNT) as pool:
        for i, (xidx, yidx, clifn) in enumerate(queue):
            pool.apply_async(
                edit_clifile,
                (xidx, yidx, clifn, data, valid),
                callback=_callback,
                error_callback=_errorback,
            )
        pool.close()
        pool.join()


if __name__ == "__main__":
    # Go Main Go
    main(sys.argv)


def test_compute_tilebounds():
    """Test that computing tilebounds works."""
    res = compute_tile_bounds(5, 5, 5)
    assert abs(res.south - 60.0) < 0.01


def test_bp():
    """issue #6 invalid time"""
    data = np.zeros([30 * 24])
    data[0] = 3.2
    bp = compute_breakpoint(data)
    assert bp[0] == "00.0000 0.00"
    assert bp[1] == "00.0333 3.20"
    data[0] = 0
    data[24 * 30 - 1] = 9.99
    bp = compute_breakpoint(data)
    assert bp[0] == "23.9666 0.00"
    assert bp[1] == "23.9833 9.99"

    data[24 * 30 - 1] = 10.99
    bp = compute_breakpoint(data)
    assert bp[0] == "23.9666 0.00"
    assert bp[1] == "23.9833 10.99"

    # Do some random futzing
    for _ in range(100):
        data = np.random.randint(20, size=(30 * 24,))
        bp = compute_breakpoint(data)
        lastts = -1
        lastaccum = -1
        for b in bp:
            tokens = b.split()
            if float(tokens[0]) <= lastts or float(tokens[1]) <= lastaccum:
                print(data)
                print(bp)
                assert False
            lastts = float(tokens[0])
            lastaccum = float(tokens[1])
