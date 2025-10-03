"""Comparison to: https://zenodo.org/records/16740666"""

import json

import click
import pandas as pd

STATE2FIPS = {
    "MN": "27",
    "IA": "19",
    "KS": "20",
    "NE": "31",
}


@click.command()
@click.option("--crop", required=True)
def main(crop: str):
    """Go main Go."""
    with open("datum2county.json") as fh:
        XREF = json.load(fh)
    XREF["KS"] = []
    XREF["MN"] = []
    XREF["IA"] = []
    XREF["NE"] = []

    df = pd.read_csv(
        f"{'c' if crop == 'corn' else 's'}cp.csv", parse_dates=["date"]
    )
    df["acres"] = df["area_daily_m2"] * 0.000247105

    results = []

    for datum in XREF:
        if XREF[datum]:
            fips = STATE2FIPS[datum[:2]]
            geoids = [f"{fips}{x[3:]}" for x in XREF[datum]]
            sample = df[df["GEOID"].isin(geoids)]
        else:
            sample = df[df["state"] == datum]  # hack
        for year in range(2000, 2021):
            dyear = sample[sample["Year"] == year].copy()
            dyear = dyear.groupby("date").sum().reset_index()
            dyear["cum_acres"] = dyear["acres"].cumsum()
            dyear["pct"] = dyear["cum_acres"] / dyear["acres"].sum() * 100.0
            for _, row in dyear.iterrows():
                results.append(
                    {
                        "datum": datum,
                        "year": year,
                        "date": row["date"],
                        "acres": row["acres"],
                        "pct": row["pct"],
                    }
                )
    pd.DataFrame(results).to_csv(f"deines2023_datum_{crop}.csv", index=False)


if __name__ == "__main__":
    main()
