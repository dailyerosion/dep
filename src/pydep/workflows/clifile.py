"""DEP Workflows around CLI files."""

import os
import sys
import traceback
import warnings
from datetime import date, datetime, timedelta, timezone
from io import StringIO
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
from typing import Optional
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import rasterio
from affine import Affine
from osgeo import gdal
from pyiem.database import get_sqlalchemy_conn, sql_helper
from pyiem.grid.nav import STAGE4, get_nav
from pyiem.iemre import DOMAINS, get_grids, hourly_offset
from pyiem.models.gridnav import CartesianGridNavigation
from pyiem.util import LOG, archive_fetch, convert_value, ncopen
from rasterio.errors import NotGeoreferencedWarning
from rasterio.warp import reproject
from tqdm import tqdm

from pydep.io.cli import daily_formatter
from pydep.reference import GRID_SPACING

# NB: This seems to be some thread safety issue with GDAL
warnings.simplefilter("ignore", NotGeoreferencedWarning)
gdal.UseExceptions()
CENTRAL = ZoneInfo("America/Chicago")
UTC = timezone.utc
ST4PATH = "/mesonet/data/stage4"
# used for breakpoint logic
ZEROHOUR = datetime(2000, 1, 1, 0, 0)
# How many CPUs are we going to burn
CPUCOUNT = min([4, int(cpu_count() / 4)])
MEMORY = {"stamp": datetime.now()}
# An estimate of the number of years of data we have in our climate files
ESTIMATED_YEARS = date.today().year - 2007 + 1


class CLIFileWorkflowFailure(Exception):
    """Exception for CLIFileWorkflow failures."""


def load_clifiles(
    scenario: int, domain: str, tilenav: CartesianGridNavigation
) -> pd.DataFrame:
    """Return metadata for climate files within this tile.

    Important: The west and south values are inclusive, while the east and
    north values are exclusive.
    """
    dbname = "idep" if domain == "" else f"dep_{domain}"
    with get_sqlalchemy_conn(dbname) as conn:
        return pd.read_sql(
            sql_helper("""
    select st_x(geom) as lon, st_y(geom) as lat, filepath from climate_files
    WHERE scenario = :scenario and ST_Contains(
        ST_MakeEnvelope(:west, :south, :east, :north, 4326), geom)
                 """),
            conn,
            params={
                "scenario": scenario,
                "west": tilenav.left_edge,
                "east": tilenav.right_edge,
                "north": tilenav.top_edge,
                "south": tilenav.bottom_edge,
            },
        )


def get_sts_ets_at_localhour(domain: str, dt: date, local_hour: int):
    """Compute the start and end times for a local domain date."""
    tzinfo = DOMAINS[domain]["tzinfo"]
    # ZoneInfo is supposed to get this right at instanciation
    sts = datetime(
        dt.year,
        dt.month,
        dt.day,
        local_hour,
        tzinfo=tzinfo,
    )
    date2 = date(dt.year, dt.month, dt.day) + timedelta(days=1)
    ets = datetime(
        date2.year,
        date2.month,
        date2.day,
        local_hour,
        tzinfo=tzinfo,
    )
    return (sts.astimezone(UTC), ets.astimezone(UTC))


def iemre_bounds_check(clidf: pd.DataFrame, col: str, lower, upper) -> None:
    """Make sure our data is within bounds, if not, exit!"""
    if clidf[col].min() < lower or clidf[col].max() > upper:
        LOG.warning(
            "FATAL: iemre failure %s %.3f to %.3f [%.3f to %.3f]",
            col,
            clidf[col].min(),
            clidf[col].max(),
            lower,
            upper,
        )
        raise CLIFileWorkflowFailure("IEMRE data out of bounds!")


def load_iemre(clidf: pd.DataFrame, domain: str, valid: date) -> None:
    """Use IEM Reanalysis for non-precip data

    1/8 degree product is nearest neighbor resampled to the 0.01 degree grid
    """
    ds = get_grids(
        valid,
        varnames=["high_tmpk", "low_tmpk", "avg_dwpk", "wind_speed", "rsds"],
        domain=domain,
    )
    highc = convert_value(ds["high_tmpk"], "degK", "degC")
    lowc = convert_value(ds["low_tmpk"], "degK", "degC")
    dwpc = convert_value(ds["avg_dwpk"], "degK", "degC")
    nav = get_nav("IEMRE", domain)
    for idx, row in clidf.iterrows():
        i, j = nav.find_ij(row["lon"], row["lat"])
        # Convert W m-2 to langleys per day
        clidf.at[idx, "solar"] = ds["rsds"][j, i] * 86400 / 1_000_000.0 * 23.9
        clidf.at[idx, "high"] = highc[j, i]
        clidf.at[idx, "low"] = lowc[j, i]
        clidf.at[idx, "dwpt"] = dwpc[j, i]
        clidf.at[idx, "wind"] = ds["wind_speed"][j, i]

    # What's a reasonable max bounts?  Well, 50 MJ/d should be an extreme high
    iemre_bounds_check(clidf, "solar", 0, 50.0 * 23.9)
    iemre_bounds_check(clidf, "high", -60, 60)
    iemre_bounds_check(clidf, "low", -60, 60)
    iemre_bounds_check(clidf, "dwpt", -60, 60)
    iemre_bounds_check(clidf, "wind", 0, 40)


def load_stage4(data, dt: date, tile_affine: Affine):
    """It sucks, but we need to load the stage IV data to give us something
    to benchmark the MRMS data against, to account for two things:
    1) Wind Farms
    2) Over-estimates
    """
    LOG.debug("called")
    # The stage4 files store precip in the rears, so compute 1 AM
    one_am, tomorrow = get_sts_ets_at_localhour("", dt, 1)

    sts_tidx = hourly_offset(one_am)
    ets_tidx = hourly_offset(tomorrow)
    LOG.debug(
        "stage4 sts_tidx:%s[%s] ets_tidx:%s[%s]",
        sts_tidx,
        one_am,
        ets_tidx,
        tomorrow,
    )
    ncfn = f"{ST4PATH}/{dt:%Y}_stage4_hourly.nc"
    if not os.path.isfile(ncfn):
        msg = f"Stage IV file {ncfn} does not exist, aborting workflow..."
        LOG.warning(msg)
        raise CLIFileWorkflowFailure(msg)

    with ncopen(ncfn, "r") as nc:
        p01m = nc.variables["p01m"]

        # crossing jan 1
        if ets_tidx < sts_tidx:
            LOG.debug("Exercise special stageIV logic for jan1!")
            totals = np.sum(p01m[sts_tidx:], axis=0)
            with ncopen(f"{ST4PATH}/{tomorrow.year}_stage4_hourly.nc") as nc2:
                p01m = nc2.variables["p01m"]
                totals += np.sum(p01m[:ets_tidx], axis=0)
        else:
            totals = np.sum(p01m[sts_tidx:ets_tidx], axis=0)

    if np.ma.max(totals) > 0:
        pass
    else:
        LOG.warning("No StageIV data found, aborting...")
        raise CLIFileWorkflowFailure("No Stage IV data found, aborting...")
    # set a small non-zero number to keep things non-zero
    totals[totals < 0.001] = 0.001

    reproject(
        totals.filled(np.nan),  # rasterio does not like masked arrays
        data["stage4"],
        src_transform=STAGE4.affine,
        src_crs=STAGE4.crs,
        dst_transform=tile_affine,
        dst_crs="EPSG:4326",
    )
    LOG.debug("finished")


def qc_precip(data, dt: date, tile_affine: Affine):
    """Make some adjustments to the `precip` grid

    Not very sophisticated here, if the hires precip grid is within 33% of
    Stage IV, then we consider it good.  If not, then we apply a multiplier to
    bring it to near the stage IV value.
    """
    hires_total = np.sum(data["precip"], 2)
    # Only do this check for tiles west of -101, likely too crude for east
    if dt.year >= 2015 and tile_affine.c < -101:
        # Do an assessment of the hires_total (A2M MRMS), it may have too many
        # zeros where stage IV has actual data.
        a2m_zeros = hires_total < 0.01
        s4 = data["stage4"] > 5  # arb
        score = np.sum(np.logical_and(a2m_zeros, s4)) / np.multiply(*s4.shape)
        if score > 0.005:  # 0.5% is arb, but good enough?
            LOG.warning("MRMS had %.2f%% bad zeros, using legacy", score * 100)
            load_precip_legacy(data, dt, tile_affine)
            hires_total = np.sum(data["precip"], 2)

    # prevent zeros
    hires_total[hires_total < 0.01] = 0.01
    multiplier = data["stage4"] / hires_total

    # Anything close to 1, set it to 1
    multiplier = np.where(
        np.logical_and(multiplier > 0.67, multiplier < 1.33), 1.0, multiplier
    )
    data["precip"][:] *= multiplier[:, :, None]
    data["precip"][np.isnan(data["precip"])] = 0.0


def _reader(utcnow: datetime, tidx, shp, west: float, south: float):
    """Read the legacy N0R data"""
    ppath = utcnow.strftime("%Y/%m/%d/GIS/uscomp/n0r_%Y%m%d%H%M.png")
    x0 = int((west + 126.0) * 100)
    ny, nx = shp
    north = south + (ny + 1) * 0.01  # meh
    y0 = int((50.0 - north) * 100)
    with archive_fetch(ppath) as fn:
        if fn is None:
            return None, None
        # upper right corner is 50N, 126W
        with gdal.Open(fn, 0) as ds:
            # Get the size of the raster so that we don't go out of bounds
            imgshp = ds.RasterYSize, ds.RasterXSize
            y1 = min(imgshp[0] - y0, ny)
            x1 = min(imgshp[1] - x0, nx)
            imgdata = ds.ReadAsArray(
                xoff=x0, yoff=y0, xsize=x1, ysize=y1
            ).astype(np.float32)
        # Convert the image data to dbz
        dbz = (imgdata - 7.0) * 5.0
        dbz = np.where(dbz < 255, ((10.0 ** (dbz / 10.0)) / 200.0) ** 0.625, 0)
    return tidx, np.flipud(dbz)


def load_precip_legacy(data, valid, tile_affine: Affine):
    """Compute a Legacy Precip product for dates prior to 1 Jan 2014"""
    LOG.info("called")
    ts = 12 * 24  # 5 minute

    midnight, tomorrow = get_sts_ets_at_localhour("", valid, 0)

    now = midnight
    # To avoid division by zero below when we have the strip of no-data 23-24N
    m5 = np.ones((ts, *data["stage4"].shape), np.float32) * 0.01

    def _cb_pl(args):
        """callback"""
        tidx, precip = args
        # Ensure that tidx is within bounds
        if tidx is None or tidx >= m5.shape[0]:
            return
        if precip is not None:
            # sigh
            if precip.shape[0] == 401:
                m5[tidx, 99:, :] = precip
            elif precip.shape[0] == 201:
                m5[tidx, :201, :] = precip
            elif m5[tidx].shape != precip.shape:
                LOG.warning(
                    "m5[%s].shape %s != precip.shape %s",
                    tidx,
                    m5[tidx].shape,
                    precip.shape,
                )
            else:
                m5[tidx] = precip

    tidx = 0
    shp = data["stage4"].shape
    with ThreadPool(CPUCOUNT) as pool:
        # Load up the n0r data, every 5 minutes
        while now < tomorrow:
            if tidx >= ts:
                # Abort as we are in CST->CDT
                break
            pool.apply_async(
                _reader,
                (
                    now.astimezone(UTC),
                    tidx,
                    shp,
                    tile_affine.c,
                    tile_affine.f,
                ),
                callback=_cb_pl,
                error_callback=LOG.error,
            )
            now += timedelta(minutes=5)
            tidx += 1
        pool.close()
        pool.join()

    LOG.debug("finished loading N0R Composites")
    m5 = np.transpose(m5, (1, 2, 0)).copy()
    LOG.debug("transposed the data!")
    # Prevent overflow with likely bad data leading to value > np.float32
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

    for x in range(data["stage4"].shape[1]):
        for y in range(data["stage4"].shape[0]):
            _compute(y, x)

    LOG.info("finished precip calculation")


def _mrms_reader(
    utcnow: datetime,
    tidx,
    shp,
    west_edge: float,
    south_edge: float,
    a2m_divisor,
):
    """Read the MRMS data."""
    ppath = utcnow.strftime("%Y/%m/%d/GIS/mrms/a2m_%Y%m%d%H%M.png")
    # MRMS pixels are not centered on 0.01 degree grid, so we are not being
    # the most exact here.
    x0 = int((west_edge + 130.0) * 100)
    ny, nx = shp
    north = south_edge + (ny + 1) * 0.01  # meh
    y0 = int((55.0 - north) * 100)
    with archive_fetch(ppath) as fn:
        if fn is None:
            return None, None
        # Here lie dragons, going from uint8 to float32 uses special CPU
        # so it is much faster to do a small window/exact extraction
        with gdal.Open(fn, 0) as ds:
            imgdata = ds.ReadAsArray(
                xoff=x0, yoff=y0, xsize=nx, ysize=ny
            ).astype(np.float32)
        imgdata = np.where(imgdata < 255, imgdata / a2m_divisor, 0)
    return tidx, np.flipud(imgdata)


def load_imerg(data, domain: str, dt: date, tile_affine: Affine):
    """Load the 30 minute IMERG data."""
    LOG.info("called")
    # IMERG is stored in the rears, so start at 12:30 AM
    midnight, tomorrow = get_sts_ets_at_localhour(domain, dt, 0)
    now = midnight + timedelta(minutes=30)
    # IMERG is stored -180,90 to 180,-90 at 0.1x0.1
    x0 = int((tile_affine.c + 180.0) * 10)
    # DEP storage is 0.01x0.01
    ny, nx, _ = data["precip"].shape
    y0 = int((90.0 - tile_affine.f) * 10)

    tidx = 0
    while now <= tomorrow:
        ppath = now.strftime("%Y/%m/%d/GIS/imerg/p30m_%Y%m%d%H%M.png")
        with archive_fetch(ppath) as fn:
            if fn is not None:
                # idx: 0-200 0.25mm  -> 50 mm
                # idx: 201-253 1mm -> 50-102 mm
                with gdal.Open(fn, 0) as ds:
                    imgdata = np.repeat(
                        np.repeat(
                            ds.ReadAsArray(
                                xoff=x0,
                                yoff=y0,
                                xsize=nx // 10,
                                ysize=ny // 10,
                            ).astype(np.float32),
                            10,
                            axis=0,
                        ),
                        10,
                        axis=1,
                    )
                data["precip"][:, :, tidx] = np.flipud(
                    np.where(imgdata < 201, imgdata * 0.25, imgdata - 150)
                )
            else:
                LOG.warning(
                    "IMERG file %s does not exist, using zeros",
                    ppath,
                )
        tidx += 1
        now += timedelta(minutes=30)


def load_precip(data, dt: date, tile_affine: Affine):
    """Load the 2 minute precipitation data into our ginormus grid"""
    LOG.info("called")
    ts = 30 * 24  # 2 minute

    midnight, tomorrow = get_sts_ets_at_localhour("", dt, 0)

    # Oopsy we discovered a problem
    a2m_divisor = 10.0 if (dt < date(2015, 1, 1)) else 50.0

    now = midnight
    # Require at least 75% data coverage, if not, we will abort back to legacy
    quorum = {"cnt": ts * 0.75}

    def _cb_lp(args):
        """callback"""
        tidx, grid = args
        # If tidx is outside of bounds, just make this a no-op
        if grid is not None and tidx < data["precip"].shape[2]:
            data["precip"][:, :, tidx] = grid
            quorum["cnt"] -= 1

    tidx = 0
    shp = data["stage4"].shape
    with ThreadPool(CPUCOUNT) as pool:
        while now < tomorrow:
            pool.apply_async(
                _mrms_reader,
                (
                    now.astimezone(UTC),
                    tidx,
                    shp,
                    tile_affine.c,
                    tile_affine.f,
                    a2m_divisor,
                ),
                callback=_cb_lp,
                error_callback=LOG.error,
            )
            now += timedelta(minutes=2)
            tidx += 1
        pool.close()
        pool.join()
    if quorum["cnt"] > 0:
        LOG.warning(
            "Failed 75%% quorum with MRMS a2m %.1f, loading legacy",
            quorum["cnt"],
        )
        load_precip_legacy(data, dt, tile_affine)
    LOG.info("finished precip calculation")


def bpstr(ts, accum):
    """Make a string representation of this breakpoint and accumulation"""
    # Need four decimals for accurate reproduction
    return f"{ts.hour:02.0f}.{(ts.minute / 60.0 * 10000.0):04.0f} {accum:.2f}"


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
    dt = 2 if len(ar) > 100 else 30
    for i, intensity in enumerate(ar):
        if intensity < 0.001:
            continue
        # Need to initialize the breakpoint data
        if bp is None:
            ts = ZEROHOUR + timedelta(minutes=i * dt)
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
                ts = ZEROHOUR + timedelta(minutes=(i + 1) * dt)
            bp.append(bpstr(ts, accum))
    # To append a last accumulation, we need to have something meaningful
    # so to not have redundant values, which bombs WEPP
    if accum - lastaccum > 0.02:
        if (lasti + 1) == len(ar):
            ts = ZEROHOUR.replace(hour=23, minute=59)
        else:
            ts = ZEROHOUR + timedelta(minutes=(lasti + 1) * dt)
        bp.append(bpstr(ts, accum))
    return bp


def write_grid(
    domain: str, grid: np.ndarray, valid, tile_affine: Affine, fnadd=""
):
    """Save off the daily precip totals for usage later in computing huc_12"""
    if fnadd != "" and not sys.stdout.isatty():
        LOG.debug("not writting extra grid to disk")
        return
    basedir = f"/mnt/idep2/data/dailyprecip/{valid.year}"
    if domain != "":
        basedir = f"/mnt/dep/{domain}/data/dailyprecip/{valid.year}"
    if not os.path.isdir(basedir):
        os.makedirs(basedir)
    lat_prefix = "N" if tile_affine.f > 0 else "S"
    lon_prefix = "E" if tile_affine.c > 0 else "W"
    fn = (
        f"{basedir}/{valid:%Y%m%d}{fnadd}."
        f"tile_{lon_prefix}{abs(tile_affine.c):.0f}_"
        f"{lat_prefix}{abs(tile_affine.f):.0f}.geotiff"
    )
    with rasterio.open(
        fn,
        "w",
        driver="GTiff",
        height=grid.shape[0],
        width=grid.shape[1],
        count=1,
        dtype=grid.dtype,
        crs="EPSG:4326",
        transform=tile_affine,
    ) as dst:
        dst.write(grid, 1)


def precip_workflow(domain: str, data, valid, tile_affine: Affine):
    """Drive the precipitation workflow"""
    if domain == "":
        load_stage4(data, valid, tile_affine)
        # We have MRMS a2m RASTER files prior to 1 Jan 2015, but these files
        # used a very poor choice of data interval of 0.1mm, which is not
        # large enough to capture low intensity events.  Files after 1 Jan 2015
        # used a better 0.02mm resolution
        if valid.year < 2015:
            load_precip_legacy(data, valid, tile_affine)
        else:
            load_precip(data, valid, tile_affine)
        qc_precip(data, valid, tile_affine)
    else:
        load_imerg(data, domain, valid, tile_affine)


def edit_clifile(
    clirow: dict,
    xidx: int,
    yidx: int,
    data: dict[str, np.ndarray],
    valid: date,
) -> bool:
    """Edit the climate file, run from thread."""
    # Okay we have work to do
    with open(clirow["filepath"], "r", encoding="utf8") as fh:  # skipcq
        clidata = fh.read()
    pos = clidata.find(valid.strftime("%-d\t%-m\t%Y"))
    if pos == -1:
        LOG.warning("Date find failure for %s", clirow["filepath"])
        return False

    pos2 = clidata[pos:].find(
        (valid + timedelta(days=1)).strftime("%-d\t%-m\t%Y")
    )
    if pos2 == -1:
        LOG.warning("Date2 find failure for %s", clirow["filepath"])
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

    high = clirow["high"]
    low = clirow["low"]
    solar = clirow["solar"]
    wind = clirow["wind"]
    dwpt = clirow["dwpt"]
    if np.isnan([high, low, solar, wind, dwpt]).any():
        msg = []
        for v, n in zip(
            [high, low, solar, wind, dwpt],
            "hi lo sol wnd dpt".split(),
            strict=False,
        ):
            if np.isnan(v):
                msg.append(f"{n}={v}")
        LOG.warning(
            "Missing data[%s] for %s", ",".join(msg), clirow["filepath"]
        )
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

    with open(clirow["filepath"], "w", encoding="utf8") as fh:
        fh.write(clidata[:pos] + thisday + clidata[(pos + pos2) :])
    return True


def daily_editor_workflow(
    scenario: int,
    domain: str,
    dt: date,
    west: int,
    east: int,
    south: int,
    north: int,
) -> Optional[int]:
    """Do daily processing work.

    Args:
        scenario (int): DEP Scenario ID
        domain (str): Domain name
        dt (date): Date to edit
        west (int): West grid point (inclusive center point)
        east (int): East grid point (exclusive center point)
        south (int): South grid point (inclusive center point)
        north (int): North grid point (exclusive center point)
    """
    # Create a grid navigation object
    tilenav = CartesianGridNavigation(
        left_edge=west - GRID_SPACING / 2.0,
        bottom_edge=south - GRID_SPACING / 2.0,
        nx=int((east - west) / GRID_SPACING),
        ny=int((north - south) / GRID_SPACING),
        dx=GRID_SPACING,
        dy=GRID_SPACING,
    )
    clidf = load_clifiles(scenario, domain, tilenav)
    if clidf.empty:
        LOG.info("No climate files found for scenario %s", scenario)
        return 0

    # This is the outer edge of the grid and our west/south pts are inclusive
    # the grid is oriented from south to north (positive dy)
    tile_affine = tilenav.affine

    # Fill out clidf with IEMRE values
    # 1. Max Temp C
    # 2. Min Temp C
    # 3. Radiation l/d
    # 4. wind mps
    # 6. Mean dewpoint C
    load_iemre(clidf, domain, dt)

    shp = (int((north - south) * 100), int((east - west) * 100))
    data = {
        "stage4": np.zeros(shp, np.float32),
        # CONUS is 2 minute, everybody else is 30 minute, for now
        "precip": np.zeros(
            (*shp, (30 if domain == "" else 2) * 24), np.float32
        ),
    }

    # 5. wind direction (always zero)
    # 7. breakpoint precip mm
    precip_workflow(domain, data, dt, tile_affine)
    if domain == "":
        write_grid(domain, data["stage4"], dt, tile_affine, fnadd="stage4")
    write_grid(domain, np.sum(data["precip"], 2), dt, tile_affine)

    progress = tqdm(total=len(clidf), disable=not sys.stdout.isatty())
    errors = {"cnt": 0}

    with ThreadPool(CPUCOUNT) as pool:

        def _callback(res):
            """We got a result."""
            if not res:
                errors["cnt"] += 1
            progress.update(1)

        def _proxy(clirow: dict, data, valid):
            """Proxy."""
            if errors["cnt"] > 10:
                return False
            clifn = clirow["filepath"]
            xidx = int((clirow["lon"] - west) * 100)
            yidx = int((clirow["lat"] - south) * 100)
            # Ensure that our indices are within bounds
            if xidx < 0 or xidx >= shp[1] or yidx < 0 or yidx >= shp[0]:
                LOG.warning(
                    "clifile %s out of bounds x:%s[0-%s] y:%s[0-%s]",
                    clifn,
                    xidx,
                    shp[1],
                    yidx,
                    shp[0],
                )
                return False
            try:
                return edit_clifile(clirow, xidx, yidx, data, valid)
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

        for _, row in clidf.iterrows():
            if not os.path.isfile(row["filepath"]):
                continue

            pool.apply_async(
                _proxy,
                (row.to_dict(), data, dt),
                callback=_callback,
                error_callback=LOG.error,
            )
        pool.close()
        pool.join()

    LOG.info("Finished with %s errors", errors["cnt"])
    return 0
