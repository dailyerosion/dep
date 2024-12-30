"""Proctor the editing of DEP CLI files."""

import glob
import os
import stat
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import date, datetime
from math import ceil
from multiprocessing import cpu_count

import click
import numpy as np
import rasterio
from affine import Affine
from pyiem.grid.nav import IEMRE
from pyiem.util import logger

LOG = logger()
DATADIR = "/mnt/idep2/data/dailyprecip"


def get_fn(dt: date):
    """Return the filename for this date."""
    return f"{DATADIR}/{dt.year}/{dt:%Y%m%d}.geotiff"


def assemble_geotiffs(dt: date):
    """Build back the grid from the tiles.

    Important: The tiles are S-N, but we flip and store as N-S (image)
    """
    north = ceil(IEMRE.top_edge)
    YS = int((north - IEMRE.bottom) * 100.0)
    XS = int((ceil(IEMRE.right) - IEMRE.left) * 100.0)
    res = np.zeros((YS, XS))
    for gfn in glob.glob(f"{DATADIR}/{dt:%Y}/{dt:%Y%m%d}.tile*.geotiff"):
        with rasterio.open(gfn) as src:
            data = src.read(1)
            meta = src.meta
            # The raster is stored south to north and has the small offset
            height = meta["height"]
            width = meta["width"]
            xs = int((meta["transform"][2] + 0.005 - IEMRE.left) * 100.0)
            ys = int((meta["transform"][5] + 0.005 - IEMRE.bottom) * 100.0)
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
        get_fn(dt),
        "w",
        driver="GTiff",
        compress="lzw",
        height=res.shape[0],
        width=res.shape[1],
        count=1,
        dtype=res.dtype,
        crs="EPSG:4326",
        # Oh boy. We never actually get to the north edge
        transform=Affine(
            0.01, 0.0, IEMRE.left - 0.005, 0.0, -0.01, north - 0.005
        ),
    ) as dst:
        dst._set_all_scales([0.01])
        dst._set_all_offsets([0.0])
        dst.write(np.flipud(res), 1)


def myjob(cmd: list):
    """Run this command and return any result."""
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = proc.communicate()
    if stdout != b"" or stderr != b"":
        LOG.warning(
            "CMD: %s\nSTDOUT: %s\nSTDERR: %s",
            " ".join(cmd),
            stdout.decode("ascii", "ignore").strip(),
            stderr.decode("ascii", "ignore").strip(),
        )
    return proc.returncode


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
    fn = get_fn(dt)
    if os.path.isfile(fn):
        filets = os.stat(fn)[stat.ST_MTIME]
        LOG.warning("%s was last processed on %s", dt, time.ctime(filets))
    jobs = []
    # This is more convoluted than it should be, but our IEMRE grid is not
    # exactly even. This also needs to assume that the IEMRE corner is an int
    east = ceil(IEMRE.right)
    north = ceil(IEMRE.top)
    for lon in np.arange(IEMRE.left, east, tilesz):
        for lat in np.arange(IEMRE.bottom, north, tilesz):
            cmd = [
                "python",
                "daily_clifile_editor.py",
                f"--west={lon:.0f}",
                f"--east={min(east, lon + tilesz):.0f}",
                f"--south={lat:.0f}",
                f"--north={min(north, lat + tilesz):.0f}",
                f"--scenario={scenario}",
                f"--date={dt:%Y-%m-%d}",
            ]
            jobs.append(cmd)
    failed = False
    # 12 Nov 2021 audit shows per process usage in the 2-3 GB range
    workers = int(min([4, cpu_count() / 4]))
    LOG.debug("starting %s workers", workers)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for job, res in zip(jobs, executor.map(myjob, jobs)):
            if res != 0:
                failed = True
                LOG.warning("job: %s exited with status code %s", job, res)
    if failed:
        LOG.warning("Aborting due to job failures")
        sys.exit(3)

    assemble_geotiffs(dt)


if __name__ == "__main__":
    main()
