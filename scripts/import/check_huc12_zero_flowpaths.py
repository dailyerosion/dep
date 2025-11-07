"""Report which HUC12s have 0 flowpaths."""

import click
import pandas as pd
from pyiem.database import get_sqlalchemy_conn, sql_helper


@click.command()
@click.option("-s", "--scenario", type=int, required=True)
def main(scenario: int):
    """Go Main Go."""
    with open("myhucs.txt", encoding="utf8") as fh:
        huc12s = [s.strip() for s in fh.readlines()]
    with get_sqlalchemy_conn("idep") as conn:
        df = pd.read_sql(
            sql_helper(
                """
    SELECT huc_12, count(*) from flowpaths where scenario = :scenario
    GROUP by huc_12"""
            ),
            conn,
            params={"scenario": scenario},
            index_col="huc_12",
        )
    df = df.reindex(huc12s).fillna(0)
    print(df[df["count"] == 0].index.values)


if __name__ == "__main__":
    main()
