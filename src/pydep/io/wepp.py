"""pydep readers for WEPP input/output files."""

import pandas as pd


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
