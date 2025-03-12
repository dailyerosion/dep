"""
Process DEP Soil Moisture to create a state file.

Division of labor and this can run much earlier for the Dynamic Tillage
workflow.

Crontab entry at 3 PM Central for the previous date.
"""

import os
import tempfile
from functools import partial
from multiprocessing import cpu_count
from multiprocessing.pool import Pool

import click
import geopandas as gpd
import pandas as pd
from pyiem.database import get_sqlalchemy_conn, sql_helper
from pyiem.util import logger
from tqdm import tqdm

from pydep.io.dep import read_wb

LOG = logger()


def job(dates, tmpdir, huc12) -> int:
    """Do work for a HUC12"""
    with get_sqlalchemy_conn("idep") as conn:
        # Build up cross reference of fields and flowpath/OFEs
        # Dates are currently always for the same year
        huc12df = pd.read_sql(
            sql_helper(
                """
    select o.ofe, p.fpath, o.fbndid,
    case when g.plastic_limit < 40 then
        g.plastic_limit else
        g.wepp_min_sw + (g.wepp_max_sw - g.wepp_min_sw) * 0.42
    end as plastic_limit,
    p.fpath || '_' || o.ofe as combo, p.huc_12 as huc12,
    substr(o.landuse, :charat, 1) as crop
    from flowpaths p, flowpath_ofes o, gssurgo g
    WHERE o.flowpath = p.fid and p.huc_12 = :huc12
    and p.scenario = 0 and o.gssurgo_id = g.id
            """
            ),
            conn,
            params={"huc12": huc12, "charat": dates[0].year - 2007 + 1},
            index_col=None,
        )
    huc12df["sw1"] = pd.NA
    # expand the cross reference to include the dates, so the original
    # data frame now has one row per date per metadata row
    entries = len(huc12df.index)
    huc12df = huc12df.loc[huc12df.index.repeat(len(dates))]
    huc12df["date"] = pd.concat([dates] * entries, ignore_index=True).values
    # need to have a valid index to make magic below work
    huc12df = huc12df.reset_index(drop=True)

    reads = 0
    for flowpath, flowpathdf in huc12df.groupby("fpath"):
        wbfn = f"/i/0/wb/{huc12[:8]}/{huc12[8:]}/{huc12}_{flowpath}.wb"
        if not os.path.isfile(wbfn):
            continue
        try:
            reads += 1
            smdf = read_wb(wbfn)
        except Exception as exp:
            raise ValueError(f"Read {wbfn} failed") from exp
        smdf = smdf[smdf["date"].isin(dates)]
        for ofe, gdf in smdf.groupby("ofe"):
            ofedf = flowpathdf[flowpathdf["ofe"] == ofe]
            # assume that we are aligned here, gasp
            huc12df.loc[ofedf.index, "sw1"] = gdf["sw1"].values
    huc12df.to_feather(f"{tmpdir}/{huc12}.feather")
    return reads


@click.command()
@click.option("--date", "dt", type=click.DateTime(), help="Date to process")
@click.option("--huc12", type=str, help="HUC12 to process")
@click.option("--year", type=int, help="Year to process 4/10 through 6/15")
def main(dt, huc12, year):
    """Go Main Go."""
    if dt is None:
        dates = pd.Series(pd.date_range(f"{year}-04-10", f"{year}-06-15"))
    else:
        dates = pd.Series([pd.Timestamp(dt.date())])

    outdir = f"/mnt/idep2/data/smstate/{dates[0]:%Y}"
    os.makedirs(outdir, exist_ok=True)

    huc12limiter = "" if huc12 is None else " and huc_12 = :huc12"
    with get_sqlalchemy_conn("idep") as conn:
        huc12df = gpd.read_postgis(
            sql_helper(
                """
            SELECT geom, huc_12,
            ST_x(st_transform(st_centroid(geom), 4326)) as lon,
            ST_y(st_transform(st_centroid(geom), 4326)) as lat
            from huc12 where scenario = 0 {huc12limiter}
            """,
                huc12limiter=huc12limiter,
            ),
            conn,
            params={"huc12": huc12},
            geom_col="geom",
            index_col="huc_12",
        )
    progress = tqdm(total=len(huc12df.index), disable=not os.isatty(1))
    with (
        Pool(min([8, int(cpu_count() / 2)])) as pool,
        tempfile.TemporaryDirectory() as tmpdir,
    ):
        func = partial(job, dates, tmpdir)
        for _ in pool.imap_unordered(func, huc12df.index.values):
            progress.update(1)
        pool.close()
        pool.join()

        df = pd.concat(
            pd.read_feather(f"{tmpdir}/{huc12}.feather")
            for huc12 in huc12df.index.values
        )
    for ddt, dfdate in df.groupby("date"):
        dfdate.to_feather(f"{outdir}/smstate{ddt:%Y%m%d}.feather")


if __name__ == "__main__":
    main()
