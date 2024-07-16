"""Assemble the csv intermediate files into one big one."""

import glob

import pandas as pd


def main():
    """Go main Go."""
    dfs = []
    for csvfn in glob.glob("*_??.csv"):
        crop, _year, state = csvfn[:-4].split("_")
        if state not in ["MN", "IA"]:
            continue
        progress = pd.read_csv(csvfn, parse_dates=["valid"])
        progress["state"] = state
        # Need to fill out NASS with 100s
        firstidx = progress[f"{crop} planted"].first_valid_index()
        if firstidx > 0:
            progress.loc[:firstidx, f"{crop} planted"] = 0
        lastidx = progress[f"{crop} planted"].last_valid_index()
        if lastidx is not None:
            progress.loc[(lastidx + 1) :, f"{crop} planted"] = 100
        progress = progress.rename(
            columns={"dep_planted": f"{crop}_dep_planted"}
        ).set_index(["state", "valid"])
        dfs.append(progress)
    jumbo = pd.concat(dfs)
    rectified = jumbo[
        jumbo["corn planted"].notna() | jumbo["dep_corn_planted"].notna()
    ].copy()
    soybeans = jumbo[
        jumbo["soybeans planted"].notna()
        | jumbo["dep_soybeans_planted"].notna()
    ].copy()
    rectified["soybeans planted"] = soybeans["soybeans planted"]
    rectified["dep_soybeans_planted"] = soybeans["dep_soybeans_planted"]

    # Drop things with all nulls
    rectified = rectified[
        rectified["dep_corn_planted"].notna()
        | rectified["dep_soybeans_planted"].notna()
        | rectified["dep_days_suitable"].notna()
    ]

    (
        rectified.reset_index()
        .sort_values(["state", "valid"])
        .to_csv("IA_MN_dep_vs_nass_240715.csv", index=False)
    )


if __name__ == "__main__":
    main()
