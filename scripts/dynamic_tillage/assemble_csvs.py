"""Assemble the csv intermediate files into one big one."""

import glob

import click
import pandas as pd


@click.command()
@click.option("--crop", required=True, type=click.Choice(["corn", "soybeans"]))
def main(crop: str):
    """Go main Go."""
    dfs = []
    # plots directory is sym link managed
    for csvfn in glob.glob(f"plots/{crop}_20??_*.csv"):
        _crop, _year, datum = csvfn.split("/")[-1][:-4].split("_", maxsplit=2)
        if datum in [
            "KS",
        ]:
            continue
        progress = pd.read_csv(csvfn, parse_dates=["date"])
        if f"nass_{crop}_pct" in progress.columns:
            # We need to linearly interpolate the NASS data by year
            for _, _gdf in progress.groupby(progress["date"].dt.year):
                gdf = _gdf.set_index("date").copy()
                # We need to add a 100 observation for the next week following
                # the last observation
                lastob = gdf[gdf[f"nass_{crop}_pct"].notna()].index.max()
                nextweek = lastob + pd.Timedelta(days=7)
                gdf.at[nextweek, f"nass_{crop}_pct"] = 100.0
                gdf[f"nass_{crop}_pct_interp"] = (
                    gdf[f"nass_{crop}_pct"]
                    .interpolate(method="time", limit_direction="both")
                    .ffill()
                    .bfill()
                )
                dfs.append(gdf.reset_index())
        else:
            dfs.append(progress)
    jumbo = pd.concat(dfs)
    (
        jumbo.sort_values(["datum", "date"]).to_csv(
            f"plots/{crop}_progress.csv", index=False
        )
    )


if __name__ == "__main__":
    main()
