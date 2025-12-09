"""DEP/WEPP Climate File Helpers."""
# pylint: disable=too-many-arguments

import os
from collections import namedtuple

import numpy as np
from pyiem import iemre

# Definition of some bounds for processing
BOUNDS = namedtuple("Bounds", ["south", "north", "east", "west"])
# Climate File Tile Size (in degrees)
CLIMATE_TILE_SIZE = 5


def check_has_clifiles(bounds: BOUNDS):
    """Check that a directory exists, which likely indicates clifiles exist."""
    for lon in np.arange(bounds.west, bounds.east, 1):
        for lat in np.arange(bounds.south, bounds.north, 1):
            ckdir = f"/i/0/cli/{(0 - lon):03.0f}x{(lat):03.0f}"
            if os.path.isdir(ckdir):
                return True
    return False


def compute_tile_bounds(xtile, ytile, domain="conus") -> BOUNDS:
    """Return a BOUNDS namedtuple."""
    dom = iemre.DOMAINS[domain]
    south = dom["south"] + ytile * CLIMATE_TILE_SIZE
    west = dom["west"] + xtile * CLIMATE_TILE_SIZE
    return BOUNDS(
        south=south,
        north=min([south + CLIMATE_TILE_SIZE, dom["north"]]),
        west=west,
        east=min([west + CLIMATE_TILE_SIZE, dom["east"]]),
    )


def daily_formatter(valid, bpdata, high, low, solar, wind, dwpt) -> str:
    """Generate string formatting the given data.

    This includes a trailing line feed.
    """
    bptext = "\n".join(bpdata)
    bptext2 = "\n" if bpdata else ""
    # https://peps.python.org/pep-0682/
    # Need to prevent the string -0.0 from appearing, so hackishness ensues
    return (
        f"{valid.day}\t{valid.month}\t{valid.year}\t{len(bpdata)}\t"
        f"{round(high, 1) + 0.0:.1f}\t{round(low, 1) + 0.0:.1f}\t"
        f"{solar:.0f}\t{wind:.1f}\t0\t{round(dwpt, 1) + 0.0:.1f}\n"
        f"{bptext}{bptext2}"
    )
