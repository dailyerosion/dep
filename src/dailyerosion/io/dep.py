"""Read DEP custom input/output files."""

import pandas as pd


def read_env(filename, year0=2006) -> pd.DataFrame:
    """Read DEP customized .env file, which is single space delimited and has
    a full year.

    Args:
      filename (str): Filename to read

    Returns:
      pd.DataFrame
    """
    df = pd.read_csv(
        filename,
        skiprows=3,
        index_col=False,
        sep=" ",
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
        # Considerably faster than df.apply
        df["date"] = pd.to_datetime(
            {"year": df["year"], "month": df["month"], "day": df["day"]}
        )
    return df


def _date_from_year_jday(df):
    """Create a date column based on year and jday columns."""
    df["date"] = pd.to_datetime(
        df["year"].astype(str) + " " + df["jday"].astype(str), format="%Y %j"
    )


def read_wb(filename):
    """Read a *custom* WEPP .wb file into Pandas Data Table"""
    df = pd.read_csv(filename, sep=r"\s+", na_values=["*******", "******"])
    if df.empty:
        df["date"] = None
    else:
        # Considerably faster than df.apply
        _date_from_year_jday(df)
    return df
