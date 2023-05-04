"""Collate up the myhucs.txt data."""
import os
import subprocess
import sys

from pyiem.util import logger
from tqdm import tqdm

LOG = logger()


def main(argv):
    """Go main Go."""
    scenario = int(argv[1])
    myhucs = [s.strip() for s in open("myhucs.txt", encoding="utf8")]
    LOG.info("Packaging %s huc12s for delivery", len(myhucs))
    os.chdir(f"/i/{scenario}")
    if os.path.isfile("dep.tar"):
        LOG.info("removed old dep.tar file")
        os.unlink("dep.tar")
    for huc in tqdm(myhucs):
        cmd = f"tar -uf dep.tar {{man,slp,sol}}/{huc[:8]}/{huc[8:]}"
        subprocess.call(cmd, shell=True)


if __name__ == "__main__":
    main(sys.argv)
