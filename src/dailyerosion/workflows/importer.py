"""Helpers related to the data import into DEP."""

import pandas as pd


def clean_water_landuse(df: pd.DataFrame) -> None:
    """Apply logic to clean/rectify landuse codes with `T` values.

    See: https://github.com/dailyerosion/dep/issues/48
    """
    t_counts = df["landuse"].str.count("T")
    years = len(df.iloc[0]["landuse"])
    all_t = "T" * years
    # If landuse is 50% or more T, then it goes all T
    df.loc[t_counts >= years / 2, "landuse"] = all_t

    # If it is less then 50%, then we replace with most recent non-T value
    def _replace_t_with_first_non_t(landuse: str) -> str:
        """Helper."""
        if "T" not in landuse:
            return landuse
        replace_value = landuse.replace("T", "")[0]
        new_landuse = list(landuse)
        for idx, value in enumerate(list(landuse)):
            if value != "T":
                replace_value = value
                continue
            new_landuse[idx] = replace_value
        return "".join(new_landuse)

    df.loc[t_counts < years / 2, "landuse"] = df.loc[
        t_counts < years / 2, "landuse"
    ].apply(_replace_t_with_first_non_t)
