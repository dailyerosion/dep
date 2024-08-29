"""Assemble the csv intermediate files into one big one."""

import glob

import pandas as pd


def main():
    """Go main Go."""
    dfs = []
    for csvfn in glob.glob("plotsv2/*_??.csv"):
        crop, _year, state = csvfn[:-4].split("_")
        if state not in ["MN", "IA"]:
            continue
        progress = pd.read_csv(csvfn, parse_dates=["valid"])
        progress["state"] = state
        progress = progress.rename(
            columns={"dep_planted": f"{crop}_dep_planted"}
        ).set_index(["state", "valid"])
        dfs.append(progress)
    jumbo = pd.concat(dfs)
    rectified = jumbo[
        jumbo["corn planted"].notna() | jumbo["dep_corn_planted"].notna()
    ].copy()

    # Drop things with all nulls
    rectified = rectified[
        rectified["dep_corn_planted"].notna()
        | rectified["dep_days_suitable"].notna()
    ]

    (
        rectified.reset_index()
        .sort_values(["state", "valid"])
        .to_csv("IA_MN_dep_vs_nass_240828.csv", index=False)
    )


if __name__ == "__main__":
    main()
