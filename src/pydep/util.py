"""pydep helper util methods."""

import logging
import math
import sys
from typing import Tuple

import numpy as np
import pandas as pd
from pyiem.database import get_sqlalchemy_conn, sql_helper
from pyiem.iemre import get_domain
from pyiem.util import CustomFormatter
from tqdm import tqdm

from pydep.reference import KWFACT_CLASSES, SLOPE_CLASSES


class TqdmLoggingHandler(logging.Handler):  # skipcq
    """Custom logging handler that uses tqdm.write() for output."""

    def emit(self, record):
        """Emit a log record."""
        try:
            msg = self.format(record)
            tqdm.write(msg)
        except Exception:
            self.handleError(record)


def tqdm_logger() -> logging.Logger:
    """Return a logger that writes to tqdm."""
    ch = TqdmLoggingHandler()
    ch.setFormatter(CustomFormatter())
    # We want the root logger to control everything
    log = logging.getLogger()
    log.setLevel(logging.INFO if sys.stdout.isatty() else logging.WARNING)
    log.addHandler(ch)
    return log


def logger() -> logging.Logger:
    """Return the root logger."""
    ch = logging.StreamHandler()
    ch.setFormatter(CustomFormatter())
    # We want the root logger to control everything
    log = logging.getLogger()
    log.setLevel(logging.INFO if sys.stdout.isatty() else logging.WARNING)
    log.addHandler(ch)
    return log


def compute_management_for_groupid(text: str) -> str:
    """Compute the management portion of the groupid."""
    if text[0] != "0":
        return text[0]
    # Find the first non-0 character in the text string
    for char in text:
        if char != "0":
            return char
    return "0"


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
        return pd.read_sql(
            sql_helper("SELECT * from scenarios ORDER by id ASC"),
            conn,
            index_col="id",
        )


def get_cli_fname(lon: float, lat: float, scenario: int = 0):
    """Get the climate file name for the given lon, lat, and scenario"""
    # The trouble here is relying on rounding is problematic, so we just
    # truncate
    lat = round(lat, 2)
    lon = round(lon, 2)
    domain = get_domain(lon, lat)
    if domain is None:
        raise ValueError(f"lon: {lon} lat: {lat} outside any IEMRE domain")
    if domain == "":
        # Legacy nomenclature
        return (
            f"/i/{scenario}/cli/{math.floor(abs(lon)):03.0f}x"
            f"{math.floor(lat):03.0f}/{(0 - lon):06.2f}x{lat:06.2f}.cli"
        )
    # Lots of pain to keep dashes out of the path
    return (
        f"/mnt/dep/{domain}/2/0/cli/"
        f"{'W' if lon < 0 else 'E'}{math.floor(abs(lon)):03.0f}x"
        f"{'S' if lat < 0 else 'N'}{math.floor(abs(lat)):02.0f}/"
        f"{'W' if lon < 0 else 'E'}{abs(lon):06.2f}x"
        f"{'S' if lat < 0 else 'N'}{abs(lat):05.2f}.cli"
    )
