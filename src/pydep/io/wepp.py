"""pydep readers for WEPP input/output files."""
import datetime
import re

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d


YLD_CROPTYPE = re.compile(r"Crop Type #\s+(?P<num>\d+)\s+is (?P<name>[^\s]+)")
YLD_DATA = re.compile(
    (
        r"Crop Type #\s+(?P<num>\d+)\s+Date = (?P<doy>\d+)"
        r" OFE #\s+(?P<ofe>\d+)\s+yield=\s+(?P<yield>[0-9\.]+)"
        r" \(kg/m\*\*2\) year= (?P<year>\d+)"
    )
)


def _rfactor(times, points, return_rfactor_metric=True):
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


def read_cli(filename, compute_rfactor=False, return_rfactor_metric=True):
    """Read WEPP CLI File, Return DataFrame

    Args:
      filename (str): Filename to read
      compute_rfactor (bool, optional): Should the R-factor be computed as
        well, adds computational expense and default is False.
      return_rfactor_metric (bool, optional): should the R-factor be
        computed as the common metric value.  Default is True.

    Returns:
      pandas.DataFrame
    """
    rows = []
    dates = []
    with open(filename, encoding="ascii") as fh:
        lines = fh.readlines()
    linenum = 15
    while linenum < len(lines):
        (da, mo, year, breakpoints, tmax, tmin, rad, wvl, wdir, tdew) = lines[
            linenum
        ].split()
        breakpoints = int(breakpoints)
        accum = 0
        times = []
        points = []
        for i in range(1, breakpoints + 1):
            (ts, accum) = lines[linenum + i].split()
            times.append(float(ts))
            points.append(float(accum))
        maxr = 0
        for i in range(1, len(times)):
            dt = times[i] - times[i - 1]
            dr = points[i] - points[i - 1]
            rate = dr / dt
            if rate > maxr:
                maxr = rate
        linenum += breakpoints + 1
        dates.append(datetime.date(int(year), int(mo), int(da)))
        rows.append(
            {
                "tmax": float(tmax),
                "tmin": float(tmin),
                "rad": float(rad),
                "wvl": float(wvl),
                "wdir": float(wdir),
                "tdew": float(tdew),
                "maxr": maxr,
                "bpcount": breakpoints,
                "pcpn": float(accum),
                "rfactor": (
                    np.nan
                    if not compute_rfactor
                    else _rfactor(
                        times,
                        points,
                        return_rfactor_metric=return_rfactor_metric,
                    )
                ),
            }
        )

    return pd.DataFrame(rows, index=pd.DatetimeIndex(dates))


def read_env(filename, year0=2006) -> pd.DataFrame:
    """Read WEPP .env file, return a dataframe

    Args:
      filename (str): Filename to read
      year0 (int,optional): The simulation start year minus 1

    Returns:
      pd.DataFrame
    """
    df = pd.read_csv(
        filename,
        skiprows=3,
        index_col=False,
        sep=r"\s+",
        header=None,
        na_values=["*******", "******", "*****"],
        names=[
            "day",
            "month",
            "year",
            "precip",
            "runoff",
            "ir_det",
            "av_det",
            "mx_det",
            "point",
            "av_dep",
            "max_dep",
            "point2",
            "sed_del",
            "er",
        ],
    )
    if df.empty:
        df["date"] = None
    else:
        # Faster than +=
        df["year"] = df["year"] + year0
        # Considerably faster than df.apply
        df["date"] = pd.to_datetime(
            {"year": df["year"], "month": df["month"], "day": df["day"]}
        )
    return df


def read_yld(filename):
    """read WEPP yld file with some local mods to include a year

    Args:
      filename (str): Filename to read

    Returns:
      pandas.DataFrame
    """
    with open(filename, encoding="utf8") as fh:
        data = fh.read()
    xref = {}
    for cropcode, label in YLD_CROPTYPE.findall(data):
        xref[cropcode] = label
    rows = []
    for cropcode, doy, ofe, yld, year in YLD_DATA.findall(data):
        date = datetime.date(int(year), 1, 1) + datetime.timedelta(
            days=(int(doy) - 1)
        )
        rows.append(
            dict(
                valid=date,
                year=int(year),
                yield_kgm2=float(yld),
                crop=xref[cropcode],
                ofe=int(ofe),
            )
        )
    return pd.DataFrame(rows)
