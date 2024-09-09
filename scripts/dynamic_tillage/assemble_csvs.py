"""Assemble the csv intermediate files into one big one."""

import glob

import pandas as pd


def main():
    """Go main Go."""
    dfs = []
    for csvfn in glob.glob("plotsv3/corn*.csv"):
        crop, _year, datum = csvfn.split("/")[-1][:-4].split("_")
        if datum in ["IA", "MN", "KS", "NE"]:
            continue
        progress = pd.read_csv(csvfn, parse_dates=["valid"])
        progress["district"] = datum
        progress = progress.rename(
            columns={"dep_planted": f"{crop}_dep_planted"}
        ).set_index(["district", "valid"])
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
        .sort_values(["district", "valid"])
        .to_csv("IA_district_dep_vs_nass_240830.csv", index=False)
    )


if __name__ == "__main__":
    main()
