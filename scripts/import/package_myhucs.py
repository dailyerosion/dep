"""Collate up the myhucs.txt data."""

import os
import subprocess

import click
from pyiem.util import logger
from tqdm import tqdm

LOG = logger()


@click.command()
@click.option("--scenario", "-s", type=int, required=True, help="Scenario ID")
def main(scenario: int):
    """Go main Go."""
    myhucs = [s.strip() for s in open("myhucs.txt", encoding="utf8")]
    LOG.info("Packaging %s huc12s for delivery", len(myhucs))
    os.chdir(f"/i/{scenario}")
    if os.path.isfile("dep.tar"):
        LOG.info("removed old dep.tar file")
        os.unlink("dep.tar")
    for huc in tqdm(myhucs):
        cmd = (
            f"tar -uf dep.tar {{man,prj,rot,slp,sol,meta}}/{huc[:8]}/{huc[8:]}"
        )
        subprocess.call(cmd, shell=True)


if __name__ == "__main__":
    main()
