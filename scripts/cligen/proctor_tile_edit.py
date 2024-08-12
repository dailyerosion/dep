"""Proctor the editing of DEP CLI files."""

import gzip
import os
import stat
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from multiprocessing import cpu_count

import click
import numpy as np
from pyiem.iemre import EAST, NORTH, SOUTH, WEST
from pyiem.util import logger

LOG = logger()
DATADIR = "/mnt/idep2/data/dailyprecip"


def get_fn(dt: date):
    """Return the filename for this date."""
    return f"{DATADIR}/{dt.year}/{dt:%Y%m%d}.npy.gz"


def assemble_grids(tilesz, dt: date):
    """Build back the grid from the tiles."""
    YS = int((NORTH - SOUTH) * 100.0)
    XS = int((EAST - WEST) * 100.0)
    res = np.zeros((YS, XS))
    basedir = f"{DATADIR}/{dt.year}"
    for i, _lon in enumerate(np.arange(WEST, EAST, tilesz)):
        for j, _lat in enumerate(np.arange(SOUTH, NORTH, tilesz)):
            fn = f"{basedir}/{dt:%Y%m%d}.tile_{i}_{j}.npy"
            if not os.path.isfile(fn):
                continue
            yslice = slice(j * 100 * tilesz, (j + 1) * 100 * tilesz)
            xslice = slice(i * 100 * tilesz, (i + 1) * 100 * tilesz)
            res[yslice, xslice] = np.load(fn)
            os.unlink(fn)

    with gzip.GzipFile(get_fn(dt), "w") as fh:
        np.save(file=fh, arr=res)


def myjob(cmd):
    """Run this command and return any result."""
    proc = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = proc.communicate()
    if stdout != b"" or stderr != b"":
        LOG.warning(
            "CMD: %s\nSTDOUT: %s\nSTDERR: %s",
            cmd,
            stdout.decode("ascii", "ignore").strip(),
            stderr.decode("ascii", "ignore").strip(),
        )
    return proc.returncode


@click.command()
@click.option("--scenario", "-s", type=int, default=0, help="Scenario")
@click.option("--date", "dt", type=click.DateTime(), help="Date to process")
def main(scenario, dt):
    """Go Main Go."""
    tilesz = 5
    dt = dt.date()
    fn = get_fn(dt)
    if os.path.isfile(fn):
        filets = os.stat(fn)[stat.ST_MTIME]
        LOG.warning("%s was last processed on %s", dt, time.ctime(filets))
    jobs = []
    for i, _lon in enumerate(np.arange(WEST, EAST, tilesz)):
        for j, _lat in enumerate(np.arange(SOUTH, NORTH, tilesz)):
            cmd = (
                f"python daily_clifile_editor.py {i} {j} {tilesz} "
                f"{scenario} {dt:%Y %m %d}"
            )
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

    assemble_grids(tilesz, dt)


if __name__ == "__main__":
    main()
