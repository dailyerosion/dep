"""Summarize the data."""

import pandas as pd
from pyiem.database import get_sqlalchemy_conn, sql_helper


def main():
    """Go Main Go."""
    with open("myhucs.txt") as fh:
        huc12s = [line.strip() for line in fh]
    with get_sqlalchemy_conn("dep") as conn:
        yearlydf = pd.read_sql(
            sql_helper("""
                select huc12_code, scenario_id,
                extract(year from valid) as year,
                sum(avg_loss) as loss_static,
                sum(avg_delivery) as delivery_static,
                sum(avg_runoff) as runoff_static,
                sum(qc_precip) as precip_static
                from water_results_by_huc12 r
                JOIN huc12 h on (r.huc12_id = h.huc12_id)
                where huc12_code = Any(:hucs) and scenario_id in (0, 172)
                and valid < '2026-01-01'
                GROUP by huc12_code, scenario_id, year
            """),
            conn,
            params={"hucs": huc12s},
        )

    finaldf = (
        yearlydf[yearlydf["scenario_id"] == 0]
        .copy()
        .set_index(["huc12_code", "year"])
    )
    staticdf = (
        yearlydf[yearlydf["scenario_id"] == 172]
        .copy()
        .set_index(["huc12_code", "year"])
    )
    for col in ["loss", "delivery", "runoff", "precip"]:
        finaldf[f"{col}_dynamic"] = staticdf[f"{col}_static"]

    finaldf.reset_index().to_csv("plots/results_260226.csv", index=False)


if __name__ == "__main__":
    main()
