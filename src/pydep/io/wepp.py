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


def _date_from_year_jday(df):
    """Create a date column based on year and jday columns."""
    df["date"] = pd.to_datetime(
        df["year"].astype(str) + " " + df["jday"].astype(str), format="%Y %j"
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


def intensity(times, points, compute_intensity_over) -> dict:
    """Returns dict of computed intensities over the given minute intervals."""
    entry = {}
    for interval in compute_intensity_over:
        entry[f"i{interval}_mm"] = 0
    if not times:
        return entry

    # Optimize, a two length times can be directly computed
    if len(times) == 2:
        rate_mmhr = points[1] / (times[1] - times[0])
        for interval in compute_intensity_over:
            entry[f"i{interval}_mm"] = rate_mmhr * interval / 60.0
        return entry

    # Rectify times to integer minutes
    times = (np.array(times) * 60.0).round(0)
    # Resample to every minute
    df = (
        pd.DataFrame({"pcpn": points}, index=times)
        .reindex(np.arange(0, 24 * 60.0))
        .interpolate()
        .fillna(0)
    )
    for interval in compute_intensity_over:
        entry[f"i{interval}_mm"] = (
            df["pcpn"].shift(0 - interval) - df["pcpn"]
        ).max()
    return entry


def read_cli(
    filename,
    compute_rfactor=False,
    return_rfactor_metric=True,
    compute_intensity_over=None,
):
    """Read WEPP CLI File, Return DataFrame

    Args:
      filename (str): Filename to read
      compute_rfactor (bool, optional): Should the R-factor be computed as
        well, adds computational expense and default is False.
      return_rfactor_metric (bool, optional): should the R-factor be
        computed as the common metric value.  Default is True.
      compute_intensity_over (list, optional): list of minute values to compute
        the max intensity over.  Adds `i{minute}_mm` in returned DataFrame.

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
        row = {
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
        if compute_intensity_over is not None:
            row.update(intensity(times, points, compute_intensity_over))
        rows.append(row)

    return pd.DataFrame(rows, index=pd.DatetimeIndex(dates))


def read_crop(filename):
    """Read WEPP's plant and residue output file.

    Args:
      filename (str): The file to read in.

    Returns:
      pandas.DataFrame
    """
    df = pd.read_csv(
        filename,
        skiprows=13,
        index_col=False,
        sep=r"\s+",
        header=None,
        na_values=["*******", "******", "********"],
        names=[
            "ofe",
            "jday",
            "year",
            "canopy_height_m",
            "canopy_percent",
            "lai",
            "cover_rill_percent",
            "cover_inter_percent",
            "cover_inter_type",
            "live_biomass_kgm2",
            "standing_residue_kgm2",
            "flat_residue_last_type",
            "flat_residue_last_kgm2",
            "flat_residue_prev_type",
            "flat_residue_prev_kgm2",
            "flat_residue_all_type",
            "flat_residue_all_kgm2",
            "buried_residue_last_kgm2",
            "buried_residue_prev_kgm2",
            "buried_residue_all_kgm2",
            "deadroot_residue_last_type",
            "deadroot_residue_last_kgm2",
            "deadroot_residue_prev_type",
            "deadroot_residue_prev_kgm2",
            "deadroot_residue_all_type",
            "deadroot_residue_all_kgm2",
            "avg_temp_c",
        ],
    )
    # Convert jday into dates
    _date_from_year_jday(df)
    return df


def read_env(filename, year0=2006) -> pd.DataFrame:
    """Read WEPP .env file, return a dataframe.

    Args:
      filename (str): Filename to read
      year0 (int,optional): The simulation start year minus 1, WEPP2013 for DEP
        uses an explicit year, so magic happens if it detects years > 1000.

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
            "detlen",  # wepp2023
            "deplen",  # wepp2023
        ],
    )
    if df.empty:
        df["date"] = None
    else:
        # Only add years when the data seems to warrant it.
        if df["year"].max() < 1000:
            # Faster than +=
            df["year"] = df["year"] + year0
        # Considerably faster than df.apply
        df["date"] = pd.to_datetime(
            {"year": df["year"], "month": df["month"], "day": df["day"]}
        )
    return df


def read_ofe(filename, year0=2006):
    """Read OFE .ofe file, return a dataframe

    Args:
      filename (str): Filename to read
      year0 (int,optional): The simulation start year minus 1

    Returns:
      pd.DataFrame
    """
    df = pd.read_csv(
        filename,
        skiprows=2,
        index_col=False,
        sep=r"\s+",
        header=None,
        na_values=["*******", "******", "********"],
        names=[
            "ofe",
            "day",
            "month",
            "year",
            "precip",
            "runoff",
            "effint",
            "peakro",
            "effdur",
            "enrich_ratio",
            "keff",
            "sm",
            "leafarea",
            "canhght",
            "cancov",
            "intcov",
            "rilcov",
            "livbio",
            "deadbio",
            "ki",
            "kr",
            "tcrit",
            "rilwid",
            "sedleave",
        ],
    )
    if df.empty:
        df["date"] = None
    else:
        # Faster than +=
        df["year"] = df["year"] + year0
        # Considerably faster than df.apply
        df["date"] = pd.to_datetime(
            dict(year=df["year"], month=df["month"], day=df["day"])
        )
    return df


def read_slp(filename):
    """read WEPP slp file.

    Args:
      filename (str): Filename to read

    Returns:
      list of slope profiles
    """
    with open(filename, encoding="utf8") as fh:
        lines = [a[: a.find("#")].strip() for a in fh]
    segments = int(lines[5])
    res = [None] * segments
    xpos = 0
    elev = 0
    for seg in range(segments):
        # first line is pts and x-length
        (_pts, length) = [float(x) for x in lines[7 + seg * 2].split()]
        # next line is the combo of x-position along length and slope at pt
        line2 = lines[8 + seg * 2].replace(",", " ")
        tokens = np.array([float(x) for x in line2.split()])
        # first value in each pair is the x-pos relative to the length
        xs = xpos + tokens[::2] * length
        # second value is the slope at that position?
        slopes = tokens[1::2]
        # initialize the y-position at the current elevation
        ys = [elev]
        for i in range(1, len(slopes)):
            # dx * slope
            elev -= (xs[i] - xs[i - 1]) * slopes[i - 1]
            ys.append(elev)
        res[seg] = {"x": xs, "slopes": slopes, "y": np.array(ys)}
        xpos += length
    return res


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
