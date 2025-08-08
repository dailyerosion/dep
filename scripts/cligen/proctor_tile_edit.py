"""Proctor the editing of DEP CLI files."""

import glob
import os
import stat
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime
from math import ceil, floor
from multiprocessing import cpu_count

import click
import numpy as np
import rasterio
from affine import Affine
from pyiem.grid.nav import get_nav
from pyiem.util import logger

from pydep.workflows.clifile import (
    CLIFileWorkflowFailure,
    daily_editor_workflow,
)

LOG = logger()


@dataclass
class Tile:
    """Tile information."""

    west: float
    east: float
    south: float
    north: float
    scenario: int
    dt: date
    domain: str


def get_fn(dt: date, domain: str) -> str:
    """Return the filename for this date."""
    if domain == "":
        return f"/mnt/idep2/data/dailyprecip/{dt.year}/{dt:%Y%m%d}.geotiff"
    return f"/mnt/dep/{domain}/data/dailyprecip/{dt.year}/{dt:%Y%m%d}.geotiff"


def assemble_geotiffs(dt: date, domain: str):
    """Build back the grid from the tiles.

    Important: The tiles are S-N, but we flip and store as N-S (image)
    """
    geodir = os.path.dirname(get_fn(dt, domain))
    nav = get_nav("IEMRE", domain)
    north = ceil(nav.top_edge)
    east = ceil(nav.right)
    south = floor(nav.bottom)
    west = floor(nav.left)
    YS = int((north - south) * 100.0)
    XS = int((east - west) * 100.0)
    res = np.zeros((YS, XS))
    for gfn in glob.glob(f"{geodir}/{dt:%Y%m%d}.tile*.geotiff"):
        with rasterio.open(gfn) as src:
            data = src.read(1)
            meta = src.meta
            # The raster is stored south to north and has the small offset
            height = meta["height"]
            width = meta["width"]
            xs = int((meta["transform"][2] + 0.005 - west) * 100.0)
            ys = int((meta["transform"][5] + 0.005 - south) * 100.0)
            LOG.info(
                "%s %s %s %s %s %s %s",
                gfn,
                xs,
                ys,
                width,
                height,
                data.shape,
                res.shape,
            )
            res[ys : ys + height, xs : xs + width] = data
            os.unlink(gfn)

    # Write out a GeoTIFF, we will store as a UInt16 with a scale factor
    # of 100, so we can store 0 to 655.35 mm of precipitation
    res = (res * 100.0).astype(np.uint16)
    with rasterio.open(
        get_fn(dt, domain),
        "w",
        driver="GTiff",
        compress="lzw",
        height=res.shape[0],
        width=res.shape[1],
        count=1,
        dtype=res.dtype,
        crs="EPSG:4326",
        # Oh boy. We never actually get to the north edge
        transform=Affine(0.01, 0.0, west - 0.005, 0.0, -0.01, north - 0.005),
    ) as dst:
        dst._set_all_scales([0.01])  # skipcq
        dst._set_all_offsets([0.0])  # skipcq
        dst.write(np.flipud(res), 1)


def myjob(tile: Tile) -> list[bool, int, int]:
    """Run this command and return any result."""
    try:
        return daily_editor_workflow(
            tile.scenario,
            tile.domain,
            tile.dt,
            tile.west,
            tile.east,
            tile.south,
            tile.north,
        )
    except CLIFileWorkflowFailure as exp:
        LOG.error(
            "CLIFileWorkflowFailure %s: %s",
            tile,
            exp,
        )
    except Exception as exp:
        LOG.error(
            "Tile %s generated unexpected exception: %s",
            tile,
            exp,
        )
        # Log the exception and full stack trace
        traceback.print_exc()
    return False, 0, 0


@click.command()
@click.option("--scenario", "-s", type=int, default=0, help="Scenario")
@click.option(
    "--date",
    "dt",
    type=click.DateTime(),
    help="Date to process",
    required=True,
)
@click.option(
    "--domain",
    type=str,
    default="",
    help="Domain to process",
)
def main(scenario, dt: datetime, domain: str):
    """Go Main Go."""
    tilesz = 5
    dt = dt.date()
    fn = get_fn(dt, domain)
    if os.path.isfile(fn):
        filets = os.stat(fn)[stat.ST_MTIME]
        LOG.warning(
            "%s[%s] was last processed on %s", dt, domain, time.ctime(filets)
        )
    jobs: list[Tile] = []
    # This is more convoluted than it should be, but our IEMRE grid is not
    # exactly even. This also needs to assume that the IEMRE corner is an int
    nav = get_nav("IEMRE", domain)
    east = ceil(nav.right)
    north = ceil(nav.top)
    west = floor(nav.left)
    south = floor(nav.bottom)
    for lon in np.arange(west, east, tilesz):
        for lat in np.arange(south, north, tilesz):
            jobs.append(
                Tile(
                    west=lon,
                    east=round(min(east, lon + tilesz), 0),
                    south=lat,
                    north=round(min(north, lat + tilesz), 0),
                    scenario=scenario,
                    dt=dt,
                    domain=domain,
                )
            )
    failed = 0
    # 12 Nov 2021 audit shows per process usage in the 2-3 GB range
    workers = int(min([4, cpu_count() / 4]))
    LOG.info("starting %s workers", workers)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for res in executor.map(myjob, jobs):
            if not res[0]:
                failed += 1
    if failed > 0:
        LOG.warning("Exiting with status 3 due to %s failure(s)", failed)
        sys.exit(3)
    assemble_geotiffs(dt, domain)


if __name__ == "__main__":
    main()
