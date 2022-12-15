"""Summarize the OFE files"""
import datetime
import os
import sys

import pandas as pd
from tqdm import tqdm
from pyiem.util import get_sqlalchemy_conn, get_dbconn
from pyiem.dep import read_env, read_ofe

# 2007 is skipped
print("\n    PERIOD OF RECORD!!!\n")
YEARS = 2023 - 2007


def fpmagic(cursor, scenario, envfn, rows, huc12, fpath):
    """Do the computations for the flowpath."""
    df = read_env(envfn)
    # Drop any 2007 or 2021+ data
    # df = df[
    #    (df["date"] < datetime.datetime(2021, 1, 1))
    #    & (df["date"] >= datetime.datetime(2008, 1, 1))
    # ]
    cursor.execute(
        "SELECT real_length, bulk_slope, max_slope from flowpaths "
        "where scenario = %s and huc_12 = %s and fpath = %s",
        (scenario, huc12, fpath),
    )
    meta = cursor.fetchone()
    fplen = meta[0]
    df["delivery"] = df["sed_del"] / fplen
    rows.append(
        {
            "id": f"{huc12}_{fpath}",
            "huc12": huc12,
            "fpath": fpath,
            "bulk_slope[1]": meta[1],
            "max_slope[1]": meta[2],
            "runoff[mm/yr]": df["runoff"].sum() / YEARS,
            "detach[t/a/yr]": df["av_det"].sum() / YEARS * 4.463,
            "length[m]": fplen,
            "delivery[t/a/yr]": df["delivery"].sum() / YEARS * 4.463,
        }
    )


def main(argv):
    """Go Main Go"""
    scenario = int(argv[1])
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()
    fprows = {}
    oferows = {}
    with open("myhucs.txt", encoding="utf8") as fh:
        myhucs = fh.read().split("\n")
    for root, _d, files in tqdm(os.walk(f"/i/{scenario}/ofe"), disable=True):
        for filename in files:
            ofefn = f"{root}/{filename}"
            fpath = filename.split("_")[1][:-4]
            huc12 = filename[:12]
            if huc12 not in myhucs:
                continue
            ofedf = read_ofe(ofefn)
            fpmagic(
                cursor,
                scenario,
                ofefn.replace("ofe", "env"),
                fprows.setdefault(huc12, []),
                huc12,
                fpath,
            )
            # Drop any 2007 or 2021+ data
            # ofedf = ofedf[
            #    (ofedf["date"] < datetime.datetime(2021, 1, 1))
            #    & (ofedf["date"] >= datetime.datetime(2008, 1, 1))
            # ]
            # Figure out the crop string
            huc12rows = oferows.setdefault(huc12, [])
            with get_sqlalchemy_conn("idep") as conn:
                meta = pd.read_sql(
                    """
                    with data as (
                        select ofe,
                        o.bulk_slope,
                        o.max_slope,
                        landuse, management,
                        mukey as surgo,
                        kwfact, hydrogroup, fbndid,
                        o.real_length as length, o.genlu
                        from flowpath_ofes o JOIN flowpaths f on
                        (o.flowpath = f.fid)
                        JOIN gssurgo g on (o.gssurgo_id = g.id)
                        WHERe f.scenario = %s
                        and f.huc_12 = %s  and fpath = %s)
                    select d.*, g.label from data d JOIN general_landuse g on
                    (d.genlu = g.id)
                    """,
                    conn,
                    params=(scenario, huc12, fpath),
                )
            accum_length = 0
            for ofe in ofedf["ofe"].unique():
                myofe = ofedf[ofedf["ofe"] == ofe]
                myofe2010 = myofe[myofe["year"] == 2010]
                meta_ofe = meta[meta["ofe"] == ofe]
                if meta_ofe.empty:
                    print(ofe, huc12, fpath)
                    sys.exit()
                length = meta_ofe["length"].values[0]
                accum_length += length
                huc12rows.append(
                    {
                        "id": f"{filename[:-4]}_{ofe}",
                        "huc12": huc12,
                        "fpath": fpath,
                        "ofe": ofe,
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
                        "delivery[t/a/yr]": (
                            myofe["sedleave"].sum()
                            / YEARS
                            / accum_length
                            * 4.463
                        ),
                        "delivery_2010[t/a/yr]": (
                            myofe2010["sedleave"].sum() / accum_length * 4.463
                        ),
                        "genlanduse": meta_ofe["label"].values[0],
                        "management": meta_ofe["management"].values[0],
                    }
                )

    for huc12, frows in oferows.items():
        df = pd.DataFrame(frows)
        df.to_csv(f"oferesults_scenario_{huc12}.csv", index=False)

    for huc12, hrows in fprows.items():
        df = pd.DataFrame(hrows)
        df.to_csv(f"fpresults_scenario_{huc12}.csv", index=False)


if __name__ == "__main__":
    main(sys.argv)
