"""When DEP expands, we have a problem that we have no close by precip files.

So lets ensure we have one file per 0.25 degree lat and lon, we can then use
these to fast-start newly expanded areas...
"""
from pyiem.dep import SOUTH, EAST, NORTH, WEST
import numpy as np
import os
import shutil

# We shall use this file, no mater what
SRC = "/i/0/cli/095x038/095.17x038.13.cli"
SCENARIO = 0

created = 0
for lon in np.arange(WEST, EAST, 0.05):
    for lat in np.arange(SOUTH, NORTH, 0.05):
        if (("%.2f" % (lon,)).endswith(".25") and
                ("%.2f" % (lat,)).endswith(".25")):
            mydir = "/i/%s/cli/%03.0fx%03.0f" % (SCENARIO, 0 - lon, lat)
            if not os.path.isdir(mydir):
                os.makedirs(mydir)
            fn = "%s/%06.2fx%06.2f.cli" % (mydir, 0 - lon, lat)
            if not os.path.isfile(fn):
                created += 1
                shutil.copyfile(SRC, fn)

print("We just created %s new files!" % (created,))
