"""Collate up the myhucs.txt data."""
import sys
import os
import subprocess

from pyiem.util import logger
from tqdm import tqdm
LOG = logger()


def main(argv):
    """Go main Go."""
    scenario = int(argv[1])
    myhucs = [s.strip() for s in open('myhucs.txt').readlines()]
    LOG.info("Packaging %s huc12s for delivery", len(myhucs))
    os.chdir("/i/%s" % (scenario, ))
    if os.path.isfile("dep.tar"):
        LOG.info("removed old dep.tar file")
        os.unlink("dep.tar")
    for huc in tqdm(myhucs):
        cmd = "tar -uf dep.tar {man,slp,sol}/%s/%s" % (huc[:8], huc[8:])
        subprocess.call(cmd, shell=True)


if __name__ == '__main__':
    main(sys.argv)
