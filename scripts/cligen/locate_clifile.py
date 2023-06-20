"""Find an available precip file after we do expansion."""
import os
import subprocess
import sys

from pydep.util import get_cli_fname
from pyiem.util import get_dbconn, logger

LOG = logger()


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


def main(argv):
    """Go Main Go."""
    scenario = 0 if len(argv) == 1 else int(argv[1])
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()
    # This given scenario may use a different climate scenario's files.
    cursor.execute(
        "SELECT climate_scenario from scenarios where id = %s", (scenario,)
    )
    clscenario = cursor.fetchone()[0]
    LOG.info("DEP scenario: %s uses clscenario: %s", scenario, clscenario)

    cursor.execute(
        "SELECT climate_file, fid from flowpaths where scenario = %s",
        (scenario,),
    )
    created = 0
    for row in cursor:
        fn = row[0]
        if fn is None:
            LOG.error("FATAL, found null climate_file, run assign first")
            return
        if os.path.isfile(fn):
            continue
        created += 1
        # /i/0/cli/092x041/092.30x041.22.cli
        lon, lat = fn.split("/")[-1][:-4].split("x")
        lon = 0 - float(lon)
        lat = float(lat)
        copyfn, xoff, yoff = finder(lon, lat, clscenario)
        if copyfn is None:
            LOG.info("missing %s for fid: %s ", fn, row[1])
            sys.exit()
        LOG.info("cp %s %s xoff: %s yoff: %s", copyfn, fn, xoff, yoff)
        mydir = os.path.dirname(fn)
        if not os.path.isdir(mydir):
            os.makedirs(mydir)
        subprocess.call(["cp", copyfn, fn])
        # Now fix the header to match its location
        subprocess.call(["python", "edit_cli_header.py", fn])
    LOG.info("added %s files", created)


if __name__ == "__main__":
    main(sys.argv)
