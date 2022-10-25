"""Summarize the OFE files"""
import datetime
import os
import sys

import pandas as pd
from tqdm import tqdm
from pyiem.util import get_sqlalchemy_conn, get_dbconn
from pyiem.dep import read_env, read_ofe

# 2007 is skipped
YEARS = 2021 - 2008


def fpmagic(cursor, envfn, rows, huc12, fpath):
    """Do the computations for the flowpath."""
    df = read_env(envfn)
    # Drop any 2007 or 2021+ data
    df = df[
        (df["date"] < datetime.datetime(2021, 1, 1))
        & (df["date"] >= datetime.datetime(2008, 1, 1))
    ]
    cursor.execute(
        "SELECT ST_length(geom), bulk_slope, max_slope from flowpaths "
        "where scenario = 0 and huc_12 = %s and fpath = %s",
        (huc12, fpath),
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


def main():
    """Go Main Go"""
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()
    rows = {}
    fprows = {}
    for root, _dirs, files in tqdm(os.walk("/i/0/ofe"), disable=True):
        for filename in files:
            ofefn = f"{root}/{filename}"
            ofedf = read_ofe(ofefn)
            fpath = filename.split("_")[1][:-4]
            huc12 = filename[:12]
            fpmagic(
                cursor,
                ofefn.replace("ofe", "env"),
                fprows.setdefault(huc12, []),
                huc12,
                fpath,
            )
            # Drop any 2007 or 2021+ data
            ofedf = ofedf[
                (ofedf["date"] < datetime.datetime(2021, 1, 1))
                & (ofedf["date"] >= datetime.datetime(2008, 1, 1))
            ]
            # Figure out the crop string
            huc12rows = rows.setdefault(huc12, [])
            with get_sqlalchemy_conn("idep") as conn:
                meta = pd.read_sql(
                    """
                    with data as (
                        select ofe,
                        (max(elevation) - min(elevation)) /
                        greatest(3, max(length) - min(length)) as bulk_slope,
                        max(slope) as max_slope,
                        max(genlu) as genlu,
                        max(landuse) as landuse, max(management) as management,
                        max(g.mukey) as surgo,
                        max(g.kwfact) as kwfact,
                        max(g.hydrogroup) as hydrogroup,
                        max(fbndid) as max_fbndid,
                        min(fbndid) as min_fbndid,
                        greatest(3, max(length) - min(length)) as length
                        from flowpath_points p JOIN flowpaths f on
                        (p.flowpath = f.fid)
                        JOIN gssurgo g on (p.gssurgo_id = g.id)
                        WHERe f.scenario = 0
                        and f.huc_12 = %s  and fpath = %s GROUP by ofe)
                    select d.*, g.label from data d JOIN general_landuse g on
                    (d.genlu = g.id)
                    """,
                    conn,
                    params=(huc12, fpath),
                )
            # could have zeros from bulk_slope, so overwrite max value
            meta.loc[meta["bulk_slope"] == 0, "bulk_slope"] = meta["max_slope"]

            for ofe in ofedf["ofe"].unique():
                myofe = ofedf[ofedf["ofe"] == ofe]
                meta_ofe = meta[meta["ofe"] == ofe]
                if meta_ofe.empty:
                    print(ofe, huc12, fpath)
                    sys.exit()
                length = meta_ofe["length"].values[0]
                # TODO does not handle OFEs crossing fbndid values
                huc12rows.append(
                    {
                        "id": f"{filename[:-4]}_{ofe}",
                        "huc12": huc12,
                        "fpath": fpath,
                        "ofe": ofe,
                        "fbndid": meta_ofe["min_fbndid"].values[0],
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
                            myofe["sedleave"].sum() / YEARS / length * 4.463
                        ),
                        "genlanduse": meta_ofe["label"].values[0],
                        "management": meta_ofe["management"].values[0],
                    }
                )

    for huc12, hrows in fprows.items():
        df = pd.DataFrame(hrows)
        df.to_csv(f"fpresults_{huc12}.csv", index=False)


if __name__ == "__main__":
    main()
