"""Summarize the OFE files"""

import glob
import os
import sys
from datetime import datetime

import click
import pandas as pd
from pyiem.database import get_dbconn, get_sqlalchemy_conn, sql_helper
from pyiem.util import logger
from tqdm import tqdm

from dailyerosion.io.wepp import read_env, read_ofe
from dailyerosion.reference import KG_M2_TO_TON_ACRE

LOG = logger()
# 2007 is skipped
YEARS = 6.0


def fpmagic(cursor, scenario, envfn, rows, huc12, fpath, mlrarsym):
    """Do the computations for the flowpath."""
    eventdf = read_env(envfn)
    cursor.execute(
        "SELECT real_length, bulk_slope, max_slope from flowpaths "
        "where scenario = %s and huc_12 = %s and fpath = %s",
        (scenario, huc12, fpath),
    )
    meta = cursor.fetchone()
    fplen = meta[0]
    eventdf["delivery"] = eventdf["sed_del"] / fplen
    # Only want 2017 through 2022
    filtered = eventdf[
        (eventdf["date"] < datetime(2024, 1, 1))
        & (eventdf["date"] >= datetime(2018, 1, 1))
    ]
    res = {
        "id": f"{huc12}_{fpath}",
        "huc12": huc12,
        "mlrarsym": mlrarsym,
        "fpath": fpath,
        "bulk_slope[1]": meta[1],
        "max_slope[1]": meta[2],
        "runoff[mm/yr]": filtered["runoff"].sum() / YEARS,
        "detach[t/a/yr]": filtered["av_det"].sum() / YEARS * KG_M2_TO_TON_ACRE,
        "length[m]": fplen,
        "delivery[t/a/yr]": filtered["delivery"].sum()
        / YEARS
        * KG_M2_TO_TON_ACRE,
    }
    for year in range(2007, 2025):
        df2 = eventdf[eventdf["year"] == year]
        res[f"delivery_{year}_t/a"] = df2["delivery"].sum() * KG_M2_TO_TON_ACRE
        res[f"runoff_{year}_mm"] = df2["runoff"].sum()
    rows.append(res)


def do_huc12(cursor, scenario, huc12):
    """Workflow."""
    fprows = []
    oferows = []
    if os.path.isfile(
        f"/i/{scenario}/ofe/{huc12[:8]}/{huc12[8:]}/oferesults_{huc12}.csv"
    ):
        return
    with get_sqlalchemy_conn("idep") as conn:
        huc12df = pd.read_sql(
            sql_helper(
                """
            SELECT huc_12, max(mlrarsym) as mlrarsym
                from huc12 h JOIN mlra m on
            (h.mlra_id = m.mlra_id) WHERE h.scenario = :scen and
            huc_12 = :huc12
            GROUP by huc_12
            """
            ),
            conn,
            params={"scen": scenario, "huc12": huc12},
            index_col="huc_12",
        )
        fieldsdf = pd.read_sql(
            sql_helper(
                """
            select huc12, fbndid, isag, g.label as genlanduse from
            fields f, general_landuse g WHERE f.genlu = g.id and
            f.scenario = :scen and huc12 = :huc12
            """
            ),
            conn,
            params={"scen": scenario, "huc12": huc12},
        )

    for ofefn in glob.glob(f"/i/{scenario}/ofe/{huc12[:8]}/{huc12[8:]}/*.ofe"):
        fpath = ofefn.split("_")[-1][:-4]
        ofedf = read_ofe(ofefn)
        fpmagic(
            cursor,
            scenario,
            ofefn.replace("ofe", "env"),
            fprows,
            huc12,
            fpath,
            huc12df.at[huc12, "mlrarsym"],
        )
        # Just 2017-2022
        ofedf = ofedf[
            (ofedf["date"] < datetime(2024, 1, 1))
            & (ofedf["date"] >= datetime(2018, 1, 1))
        ]
        # Figure out the crop string
        with get_sqlalchemy_conn("idep") as conn:
            meta = pd.read_sql(
                """
                    select ofe,
                    o.bulk_slope,
                    o.max_slope,
                    landuse, management,
                    mukey as surgo,
                    kwfact, hydrogroup, fbndid,
                    o.real_length as length, groupid
                    from flowpath_ofes o JOIN flowpaths f on
                    (o.flowpath = f.fid)
                    JOIN gssurgo g on (o.gssurgo_id = g.id)
                    WHERe f.scenario = %s
                    and f.huc_12 = %s  and fpath = %s
                """,
                conn,
                params=(scenario, huc12, fpath),
            )
        accum_length = 0
        lastdelivery = 0
        lastdelivery_byyear = {
            2018: 0,
            2019: 0,
            2020: 0,
            2021: 0,
            2022: 0,
            2023: 0,
        }
        for ofe in ofedf["ofe"].unique():  # Assuming this is sorted(?)
            myofe = ofedf[ofedf["ofe"] == ofe]
            meta_ofe = meta[meta["ofe"] == ofe]
            if meta_ofe.empty:
                print(ofe, huc12, fpath)
                sys.exit()
            field_meta = fieldsdf[
                (fieldsdf["fbndid"] == meta_ofe["fbndid"].values[0])
                & (fieldsdf["huc12"] == huc12)
            ]
            length = meta_ofe["length"].values[0]
            accum_length += length
            thisdelivery = (
                myofe["sedleave"].sum()
                / YEARS
                / accum_length
                * KG_M2_TO_TON_ACRE
            )
            groupid: str = meta_ofe["groupid"].values[0]
            res = {
                "id": f"{os.path.basename(ofefn)[:-4]}_{ofe}",
                "groupid": groupid,
                "slope_reclass": groupid.split("_")[0],
                "kw_reclass": groupid.split("_")[1],
                "huc12": huc12,
                "mlrarsym": huc12df.at[huc12, "mlrarsym"],
                "fpath": fpath,
                "ofe": ofe,
                "genlanduse": field_meta["genlanduse"].values[0],
                "isag": field_meta["isag"].values[0],
                "fbndid": meta_ofe["fbndid"].values[0],
                "CropRotationString": meta_ofe["landuse"].values[0],
                "bulk_slope[1]": meta_ofe["bulk_slope"].values[0],
                "max_slope[1]": meta_ofe["max_slope"].values[0],
                "soil_mukey": meta_ofe["surgo"].values[0],
                "soil_kwfact": meta_ofe["kwfact"].values[0],
                "soil_hydrogroup": meta_ofe["hydrogroup"].values[0],
                "rainfall": -1,
                "runoff[mm/yr]": myofe["runoff"].sum() / YEARS,
                "detach": -1,
                "length[m]": length,
                "delivery[t/a/yr]": thisdelivery,
                "ofe_loss[t/a/yr]": thisdelivery - lastdelivery,
                "management": meta_ofe["management"].values[0],
                "tillage_code_2022": (
                    meta_ofe["management"].values[0][2022 - 2007]
                ),
            }
            lastdelivery = thisdelivery
            for year in range(2018, 2024):
                df2 = myofe[myofe["year"] == year]
                thisdelivery = (
                    df2["sedleave"].sum() / accum_length * KG_M2_TO_TON_ACRE
                )
                res[f"delivery_{year}[t/a]"] = thisdelivery
                res[f"ofe_loss_{year}[t/a]"] = (
                    thisdelivery - lastdelivery_byyear[year]
                )
                lastdelivery_byyear[year] = thisdelivery

            oferows.append(res)

    df = pd.DataFrame(oferows)
    df.to_csv(
        f"/i/{scenario}/ofe/{huc12[:8]}/{huc12[8:]}/oferesults_{huc12}.csv",
        index=False,
        float_format="%.4f",
    )

    df = pd.DataFrame(fprows)
    df.to_csv(
        f"/i/{scenario}/ofe/{huc12[:8]}/{huc12[8:]}/fpresults_{huc12}.csv",
        index=False,
        float_format="%.4f",
    )


@click.command()
@click.option("--scenario", "-s", default=0, help="Scenario ID", type=int)
@click.option("--huc12", type=str, help="HUC12 to process, default all")
def main(scenario, huc12):
    """Go Main Go"""
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()
    myhucs = []
    if os.path.isfile("myhucs.txt"):
        print("Found myhucs.txt, using it")
        with open("myhucs.txt", encoding="utf8") as fh:
            myhucs = fh.read().split("\n")
    elif huc12 is not None:
        myhucs.append(huc12)
    else:
        cursor.execute(
            """
    SELECT huc_12 from huc12 where scenario = %s
    ORDER by huc_12 desc""",
            (scenario,),
        )
        for row in cursor:
            myhucs.append(row[0])
    progress = tqdm(myhucs)
    for huc12 in progress:
        progress.set_description(huc12)
        try:
            do_huc12(cursor, scenario, huc12)
        except Exception as exp:
            LOG.exception(exp, exc_info=True)
            print(huc12)


if __name__ == "__main__":
    main()
