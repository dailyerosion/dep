"""Read DEP custom input/output files."""

import pandas as pd


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
