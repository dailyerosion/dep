"""Find an available precip file after we do expansion."""

import os
import subprocess

import click
import pandas as pd
from pyiem.database import get_sqlalchemy_conn
from pyiem.util import logger
from sqlalchemy import text

from pydep.util import get_cli_fname

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


@click.command()
@click.option("--scenario", "-s", type=int, required=True, help="Scenario ID")
def main(scenario: int):
    """Go Main Go."""
    # Load up the climate_files
    with get_sqlalchemy_conn("idep") as conn:
        clidf = pd.read_sql(
            text("""
    select filepath, st_x(geom) as lon, st_y(geom) as lat
    from climate_files WHERE scenario = :scenario
                 """),
            conn,
            params={"scenario": scenario},
            index_col=None,
        )
    LOG.info("Found %s climate files", len(clidf.index))

    created = 0
    for _, row in clidf.iterrows():
        fn = row["filepath"]
        if os.path.isfile(fn):
            continue
        copyfn, _, _ = finder(row["lon"], row["lat"], scenario)
        if copyfn is None:
            LOG.info("FATAL: Failed to find a file for %s", row["filepath"])
            return
        mydir = os.path.dirname(fn)
        if not os.path.isdir(mydir):
            os.makedirs(mydir)
        LOG.info("Copying %s to %s", copyfn, fn)
        subprocess.call(["cp", copyfn, fn])
        # Now fix the header to match its location
        subprocess.call(["python", "edit_cli_header.py", fn])
        created += 1
    LOG.info("added %s files", created)


if __name__ == "__main__":
    main()
