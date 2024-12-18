"""pydep's R-factor calculations."""

from datetime import date

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d


def calc_rfactor(times, points, return_rfactor_metric=True):
    """Compute the R-factor.

    https://www.hydrol-earth-syst-sci.net/19/4113/2015/hess-19-4113-2015.pdf
    It would appear that a strict implementation would need to have a six
    hour dry period around events and require more then 12mm of precipitation.

    Args:
      times (list): List of decimal time values for a date.
      points (list): list of accumulated precip values (mm).
      return_rfactor_metric (bool, optional): Should this return a metric
        (default) or english unit R value.

    Returns:
      rfactor (float): Units of MJ mm ha-1 h-1
    """
    # No precip!
    if not times:
        return 0
    # interpolate dataset into 30 minute bins
    func = interp1d(
        times,
        points,
        kind="linear",
        fill_value=(0, points[-1]),
        bounds_error=False,
    )
    accum = func(np.arange(0, 24.01, 0.5))
    rate_mmhr = (accum[1:] - accum[0:-1]) * 2.0
    # sum of E x I
    # I is the 30 minute peak intensity (mm h-1), capped at 3 in/hr
    Imax = min([3.0 * 25.4, np.max(rate_mmhr)])
    # E is sum of e_r (MJ ha-1 mm-1) * p_r (mm)
    e_r = 0.29 * (1.0 - 0.72 * np.exp(-0.082 * rate_mmhr))
    # rate * times
    p_r = rate_mmhr / 2.0
    # MJ ha-1 * mm h-1  or MJ inch a-1 h-1
    unitconv = 1.0 if return_rfactor_metric else (1.0 / 25.4 / 2.47105)
    return np.sum(e_r * p_r) * Imax * unitconv


def _compute_accum(lines):
    """Return rectified accum values."""
    times = []
    points = []
    for line in lines:
        (ts, accum) = line.strip().split()
        times.append(float(ts))
        points.append(float(accum))
    return interp1d(
        times,
        points,
        kind="linear",
        fill_value=(0, points[-1]),
        bounds_error=False,
    )(np.arange(0.5, 24.01, 0.5))


def _rfactor_year(accum: np.ndarray) -> list:
    """Compute R-factors for a year."""
    storm_start_stop = []
    storm_start = -1
    x = 12
    while x < accum.shape[0]:
        is_dry = (accum[x] - accum[x - 12]) < 1.27
        if not is_dry and storm_start == -1:
            storm_start = x
            x += 12
            continue
        if is_dry and storm_start != -1:
            storm_start_stop.append((storm_start, x))
            storm_start = -1
        x += 1
    rfactors = []
    for start, stop in storm_start_stop:
        event = accum[start:stop] - accum[start]
        rate_mmhr = (event[1:] - event[0:-1]) * 2.0
        # sum of E x I
        # I is the 30 minute peak intensity (mm h-1), capped at 3 in/hr
        Imax = min([3.0 * 25.4, np.max(rate_mmhr)])
        # E is sum of e_r (MJ ha-1 mm-1) * p_r (mm)
        e_r = 0.29 * (1.0 - 0.72 * np.exp(-0.082 * rate_mmhr))
        # rate * times
        p_r = rate_mmhr / 2.0
        # MJ ha-1 * mm h-1  or MJ inch a-1 h-1
        rfactors.append(np.sum(e_r * p_r) * Imax)
    return rfactors


def compute_rfactor_from_cli(
    filename: str,
) -> pd.DataFrame:
    """Compute **yearly** R-factor values from a WEPP breakpoint file.

    Args:
      filename (str): Filename to read

    Returns:
        pandas.DataFrame with yearly values
    """
    with open(filename, encoding="ascii") as fh:  # skipcq
        lines = fh.readlines()
    (*_unused, year1, years_simuluated) = lines[4].strip().split()
    lnum = 15
    resultdf = None
    resultdf = pd.DataFrame(
        {"rfactor": 0.0, "storm_count": 0},
        index=pd.Index(
            range(int(year1), int(year1) + int(years_simuluated)), name="year"
        ),
    )
    # We compute one year at a time.
    year_accum = np.array([])
    while lnum < len(lines):
        (da, mo, year, breakpoints, *_bah) = lines[lnum].strip().split()
        dt = date(int(year), int(mo), int(da))
        doy = dt.timetuple().tm_yday
        idx = (doy - 1) * 24 * 2
        if doy == 1:
            year_accum = np.zeros(366 * 24 * 2)
        breakpoints = int(breakpoints)
        if breakpoints == 0:
            accum = np.zeros(24 * 2)
        else:
            accum = _compute_accum(lines[lnum + 1 : lnum + 1 + breakpoints])
        # Place this accum into the yearly accum and apply offset to keep mono
        year_accum[idx : idx + 24 * 2] = accum + (
            0 if doy == 1 else year_accum[idx - 1]
        )
        if f"{dt:%m%d}" == "1231":
            # Chomp the last day that does not exist
            if doy == 365:
                year_accum = year_accum[: 365 * 24 * 2]
            rfactors = _rfactor_year(year_accum)
            if rfactors:
                resultdf.at[dt.year, "rfactor"] = np.sum(rfactors)
                resultdf.at[dt.year, "storm_count"] = len(rfactors)
        lnum += breakpoints + 1

    return resultdf
