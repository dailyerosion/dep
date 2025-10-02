"""Collate up the myhucs.txt data."""

import os
import tarfile
from pathlib import Path

import click
from pyiem.util import logger
from tqdm import tqdm

LOG = logger()


@click.command()
@click.option("--scenario", "-s", type=int, required=True, help="Scenario ID")
def main(scenario: int):
    """Go main Go."""
    myhucs = [s.strip() for s in open("myhucs.txt")]
    LOG.info("Packaging %s huc12s for delivery", len(myhucs))

    scenario_dir = Path(f"/i/{scenario}")
    os.chdir(scenario_dir)

    tar_path = scenario_dir / "dep.tar"
    if tar_path.exists():
        LOG.info("removed old dep.tar file")
        tar_path.unlink()

    # Collect all files to add to the archive first
    files_to_add = []
    directories = ["man", "prj", "rot", "slp", "sol", "meta"]

    for huc in tqdm(myhucs, desc="Collecting files"):
        huc8 = huc[:8]
        huc4 = huc[8:]

        for directory in directories:
            dir_path = scenario_dir / directory / huc8 / huc4
            if dir_path.exists():
                # Add all files in this directory
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        # Calculate archive path relative to scenario directory
                        arcname = file_path.relative_to(scenario_dir)
                        files_to_add.append((file_path, arcname))

    LOG.info("Adding %s files to tar archive", len(files_to_add))

    # Create the tar archive and add all files at once
    with tarfile.open(tar_path, "w") as tar:
        for file_path, arcname in tqdm(files_to_add, desc="Adding to tar"):
            tar.add(file_path, arcname=str(arcname))


if __name__ == "__main__":
    main()
