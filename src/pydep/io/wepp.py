"""pydep readers for WEPP input/output files."""
import datetime
import re

import pandas as pd

YLD_CROPTYPE = re.compile(r"Crop Type #\s+(?P<num>\d+)\s+is (?P<name>[^\s]+)")
YLD_DATA = re.compile(
    (
        r"Crop Type #\s+(?P<num>\d+)\s+Date = (?P<doy>\d+)"
        r" OFE #\s+(?P<ofe>\d+)\s+yield=\s+(?P<yield>[0-9\.]+)"
        r" \(kg/m\*\*2\) year= (?P<year>\d+)"
    )
)


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
