"""Assemble the csv intermediate files into one big one."""

import glob

import click
import pandas as pd


@click.command()
@click.option("--crop", required=True)
def main(crop: str):
    """Go main Go."""
    dfs = []
    # plots directory is sym link managed
    for csvfn in glob.glob(f"plots/{crop}*.csv"):
        _crop, _year, datum = csvfn.split("/")[-1][:-4].split("_")
        if datum in ["KS", "NE"]:
            continue
        progress = pd.read_csv(csvfn, parse_dates=["valid"])
        progress["datum"] = datum
        progress = progress.rename(
            columns={"dep_planted": f"{crop}_dep_planted"}
        ).set_index(["datum", "valid"])
        dfs.append(progress)
    jumbo = pd.concat(dfs)
    rectified = jumbo[
        jumbo[f"{crop} planted"].notna() | jumbo[f"dep_{crop}_planted"].notna()
    ].copy()

    # Drop things with all nulls
    rectified = rectified[
        rectified[f"dep_{crop}_planted"].notna()
        | rectified["dep_days_suitable"].notna()
    ]

    (
        rectified.reset_index()
        .sort_values(["datum", "valid"])
        .to_csv(f"{crop}_dep_vs_nass_251002.csv", index=False)
    )


if __name__ == "__main__":
    main()
