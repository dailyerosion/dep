"""When DEP expands, we have a problem that we have no close by precip files.

So lets ensure we have one file per 0.25 degree lat and lon, we can then use
these to fast-start newly expanded areas...
"""
import os
import shutil

import numpy as np
from pyiem.dep import SOUTH, EAST, NORTH, WEST, get_cli_fname


# We shall use this file, no mater what
SRC = "/i/0/cli/095x038/095.17x038.13.cli"
SCENARIO = 0

WANTS = ['.00', '.25', '.50', '.75']
created = 0
for lon in np.arange(WEST, EAST, 0.05):
    for lat in np.arange(SOUTH, NORTH, 0.05):
        if (("%.2f" % (lon,))[-3:] in WANTS and
                ("%.2f" % (lat,))[-3:] in WANTS):
            fn = get_cli_fname(lon, lat, SCENARIO)
            mydir = fn.rsplit("/", 1)[0]
            if not os.path.isdir(mydir):
                os.makedirs(mydir)
            if not os.path.isfile(fn):
                created += 1
                shutil.copyfile(SRC, fn)

print("We just created %s new files!" % (created,))
