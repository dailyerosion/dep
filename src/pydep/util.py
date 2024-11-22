"""pydep helper util methods."""

import math
from typing import Tuple

import numpy as np
import pandas as pd
from pyiem.database import get_sqlalchemy_conn
from pyiem.iemre import EAST, NORTH, SOUTH, WEST
from sqlalchemy import text

from pydep.reference import KWFACT_CLASSES, SLOPE_CLASSES


def get_kwfact_class(kwfact: float) -> int:
    """Get kwfact class for the given kwfact."""
    return np.digitize(kwfact, KWFACT_CLASSES, right=True)


def get_slope_class(slope: float) -> int:
    """Get slope class for the given slope."""
    return np.digitize(slope, SLOPE_CLASSES, right=True)


def clear_huc12data(cursor, huc12, scenario) -> Tuple[int, int, int, int]:
    """Clear out database storage for the typical import case.

    Returns:
        deleted_ofes (int): Number of OFES rows deleted
        deleted_flowpaths (int): Number of flowpaths deleted
        deleted_field_operations (int): Number of field operations deleted
        deleted_fields (int): Number of fields deleted
    """
    cursor.execute(
        "delete from flowpath_ofes o using flowpaths f where "
        "o.flowpath = f.fid and f.huc_12 = %s and f.scenario = %s",
        (huc12, scenario),
    )
    deleted_ofes = cursor.rowcount
    cursor.execute(
        "DELETE from flowpaths WHERE scenario = %s and huc_12 = %s",
        (scenario, huc12),
    )
    deleted_flowpaths = cursor.rowcount
    cursor.execute(
        "delete from field_operations o using fields f where "
        "o.field_id = f.field_id and f.huc12 = %s and f.scenario = %s",
        (huc12, scenario),
    )
    deleted_field_operations = cursor.rowcount
    cursor.execute(
        "DELETE from fields WHERE scenario = %s and huc12 = %s",
        (scenario, huc12),
    )
    deleted_fields = cursor.rowcount
    return (
        deleted_ofes,
        deleted_flowpaths,
        deleted_field_operations,
        deleted_fields,
    )


def load_scenarios():
    """Build a dataframe of DEP scenarios."""
    with get_sqlalchemy_conn("idep") as conn:
        df = pd.read_sql(
            text("SELECT * from scenarios ORDER by id ASC"),
            conn,
            index_col="id",
        )
    return df


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
