"""When DEP expands, we have a problem that we have no close by precip files.

So lets ensure we have one file per 0.1 degree lat and lon, we can then use
these to fast-start newly expanded areas...
"""

import os
import shutil
import subprocess

import numpy as np
from pyiem.iemre import EAST, NORTH, SOUTH, WEST
from pyiem.util import get_dbconn

from pydep.util import get_cli_fname


def finder(lon, lat, clscenario):
    """The logic of finding a file."""
    # https://stackoverflow.com/questions/398299/looping-in-a-spiral
    x = y = 0
    dx = 0
    dy = -1
    # points near the domain edge need to seach a bit further than 0.25deg
    X = 40
    Y = 40
    for _ in range(40**2):
        if (-X / 2 < x <= X / 2) and (-Y / 2 < y <= Y / 2):
            newfn = get_cli_fname(lon + x * 0.01, lat + y * 0.01, clscenario)
            if os.path.isfile(newfn):
                return newfn, x, y
        if x == y or (x < 0 and x == -y) or (x > 0 and x == 1 - y):
            dx, dy = -dy, dx
        x, y = x + dx, y + dy
    return None, None, None


def main():
    """Go Main Go."""
    # We shall use this file, no mater what
    SCENARIO = 0
    pgconn = get_dbconn("postgis")
    cursor = pgconn.cursor()

    created = 0
    removed = 0
    for lon in np.arange(WEST, EAST + 0.1, 0.1):
        for lat in np.arange(SOUTH, NORTH + 0.1, 0.1):
            fn = get_cli_fname(lon, lat, SCENARIO)
            # Ensure this point is on land, in CONUS
            cursor.execute(
                """
                SELECT ugc from ugcs where
                ST_Contains(geom, ST_GeomFromText('Point(%s %s)',4326))
                and substr(ugc, 3, 1) = 'C' and end_ts is null
            """,
                (lon, lat),
            )
            if cursor.rowcount == 0:
                if os.path.isfile(fn):
                    print(f"Hmmm {fn} is not onland, but has file?")
                    removed += 1
                continue
            mydir = fn.rsplit("/", 1)[0]
            if not os.path.isdir(mydir):
                os.makedirs(mydir)
            if not os.path.isfile(fn):
                created += 1
                src, _, _ = finder(lon, lat, 0)
                if src is not None:
                    print(f"{src} -> {fn}")
                    shutil.copyfile(src, fn)
                    subprocess.call(["python", "edit_cli_header.py", fn])

    print(f"We just created {created} new files, removed {removed} files!")


if __name__ == "__main__":
    main()
