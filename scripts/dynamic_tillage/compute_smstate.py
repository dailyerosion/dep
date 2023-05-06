"""
Process DEP Soil Moisture to create a state file.

Division of labor and this can run much earlier for the Dynamic Tillage
workflow.
"""
import os
import sys
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool

import geopandas as gpd
import pandas as pd
from pydep.io.dep import read_wb
from pyiem.util import get_sqlalchemy_conn, logger
from sqlalchemy import text
from tqdm import tqdm

LOG = logger()


def job(huc12, year):
    """Do work for a HUC12"""
    with get_sqlalchemy_conn("idep") as conn:
        # Build up cross reference of fields and flowpath/OFEs
        df = pd.read_sql(
            text(
                """
                select o.ofe, p.fpath, o.fbndid, g.plastic_limit
                from flowpaths p, flowpath_ofes o, gssurgo g
                WHERE o.flowpath = p.fid and p.huc_12 = :huc12
                and p.scenario = 0 and o.gssurgo_id = g.id
            """
            ),
            conn,
            params={"huc12": huc12},
            index_col=None,
        )
    dfs = []
    sts = pd.Timestamp(f"{year}/04/14")  # Need "yesterday"
    ets = pd.Timestamp(f"{year}/06/01")
    for flowpath in df["fpath"].unique():
        flowpath = int(flowpath)
        wbfn = f"/i/0/wb/{huc12[:8]}/{huc12[8:]}/{huc12}_{flowpath}.wb"
        if not os.path.isfile(wbfn):
            continue
        try:
            smdf = read_wb(wbfn)
        except Exception as exp:
            raise ValueError(f"Read {wbfn} failed") from exp
        smdf = smdf[(smdf["date"] >= sts) & (smdf["date"] <= ets)]
        # Each flowpath + ofe should be associated with a fbndid
        for ofe, gdf in smdf.groupby("ofe"):
            fbndid = df[(df["fpath"] == flowpath) & (df["ofe"] == ofe)].iloc[
                0
            ]["fbndid"]
            smdf.loc[gdf.index, "fbndid"] = fbndid
        dfs.append(smdf[["fbndid", "date", "sw1"]])  # save space
    if dfs:
        df = pd.concat(dfs)
        df["huc12"] = huc12
        return df


def main(argv):
    """Go Main Go."""
    year = int(argv[1])
    with get_sqlalchemy_conn("idep") as conn:
        huc12df = gpd.read_postgis(
            """
            SELECT geom, huc_12,
            ST_x(st_transform(st_centroid(geom), 4326)) as lon,
            ST_y(st_transform(st_centroid(geom), 4326)) as lat
            from huc12 where scenario = 0
            """,
            conn,
            geom_col="geom",
            index_col="huc_12",
        )
    progress = tqdm(total=len(huc12df.index))
    dfs = []

    def _cb(res):
        """Success."""
        progress.update()
        if res is not None:
            dfs.append(res)

    with ThreadPool(min([4, cpu_count() / 2])) as pool:

        def _eb(error):
            """Failure."""
            print(error)
            pool.terminate()

        for huc12 in huc12df.index.values:
            pool.apply_async(
                job, (huc12, year), callback=_cb, error_callback=_eb
            )
        pool.close()
        pool.join()

    df = pd.concat(dfs).reset_index().drop(columns=["index"])
    df.to_feather(f"smstate{year}.feather")


if __name__ == "__main__":
    main(sys.argv)
