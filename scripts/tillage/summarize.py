"""Summarizing some tillage code sensitivity work."""

import pandas as pd
from pyiem.database import get_sqlalchemy_conn
from sqlalchemy import text

SCENARIO2TILLAGE = {
    0: "Baseline",
    156: "1 to 2",
    157: "All 1",
    158: "All 2",
    159: "All 3",
    160: "All 4",
    161: "All 5",
    162: "All 6",
    154: "Plus 1",
}


def iowa():
    """summarize"""
    with get_sqlalchemy_conn("idep") as conn:
        df = pd.read_sql(
            text(
                """
        WITH iahuc12 as (
            SELECT huc_12, mlra_id, average_slope_ratio from huc12
            where states = 'IA' and scenario = 0
        ), agg as (
            SELECT r.huc_12, i.mlra_id, i.average_slope_ratio,
            r.scenario, extract(year from valid)::int as yr,
            sum(qc_precip) as precip, sum(avg_runoff) as runoff,
            sum(avg_delivery) as delivery,
            sum(avg_loss) as detachment from results_by_huc12 r JOIN iahuc12 i
            on (r.huc_12 = i.huc_12) WHERE r.scenario = ANY(:scenarios)
            and r.valid >= '2008-01-01'
            and r.valid <= '2024-01-01'
            GROUP by r.huc_12, r.scenario, i.mlra_id, i.average_slope_ratio, yr
        )

        SELECT yr, huc_12, scenario, mlra_id, average_slope_ratio,
        round((avg(precip) / 25.4)::numeric, 2) as precip_in,
        round((avg(runoff) / 25.4)::numeric, 2) as runoff_in,
        round((avg(delivery) * 4.463)::numeric, 2) as delivery_ta,
        round((avg(detachment) * 4.463)::numeric, 2) as detachment_ta
        from agg GROUP by yr, huc_12, scenario, mlra_id, average_slope_ratio
        ORDER by yr, scenario

        """
            ),
            conn,
            params={"scenarios": list(SCENARIO2TILLAGE.keys())},
        )
    # df["State"] = "Iowa"
    df = df.rename(
        columns={
            "mlra_id": "MLRA",
            "huc_12": "HUC12",
            "average_slope_ratio": "Slope",
            "yr": "Year",
            "precip_in": "Annual_Precip_in",
            "runoff_in": "Annual_Runoff_in",
            "delivery_ta": "Annual_Del_T/ac",
            "detachment_ta": "Annual_Det_T/ac",
        }
    )
    """
    l6 = (
        df[(df["Year"] >= 2017) & (df["Year"] < 2023)]
        .drop(columns=["Year"])
        .groupby(["scenario", "HUC12"])
        .mean()
        .reset_index()
        .copy()
        .rename(
            columns={
                "Annual_Precip_in": "L6yr_Precip_in/yr",
                "Annual_Runoff_in": "L6yr_Runoff_in/yr",
                "Annual_Del_T/ac": "L6yr_Del_T/a/yr",
                "Annual_Det_T/ac": "L6yr_Det_T/a/yr",
            }
        )
    )
    lt = (
        df
        .drop(columns=["Year"])
        .groupby(["scenario", "HUC12"])
        .mean()
        .reset_index()
        .copy()
        .rename(
            columns={
                "Annual_Precip_in": "LT_Precip_in/yr",
                "Annual_Runoff_in": "LT_Runoff_in/yr",
                "Annual_Del_T/ac": "LT_Del_T/a/yr",
                "Annual_Det_T/ac": "LT_Det_T/a/yr",
            }
        )
    )
    df = pd.merge(lt, l6, on=["scenario", "HUC12"])
    df["Till_Code"] = df["scenario"].map(SCENARIO2TILLAGE)
    df["HUC8"] = df["HUC12"].str.slice(0, 8)
    df.drop(columns=["MLRA_x", "Slope_x"]).rename(columns={
        "MLRA_y": "MLRA",
        "Slope_y": "Slope",
    }).to_csv("HUC12_LongTerm.csv", index=False)
    """
    # reorder
    df = df.groupby(["HUC12", "Year", "scenario"]).mean().reset_index().copy()
    df["Till_Code"] = df["scenario"].map(SCENARIO2TILLAGE)
    df["HUC8"] = df["HUC12"].str.slice(0, 8)
    df[
        [
            "HUC12",
            "MLRA",
            "HUC8",
            "Till_Code",
            "scenario",
            "Slope",
            "Year",
            "Annual_Precip_in",
            "Annual_Runoff_in",
            "Annual_Det_T/ac",
            "Annual_Del_T/ac",
        ]
    ].to_csv("HUC12_annual.csv", index=False)


if __name__ == "__main__":
    iowa()
