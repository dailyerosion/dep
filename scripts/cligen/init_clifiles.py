"""When DEP expands, we have a problem that we have no close by precip files.

So lets ensure we have one file per 0.25 degree lat and lon, we can then use
these to fast-start newly expanded areas...
"""
import os
import shutil

import numpy as np
from pyiem.util import get_dbconn
from pyiem.iemre import SOUTH, EAST, NORTH, WEST
from pydep.util import get_cli_fname


def main():
    """Go Main Go."""
    # We shall use this file, no mater what
    SRC = "/i/0/cli/095x038/095.17x038.13.cli"
    SCENARIO = 0
    pgconn = get_dbconn("postgis")
    cursor = pgconn.cursor()

    created = 0
    removed = 0
    for lon in np.arange(WEST, EAST + 0.25, 0.25):
        for lat in np.arange(SOUTH, NORTH + 0.25, 0.25):
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
                shutil.copyfile(SRC, fn)

    print(f"We just created {created} new files, removed {removed} files!")


if __name__ == "__main__":
    main()
