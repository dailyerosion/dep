import os
import sys

from pyiem.util import get_dbconn
from pyiem.dep import get_cli_fname


def finder(lon, lat):
    for deltax in range(25):
       for multi in [-1 * deltax, 1 * deltax]:
           for multi2 in [-1 * deltax, 1 * deltax]:
               newlon = lon - multi * deltax / 100.
               newlat = lat - multi2 * deltax / 100.
               newfn = get_cli_fname(newlon, newlat)
               if os.path.isfile(newfn):
                   return newfn


def main():
    """Go Main Go."""
    pgconn = get_dbconn('idep')
    cursor = pgconn.cursor()
    cursor.execute("""
        SELECT climate_file, fid from flowpaths where scenario = 0
    """)
    created = 0
    for row in cursor:
        fn = row[0]
        if os.path.isfile(fn):
            continue
        created += 1
        # /i/0/cli/092x041/092.30x041.22.cli
        lon, lat = fn.split("/")[-1][:-4].split("x")
        lon = 0 - float(lon)
        lat = float(lat)
        newfn = finder(lon, lat)
        if newfn is None:
            print("missing %s for fid: %s " % (fn, row[1]))
            sys.exit()
        print("%s -> %s" % (newfn, fn))
        os.system("cp %s %s" % (newfn, fn))
    print("added %s files" % (created, ))


if __name__ == '__main__':
    main()
