""" Setup the necessary directory structure, so that other codes need not """
import os
import sys

from pyiem.util import get_dbconn, logger
from pyiem.dep import load_scenarios

LOG = logger()
PREFIXES = "crop env man prj run slp sol wb error ofe yld".split()


def do_huc12(scenario, huc12):
    """ Directory creator! """
    created = 0
    for prefix in PREFIXES:
        newdir = "/i/%s/%s/%s/%s" % (scenario, prefix, huc12[:8], huc12[8:])
        if not os.path.isdir(newdir):
            created += 1
            os.makedirs(newdir)
    return created


def main(argv):
    """Do Main"""
    scenario = int(argv[1])
    sdf = load_scenarios()
    # Go Main Go
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()
    cursor.execute(
        """
        SELECT distinct huc_12 from flowpaths
        WHERE scenario = %s
    """,
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
    main(sys.argv)
