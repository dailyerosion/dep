"""Setup the necessary directory structure, so that other codes need not"""

import os

import click
from pydep.util import load_scenarios
from pyiem.database import get_dbconn
from pyiem.util import logger

LOG = logger()
PREFIXES = (
    "crop env man prj run slp sol wb error ofe yld rot grph out "
    "sweepin sweepout meta"
).split()


def do_huc12(scenario, huc12):
    """Directory creator!"""
    created = 0
    for prefix in PREFIXES:
        newdir = f"/i/{scenario}/{prefix}/{huc12[:8]}/{huc12[8:]}"
        if not os.path.isdir(newdir):
            created += 1
            os.makedirs(newdir)
    return created


@click.command()
@click.option("--scenario", "-s", required=True, type=int)
def main(scenario):
    """Do Main"""
    sdf = load_scenarios()
    # Go Main Go
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()
    cursor.execute(
        "SELECT huc_12 from huc12 WHERE scenario = %s",
        (int(sdf.at[scenario, "huc12_scenario"]),),
    )
    added = 0
    for row in cursor:
        added += do_huc12(scenario, row[0])
    LOG.info(
        "scenario: %s Added %s directories over %s HUC12s",
        scenario,
        added,
        cursor.rowcount,
    )


if __name__ == "__main__":
    main()
