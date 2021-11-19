"""Summarize the OFE files"""
import datetime
import os
import sys

import pandas as pd
from pandas.io.sql import read_sql
from tqdm import tqdm
from pyiem.util import get_dbconn
from pyiem.dep import read_ofe

# 2007 is skipped
YEARS = 2021 - 2008


def main():
    """Go Main Go"""
    pgconn = get_dbconn("idep")
    rows = []
    for root, _dirs, files in tqdm(os.walk("/i/0/ofe"), disable=True):
        for filename in files:
            ofedf = read_ofe(f"{root}/{filename}")
            # Drop any 2007 or 2018+ data
            ofedf = ofedf[
                (ofedf["date"] < datetime.datetime(2021, 1, 1))
                & (ofedf["date"] >= datetime.datetime(2008, 1, 1))
            ]
            # Figure out the crop string
            fpath = filename.split("_")[1][:-4]
            huc12 = filename[:12]
            meta = read_sql(
                """
                with data as (
                    select ofe, (max(elevation) - min(elevation)) /
                    greatest(3, max(length) - min(length)) as slope,
                    max(genlu) as genlu,
                    max(landuse) as landuse, max(management) as management,
                    max(surgo) as surgo,
                    greatest(3, max(length) - min(length)) as length
                    from flowpath_points p JOIN flowpaths f on
                    (p.flowpath = f.fid) WHERe f.scenario = 0
                    and f.huc_12 = %s  and fpath = %s GROUP by ofe)
                select d.*, g.label from data d JOIN general_landuse g on
                (d.genlu = g.id)
                """,
                pgconn,
                params=(huc12, fpath),
            )

            for ofe in ofedf["ofe"].unique():
                myofe = ofedf[ofedf["ofe"] == ofe]
                meta_ofe = meta[meta["ofe"] == (ofe - 1)]
                if meta_ofe.empty:
                    print(ofe, huc12, fpath)
                    sys.exit()
                length = meta_ofe["length"].values[0]
                rows.append(
                    {
                        "id": f"{filename[:-4]}_{ofe}",
                        "huc12": huc12,
                        "fpath": fpath,
                        "ofe": ofe,
                        "CropRotationString": meta_ofe["landuse"].values[0],
                        "slope[1]": meta_ofe["slope"].values[0],
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
