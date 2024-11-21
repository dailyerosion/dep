"""Report which HUC12s have 0 flowpaths."""

import click
import pandas as pd
from pyiem.database import get_dbconnstr
from sqlalchemy import text


@click.command()
@click.option("--scenario", type=int, required=True)
def main(scenario: int):
    """Go Main Go."""
    huc12s = [s.strip() for s in open("myhucs.txt", encoding="utf8")]
    df = pd.read_sql(
        text(
            "SELECT huc_12, count(*) from flowpaths where scenario = %s "
            "GROUP by huc_12"
        ),
        get_dbconnstr("idep"),
        params=(scenario,),
        index_col="huc_12",
    )
    df = df.reindex(huc12s).fillna(0)
    print(df[df["count"] == 0].index.values)


if __name__ == "__main__":
    main()
