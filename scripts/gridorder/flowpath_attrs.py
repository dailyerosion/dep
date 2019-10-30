"""Answer a data request with the following

 1) lat/lon of 'F0' first point
 2) Picture of location?  Hmmm, I did huc12 previously
 3) elevation of F0 and G1 through G6 nodes
 4) horizontal distance from F0 to G1-G6
 5) OFE positions along this path
 6) Generic properties, perhaps can ignore?
"""
from __future__ import print_function

import psycopg2
import numpy as np
from geopandas import read_postgis
import pandas as pd
from simpledbf import Dbf5

PGCONN = psycopg2.connect(database="idep")
HUCS = """101702031901
101702031904
070600010905
070600010906
102300020302
102300020303
102400010103
102300060405
071000030504
071000030802
070801020403
070801020504
070801070302
070801070101
102400130102
102400130201
102802010404
102802010209
070801010701
070801010702""".split(
    "\n"
)
SCEN2CODE = [None, 12, 13, 14, 0, 15, 16]


def find_ca(zst, fpath, gorder):
    """Get the contributing area"""
    df = zst[(zst["fpath"] == fpath) & (zst["gridorder"] == gorder)]
    if len(df.index) == 1:
        return df.iloc[0]["area"]
    # Search backwards until we find!
    for _gorder in range(gorder - 1, 0, -1):
        df = zst[(zst["fpath"] == fpath) & (zst["gridorder"] == _gorder)]
        if len(df.index) == 1:
            return df.iloc[0]["area"]
    print("Whoa, double failure!")
    return None


def dohuc(huc):
    """Do what we need to do for this huc"""
    cursor = PGCONN.cursor()
    zdbf = Dbf5("zst%s.dbf" % (huc,), codec="utf-8")
    zst = zdbf.to_dataframe()
    zst.columns = ["value", "count", "area", "max", "fpath", "gridorder"]
    zst.sort_values(["fpath", "gridorder"], inplace=True, ascending=True)
    # print(zst)
    df = read_postgis(
        """
    SELECT fpath, fid, st_transform(geom, 4326) as geo, huc_12 from flowpaths
    where huc_12 = %s and scenario = 0
    """,
        PGCONN,
        params=(huc,),
        geom_col="geo",
        index_col="fpath",
    )
    for col in ["F0_lon", "F0_lat", "F0_elev"]:
        df[col] = None
    for gorder in range(1, 7):
        df["G%s_elev" % (gorder,)] = None
        df["G%s_len" % (gorder,)] = None
        df["G%s_contribarea" % (gorder,)] = None
    for ofe in range(1, 18):
        df["ofe%s_pos" % (ofe,)] = None
    for fpath, row in df.iterrows():
        # 1) lat/lon of 'F0' first point
        (df.at[fpath, "F0_lon"], df.at[fpath, "F0_lat"]) = np.asarray(
            row["geo"].xy
        )[:, 0]
        # 3) elevation of F0 and G1 through G6 nodes
        for gorder in range(1, 7):
            # Contributing area
            df.at[fpath, "G%s_contribarea" % (gorder,)] = find_ca(
                zst, fpath, gorder
            )
            cursor.execute(
                """
            select max(elevation), min(elevation), max(length)
            from flowpaths p JOIN flowpath_points t on (p.fid = t.flowpath)
            where p.scenario = %s and huc_12 = %s and fpath = %s
            """,
                (SCEN2CODE[gorder], huc, fpath),
            )
            row2 = cursor.fetchone()
            df.at[fpath, "F0_elev"] = row2[0]  # overwrite each time
            df.at[fpath, "G%s_elev" % (gorder,)] = row2[1]
            # 4) horizontal distance from F0 to G1-G6
            df.at[fpath, "G%s_len" % (gorder,)] = row2[2]
        # 5) OFE positions along this path
        slpfn = "/i/%s/slp/%s/%s/%s_%s.slp" % (
            SCEN2CODE[6],
            huc[:8],
            huc[8:],
            huc,
            fpath,
        )
        lines = open(slpfn).readlines()
        ofes = int(lines[5])
        pos = 0
        for ofe, ln in enumerate(range(7, 7 + ofes * 2, 2)):
            pos += float(lines[ln].split()[1])
            df.at[fpath, "ofe%s_pos" % (ofe + 1,)] = pos
    del df["geo"]
    del df["fid"]
    # 6) Generic properties, perhaps can ignore?
    return df


def main():
    """Main Function"""
    dfs = [dohuc(huc) for huc in HUCS]
    df = pd.concat(dfs)
    df.to_csv("result.csv")


if __name__ == "__main__":
    main()
