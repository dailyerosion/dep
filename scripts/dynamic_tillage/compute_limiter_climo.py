"""Compute the climatology of a HUC12 limiter."""

import click
import pandas as pd


@click.command()
def main():
    """Go Main Go."""
    statsdf = None
    total = 0
    for year in range(2007, 2026):
        for dt in pd.date_range(f"{year}-04-11", f"{year}-06-12"):
            total += 1
            huc12data = pd.read_feather(
                f"/mnt/idep2/data/huc12status/{dt:%Y}/{dt:%Y%m%d}.feather"
            )
            if statsdf is None:
                statsdf = pd.DataFrame(
                    {
                        "limited_by_precip": 0,
                        "limited_by_soiltemp": 0,
                        "limited_by_soilmoisture": 0,
                        "limited": 0,
                    },
                    index=huc12data.index,
                )
            for col in statsdf.columns:
                statsdf[col] += huc12data[col].astype(int)
    statsdf["total"] = total
    statsdf.to_csv("plots/huc12_limiter_climo.csv", index_label="huc12")


if __name__ == "__main__":
    main()
