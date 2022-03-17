"""Summarize the OFE files"""
import datetime
import os
import sys

import pandas as pd
from tqdm import tqdm
from pyiem.util import get_sqlalchemy_conn
from pyiem.dep import read_ofe

# 2007 is skipped
YEARS = 2021 - 2008


def main():
    """Go Main Go"""
    rows = []
    for root, _dirs, files in tqdm(os.walk("/i/0/ofe"), disable=True):
        for filename in files:
            ofedf = read_ofe(f"{root}/{filename}")
            # Drop any 2007 or 2021+ data
            ofedf = ofedf[
                (ofedf["date"] < datetime.datetime(2021, 1, 1))
                & (ofedf["date"] >= datetime.datetime(2008, 1, 1))
            ]
            # Figure out the crop string
            fpath = filename.split("_")[1][:-4]
            huc12 = filename[:12]
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
                        max(surgo) as surgo,
                        max(fbndid) as max_fbndid,
                        min(fbndid) as min_fbndid,
                        greatest(3, max(length) - min(length)) as length
                        from flowpath_points p JOIN flowpaths f on
                        (p.flowpath = f.fid) WHERe f.scenario = 0
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
                print(fpath)
                print(meta_ofe)
                if meta_ofe.empty:
                    print(ofe, huc12, fpath)
                    sys.exit()
                length = meta_ofe["length"].values[0]
                assert (
                    meta_ofe["min_fbndid"].values[0]
                    == meta_ofe["max_fbndid"].values[0]
                )
                rows.append(
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

    df = pd.DataFrame(rows)
    df.to_csv("results.csv", index=False)


if __name__ == "__main__":
    main()
