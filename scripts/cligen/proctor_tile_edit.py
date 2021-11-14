"""Proctor the editing of DEP CLI files.

Usage:
    python proctor_tile_edit.py <scenario> <yyyy> <mm> <dd>
"""
import sys
import os
import stat
import datetime
import subprocess
import time
from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from pyiem.dep import SOUTH, NORTH, EAST, WEST
from pyiem.util import logger

LOG = logger()
DATADIR = "/mnt/idep2/data/dailyprecip"


def get_fn(date):
    """Return the filename for this date."""
    return f"{DATADIR}/{date.year}/{date:%Y%m%d}.npy"


def assemble_grids(tilesz, date):
    """Build back the grid from the tiles."""
    YS = int((NORTH - SOUTH) * 100.0)
    XS = int((EAST - WEST) * 100.0)
    res = np.zeros((YS, XS))
    basedir = f"{DATADIR}/{date.year}"
    for i, _lon in enumerate(np.arange(WEST, EAST, tilesz)):
        for j, _lat in enumerate(np.arange(SOUTH, NORTH, tilesz)):
            fn = f"{basedir}/{date:%Y%m%d}.tile_{i}_{j}.npy"
            if not os.path.isfile(fn):
                continue
            yslice = slice(j * 100 * tilesz, (j + 1) * 100 * tilesz)
            xslice = slice(i * 100 * tilesz, (i + 1) * 100 * tilesz)
            res[yslice, xslice] = np.load(fn)
            os.unlink(fn)

    np.save(get_fn(date), res)


def myjob(cmd):
    """Run this command and return any result."""
    proc = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = proc.communicate()
    if stdout != b"" or stderr != b"":
        LOG.info(
            "CMD: %s\nSTDOUT: %s\nSTDERR: %s",
            cmd,
            stdout.decode("ascii", "ignore").strip(),
            stderr.decode("ascii", "ignore").strip(),
        )
    return proc.returncode


def main(argv):
    """Go Main Go."""
    tilesz = 5
    scenario = argv[1]
    date = datetime.date(int(argv[2]), int(argv[3]), int(argv[4]))
    fn = get_fn(date)
    if os.path.isfile(fn):
        filets = os.stat(fn)[stat.ST_MTIME]
        LOG.info("%s was last processed on %s", date, time.ctime(filets))
    jobs = []
    for i, _lon in enumerate(np.arange(WEST, EAST, tilesz)):
        for j, _lat in enumerate(np.arange(SOUTH, NORTH, tilesz)):
            cmd = (
                f"python daily_clifile_editor.py {i} {j} {tilesz} "
                f"{scenario} {date:%Y %m %d}"
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
                LOG.info("job: %s exited with status code %s", job, res)
    if failed:
        LOG.info("Aborting due to job failures")
        sys.exit(3)

    assemble_grids(tilesz, date)


if __name__ == "__main__":
    main(sys.argv)
