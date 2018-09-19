""" Setup the necessary directory structure, so that other codes need not """
import os
import sys

from pyiem.util import get_dbconn

SCENARIO = sys.argv[1]
BASELINESCENARIO = 0 if len(sys.argv) == 2 else sys.argv[2]


PREFIXES = 'env  man  prj  run  slp  sol  wb error ofe yld'.split()


def do_huc12(huc12):
    """ Directory creator! """
    for prefix in PREFIXES:
        newdir = "/i/%s/%s/%s/%s" % (SCENARIO, prefix, huc12[:8], huc12[8:])
        if not os.path.isdir(newdir):
            os.makedirs(newdir)


def main():
    """Do Main"""
    # Go Main Go
    pgconn = get_dbconn('idep')
    cursor = pgconn.cursor()
    cursor.execute("""
        SELECT distinct huc_12 from flowpaths
        WHERE scenario = %s
    """, (BASELINESCENARIO,))
    for row in cursor:
        do_huc12(row[0])


if __name__ == '__main__':
    main()
