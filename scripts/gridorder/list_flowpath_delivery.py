"""List out the results for each flowpath within a HUC12"""
from __future__ import print_function
import sys
import datetime

import psycopg2
import pandas as pd
from pandas.io.sql import read_sql
from pyiem.dep import read_env

SCEN2CODE = [None, 12, 13, 14, 0, 15, 16]
PGCONN = psycopg2.connect(database="idep")


def get_results(huc12):
    """Do as I say"""
    df = pd.DataFrame()
    for gorder, scenario in enumerate(SCEN2CODE):
        if gorder == 0:
            continue
        lendf = read_sql(
            """
            SELECT fpath, ST_Length(geom) as length from flowpaths where
            scenario = %s and huc_12 = %s
        """,
            PGCONN,
            params=(scenario, huc12),
            index_col="fpath",
        )
        for fpath, row in lendf.iterrows():
            res = read_env(
                ("/i/%s/env/%s/%s/%s_%s.env")
                % (scenario, huc12[:8], huc12[8:], huc12, fpath)
            )
            res = res[res["date"] < datetime.date(2017, 1, 1)]
            res["delivery"] = res["sed_del"] / row["length"] * 4.463
            df.at[fpath, "G%s_delivery_ta" % (gorder,)] = (
                res["delivery"].sum() / 10.0
            )

    return df


def main(argv):
    """Do things"""
    huc12 = argv[1]
    df = get_results(huc12)
    df.to_csv("results.csv")


if __name__ == "__main__":
    main(sys.argv)
