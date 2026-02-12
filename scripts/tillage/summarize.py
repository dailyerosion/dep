"""Summarizing some tillage code sensitivity work."""

import pandas as pd
from pyiem.database import get_sqlalchemy_conn, sql_helper

from dailyerosion.reference import KG_M2_TO_TON_ACRE

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
    164: "All 1.5",
    165: "All Pasture",
    167: "All Coulter",
}


def iowa():
    """summarize"""
    with get_sqlalchemy_conn("idep") as conn:
        annualdf = pd.read_sql(
            sql_helper(
                """
        WITH huc12meta as (
            SELECT huc_12, mlra_id, average_slope_ratio, ugc,
            substr(states, 1, 2) as state from huc12 where scenario = 0
        ), annual as (
            SELECT huc_12, scenario, extract(year from valid)::int as yr,
            sum(qc_precip) as precip, sum(avg_runoff) as runoff,
            sum(avg_delivery) as delivery,
            sum(avg_loss) as detachment from results_by_huc12
            WHERE scenario = 0
            and valid >= '2008-01-01'
            and valid <= '2024-12-31'
            GROUP by huc_12, scenario, yr
        )

        SELECT h.*, a.yr, a.scenario,
        round((precip / 25.4)::numeric, 2) as precip_in,
        round((runoff / 25.4)::numeric, 2) as runoff_in,
        round((delivery * :factor)::numeric, 2) as delivery_ta,
        round((detachment * :factor)::numeric, 2) as detachment_ta
        from annual a, huc12meta h WHERE a.huc_12 = h.huc_12
        ORDER by yr, scenario

        """
            ),
            conn,
            params={
                "scenarios": list(SCENARIO2TILLAGE.keys()),
                "factor": KG_M2_TO_TON_ACRE,
            },
        )
    annualdf.rename(
        columns={
            "mlra_id": "MLRA",
            "huc_12": "HUC12",
            "ugc": "County",
            "average_slope_ratio": "Slope",
            "yr": "Year",
            "precip_in": "Annual_Precip_in",
            "runoff_in": "Annual_Runoff_in",
            "delivery_ta": "Annual_Del_T/ac",
            "detachment_ta": "Annual_Det_T/ac",
        }
    ).to_csv("HUC12_Annual.csv", index=False)
    """ All the below needs help
    l6 = (
        df[(df["Year"] >= 2017) & (df["Year"] < 2023)]
        .drop(columns=["Year"])
        .groupby(["scenario", "HUC12", "County"])
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
        df.drop(columns=["Year"])
        .groupby(["scenario", "HUC12", "County"])
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
    df.drop(columns=["Slope_x"]).rename(
        columns={
            # "MLRA_y": "MLRA",
            "Slope_y": "Slope",
        }
    ).to_csv("HUC12_LongTerm.csv", index=False)
    # reorder
    df = df.groupby(["state", "Year", "scenario"]).mean().reset_index().copy()
    df["Till_Code"] = df["scenario"].map(SCENARIO2TILLAGE)
    # df["HUC8"] = df["HUC12"].str.slice(0, 8)
    df[
        [
            "state",
            # "MLRA",
            # "HUC8",
            "Till_Code",
            "scenario",
            "Slope",
            "Year",
            "Annual_Precip_in",
            "Annual_Runoff_in",
            "Annual_Det_T/ac",
            "Annual_Del_T/ac",
        ]
    ].to_csv("State_annual.csv", index=False)
    """


if __name__ == "__main__":
    iowa()
