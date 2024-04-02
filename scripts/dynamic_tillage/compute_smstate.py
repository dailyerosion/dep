"""
Process DEP Soil Moisture to create a state file.

Division of labor and this can run much earlier for the Dynamic Tillage
workflow.
"""

import os
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool

import click
import geopandas as gpd
import pandas as pd
from pydep.io.dep import read_wb
from pyiem.database import get_sqlalchemy_conn
from pyiem.util import logger
from sqlalchemy import text
from tqdm import tqdm

LOG = logger()


def job(huc12, dates):
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
    for flowpath in df["fpath"].unique():
        flowpath = int(flowpath)
        wbfn = f"/i/0/wb/{huc12[:8]}/{huc12[8:]}/{huc12}_{flowpath}.wb"
        if not os.path.isfile(wbfn):
            continue
        try:
            smdf = read_wb(wbfn)
        except Exception as exp:
            raise ValueError(f"Read {wbfn} failed") from exp
        smdf = smdf[smdf["date"].isin(dates)]
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
    return None


@click.command()
@click.option("--date", "dt", type=click.DateTime(), help="Date to process")
@click.option("--huc12", type=str, help="HUC12 to process")
@click.option("--year", type=int, help="Year to process 4/14 through 6/5")
def main(dt, huc12, year):
    """Go Main Go."""
    if dt is None:
        dates = pd.date_range(f"{year}-04-14", f"{year}-06-05")
    else:
        dates = [pd.Timestamp(dt.date())]
    huc12limiter = "" if huc12 is None else " and huc_12 = :huc12"
    with get_sqlalchemy_conn("idep") as conn:
        huc12df = gpd.read_postgis(
            text(f"""
            SELECT geom, huc_12,
            ST_x(st_transform(st_centroid(geom), 4326)) as lon,
            ST_y(st_transform(st_centroid(geom), 4326)) as lat
            from huc12 where scenario = 0 {huc12limiter}
            """),
            conn,
            params={"huc12": huc12},
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

        for _huc12 in huc12df.index.values:
            pool.apply_async(
                job, (_huc12, dates), callback=_cb, error_callback=_eb
            )
        pool.close()
        pool.join()

    df = pd.concat(dfs).reset_index().drop(columns=["index"])
    for ddt, dfdate in df.groupby("date"):
        dfdate.to_feather(f"smstate{ddt:%Y%m%d}.feather")


if __name__ == "__main__":
    main()
