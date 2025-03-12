"""Summarize the data."""

import pandas as pd
from pyiem.database import get_sqlalchemy_conn, sql_helper


def main():
    """Go Main Go."""
    with open("myhucs.txt") as fh:
        huc12s = [line.strip() for line in fh]
    with get_sqlalchemy_conn("idep") as conn:
        yearlydf = pd.read_sql(
            sql_helper("""
                select huc_12, scenario, extract(year from valid) as year,
                sum(avg_loss) as loss_static,
                sum(avg_delivery) as delivery_static,
                sum(avg_runoff) as runoff_static,
                sum(qc_precip) as precip_static from results_by_huc12
                where huc_12 = Any(:hucs) and scenario in (0, 169)
                GROUP by huc_12, scenario, year
            """),
            conn,
            params={"hucs": huc12s},
        )

    finaldf = (
        yearlydf[yearlydf["scenario"] == 0]
        .copy()
        .set_index(["huc_12", "year"])
    )
    staticdf = (
        yearlydf[yearlydf["scenario"] == 169]
        .copy()
        .set_index(["huc_12", "year"])
    )
    for col in ["loss", "delivery", "runoff", "precip"]:
        finaldf[f"{col}_dynamic"] = staticdf[f"{col}_static"]

    finaldf.reset_index().to_csv("results_240717.csv", index=False)


if __name__ == "__main__":
    main()
