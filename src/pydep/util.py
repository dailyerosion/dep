"""pydep helper util methods."""
import math

from pyiem.iemre import SOUTH, WEST, NORTH, EAST


def get_cli_fname(lon, lat, scenario=0):
    """Get the climate file name for the given lon, lat, and scenario"""
    # The trouble here is relying on rounding is problematic, so we just
    # truncate
    lat = round(lat, 2)
    lon = round(lon, 2)
    if lat < SOUTH or lat > NORTH:
        raise ValueError(f"lat: {lat} outside of bounds: {SOUTH} {NORTH}")
    if lon < WEST or lon > EAST:
        raise ValueError(f"lon: {lon} outside of bounds: {WEST} {EAST}")
    return (
        f"/i/{scenario}/cli/{math.floor(0 - lon):03.0f}x"
        f"{math.floor(lat):03.0f}/{(0 - lon):06.2f}x{lat:06.2f}.cli"
    )
