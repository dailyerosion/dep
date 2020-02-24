"""Find an available precip file after we do expansion."""
import os
import sys

from pyiem.util import get_dbconn
from pyiem.dep import get_cli_fname


def finder(lon, lat):
    """The logic of finding a file."""
    # https://stackoverflow.com/questions/398299/looping-in-a-spiral
    x = y = 0
    dx = 0
    dy = -1
    # points near the domain edge need to seach a bit further than 0.25deg
    X = 40
    Y = 40
    for _ in range(40 ** 2):
        if (-X / 2 < x <= X / 2) and (-Y / 2 < y <= Y / 2):
            newfn = get_cli_fname(lon + x * 0.01, lat + y * 0.01)
            if os.path.isfile(newfn):
                return newfn, x, y
        if x == y or (x < 0 and x == -y) or (x > 0 and x == 1 - y):
            dx, dy = -dy, dx
        x, y = x + dx, y + dy
    return None, None, None


def main(argv):
    """Go Main Go."""
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()
    cursor.execute(
        """
        SELECT climate_file, fid from flowpaths where scenario = %s
    """,
        (0 if len(argv) == 1 else int(argv[1]),),
    )
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
        newfn, xoff, yoff = finder(lon, lat)
        if newfn is None:
            print("missing %s for fid: %s " % (fn, row[1]))
            sys.exit()
        print("%s -> %s xoff: %s yoff: %s" % (newfn, fn, xoff, yoff))
        os.system("cp %s %s" % (newfn, fn))
    print("added %s files" % (created,))


def test_finder():
    """Test what our finder does."""
    finder(-95.0, 42.0)
    assert False


if __name__ == "__main__":
    main(sys.argv)
