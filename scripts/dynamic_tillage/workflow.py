"""Dynamic Tillage Workflow.

On a given date between 15 April and 4 June, we will attempt to plant or till
fields within a HUC12.  We run this script at 9 PM and needs to be done by
about 12:30 AM.

The `bootstrap_year.py` script creates database entries with default June
dates and dates that may not be needed given the actual tillage in play.

"""

import os
import shutil
import subprocess
import threading
from datetime import timedelta
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool

import click
import geopandas as gpd
import numpy as np
import pandas as pd
from pyiem.database import get_dbconnc, get_sqlalchemy_conn
from pyiem.iemre import SOUTH, WEST, daily_offset
from pyiem.util import archive_fetch, logger, ncopen
from sqlalchemy import text
from tqdm import tqdm

LOG = logger()
CPU_COUNT = min([4, cpu_count() / 2])
PROJDIR = "/opt/dep/prj2wepp"
EXE = f"{PROJDIR}/prj2wepp"


def setup_thread():
    """Ensure that we have temp folders and sym links constructed."""
    mydir = f"tmp{threading.get_native_id()}"
    os.makedirs(f"{mydir}/wepp/runs", exist_ok=True)
    for dn in ["data", "output", "wepp", "weppwin"]:
        subprocess.call(["ln", "-s", f"../../wepp/{dn}"], cwd=f"{mydir}/wepp")
    subprocess.call(["ln", "-s", "../userdb"], cwd=mydir)


def prj2wepp(huc12, fpath):
    """Run prj2wepp."""
    mydir = f"tmp{threading.get_native_id()}"
    fn = f"/i/0/prj/{huc12[:8]}/{huc12[8:]}/{huc12}_{fpath:.0f}.prj"
    testfn = os.path.basename(fn)[:-4]
    cmd = [EXE, fn, testfn, f"{PROJDIR}/{mydir}/wepp", "no"]
    with subprocess.Popen(
        cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, cwd=mydir
    ) as proc:
        # Need to block the above
        stdout = proc.stdout.read()
        stderr = proc.stderr.read()
        if not os.path.isfile(f"{mydir}/{testfn}.man"):
            print("bzzzz", testfn)
            print(" ".join(cmd))
            print(stdout.decode("ascii"))
            print(stderr.decode("ascii"))
            return False
        # This generates .cli, .man, .run, .slp, .sol
        # We need the .man , .slp , .sol from this process
        # slp is generated in flowpath2prj
        for suffix in ["man", "sol"]:
            shutil.copyfile(
                f"{mydir}/{testfn}.{suffix}", fn.replace("prj", suffix)
            )
        for suffix in ["cli", "man", "run", "slp", "sol"]:
            os.unlink(f"{mydir}/{testfn}.{suffix}")
    return True


def edit_rotfile(year, huc12, row):
    """Edit up our .rot files."""
    yearindex = str(year - 2007 + 1)
    rotfn = (
        f"/i/0/rot/{huc12[:8]}/{huc12[8:]}/"
        f"{huc12}_{row['fpath']:.0f}_{row['ofe']:.0f}.rot"
    )
    with open(rotfn, encoding="ascii") as fh:
        lines = fh.readlines()
    dates = [row["till1"], row["till2"], row["till3"], row["plant"]]
    for i, line in enumerate(lines):
        pos = line.find(f" {yearindex} ")  # false positives
        if pos == -1:
            continue
        tokens = line.split()
        if (
            tokens[2] == yearindex
            and int(tokens[0]) < 7
            and tokens[4].startswith(("Tillage", "Plant"))
        ):
            thisdt = row["plant"]
            if tokens[4] == "Tillage":
                thisdt = dates.pop(0)
            if thisdt is None:
                thisdt = row["plant"]
            lines[i] = (
                f"{thisdt:%-m %-d} {yearindex} " f"{' '.join(tokens[3:])}\n"
            )
    with open(rotfn, "w", encoding="ascii") as fh:
        fh.write("".join(lines))


def do_huc12(dt, huc12, smdf):
    """Go Main Go."""
    with get_sqlalchemy_conn("idep") as conn:
        # build up the cross reference of everyhing we need to know
        df = gpd.read_postgis(
            text(
                """
            with myofes as (
                select o.ofe, p.fpath, o.fbndid, g.plastic_limit
                from flowpaths p, flowpath_ofes o, gssurgo g
                WHERE o.flowpath = p.fid and p.huc_12 = :huc12
                and p.scenario = 0 and o.gssurgo_id = g.id),
            agg as (
                SELECT ofe, fpath, f.fbndid, plastic_limit, f.geom, f.landuse,
                f.management, f.acres, f.field_id
                from fields f LEFT JOIN myofes m on (f.fbndid = m.fbndid)
                WHERE f.huc12 = :huc12 and f.isag ORDER by fpath, ofe)
            select a.*, o.till1, o.till2, o.till3, o.plant, o.year,
            plant >= :dt as plant_needed,
            coalesce(
                greatest(till1, till2, till3) >= :dt, false) as till_needed,
            false as operation_done
            from agg a, field_operations o
            where a.field_id = o.field_id and o.year = :year
            and o.plant is not null
            """
            ),
            conn,
            params={"huc12": huc12, "year": dt.year, "dt": dt},
            index_col=None,
            geom_col="geom",
        )
    if df.empty:
        LOG.info("No fields found for %s", huc12)
        return

    fields = df.groupby("fbndid").first().copy()

    # Soil Moisture check.  We are not modeling every field, so we are a
    # bit generous here, are 50% of **model** fields below plastic_limit?
    sw1 = fields[fields["plastic_limit"].notnull()].join(
        smdf[["fbndid", "sw1"]].groupby("fbndid").min(), on="fbndid"
    )[["sw1", "plastic_limit"]]
    hits = (sw1["sw1"] < sw1["plastic_limit"]).sum()
    if hits < len(sw1.index) / 2:
        LOG.info(
            "HUC12: %s has %s/%s fields below plastic limit",
            huc12,
            hits,
            len(sw1.index),
        )
        return

    # Compute things for year
    char_at = (dt.year - 2007) + 1
    fields["geom"].crs = 5070
    fields["crop"] = fields["landuse"].str.slice(char_at - 1, char_at)
    fields["tillage"] = fields["management"].str.slice(char_at - 1, char_at)

    total_acres = fields["acres"].sum()
    limit = total_acres / 10.0

    acres_tilled = 0
    # Work on tillage first, so to avoid planting on tilled fields
    for fbndid, row in fields[fields["till_needed"]].iterrows():
        acres_tilled += row["acres"]
        fields.at[fbndid, "operation_done"] = True
        for i in [1, 2, 3]:
            if row[f"till{i}"] >= dt:
                fields.at[fbndid, f"till{i}"] = dt
                break
        if acres_tilled > limit:
            break

    # Now we need to plant
    acres_planted = 0
    for fbndid, row in fields[fields["plant_needed"]].iterrows():
        if row["operation_done"]:
            continue
        acres_planted += row["acres"]
        fields.at[fbndid, "plant"] = dt
        fields.at[fbndid, "operation_done"] = True
        if acres_planted > limit:
            break

    LOG.info(
        "plant: %.1f[%.1f%%] tilled: %.1f[%.1f%%] total: %.1f",
        acres_planted,
        acres_planted / total_acres * 100.0,
        acres_tilled,
        acres_tilled / total_acres * 100.0,
        total_acres,
    )

    # Update the database
    df2 = fields[fields["operation_done"]].reset_index()
    if df2.empty:
        return
    conn, cursor = get_dbconnc("idep")
    cursor.executemany(
        "update field_operations set plant = %s, till1 = %s, "
        "till2 = %s, till3 = %s where field_id = %s and year = %s",
        df2[
            ["plant", "till1", "till2", "till3", "field_id", "year"]
        ].itertuples(index=False),
    )
    # FIXME cursor.close()
    # FIXME conn.commit()

    # Update the .rot files, when necessary
    df2 = df[(df["field_id"].isin(df2["field_id"])) & (df["ofe"].notna())]
    for _, row in df2.iterrows():
        edit_rotfile(dt.year, huc12, row)
    for fpath in df2["fpath"].unique():
        prj2wepp(huc12, fpath)


def estimate_soiltemp(huc12df, dt):
    """Write mean GFS soil temperature C into huc12df."""
    ppath = f"{dt:%Y/%m/%d}/model/gfs/gfs_{dt:%Y%m%d}00_iemre.nc"
    with archive_fetch(ppath) as ncfn, ncopen(ncfn) as nc:
        tsoil = np.mean(nc.variables["tsoil"][1:7], axis=0) - 273.15
        y = np.digitize(huc12df["lat"].values, nc.variables["lat"][:])
        x = np.digitize(huc12df["lon"].values, nc.variables["lon"][:])
        for i, idx in enumerate(huc12df.index.values):
            huc12df.at[idx, "tsoil"] = tsoil[y[i], x[i]]


def estimate_rainfall(huc12df, dt):
    """Figure out our rainfall estimate."""
    tidx = daily_offset(dt)
    with ncopen(f"/mesonet/data/mrms/{dt:%Y}_mrms_daily.nc") as nc:
        p01d = nc.variables["p01d"][tidx].filled(0)
    for idx, row in huc12df.iterrows():
        y = int((row["lat"] - SOUTH) * 100.0)
        x = int((row["lon"] - WEST) * 100.0)
        huc12df.at[idx, "precip_mm"] = p01d[y, x]


@click.command()
@click.option("--scenario", type=int, default=0)
@click.option("--date", "dt", type=click.DateTime(), required=True)
@click.option("--huc12", type=str, required=False)
def main(scenario, dt, huc12):
    """Go Main Go."""
    # Deal with dates not datetime
    dt = dt.date()
    LOG.info("Processing %s for scenario %s", dt, scenario)
    huc12_filter = "" if huc12 is None else " and huc_12 = :huc12"
    with get_sqlalchemy_conn("idep") as conn:
        huc12df = gpd.read_postgis(
            text(f"""
            SELECT geom, huc_12,
            false as limited_by_precip,
            false as limited_by_soiltemp,
            false as limited_by_soilmoisture,
            false as limited,
            ST_x(st_transform(st_centroid(geom), 4326)) as lon,
            ST_y(st_transform(st_centroid(geom), 4326)) as lat
            from huc12 where scenario = :scenario {huc12_filter}
            """),
            conn,
            params={"scenario": scenario, "huc12": huc12},
            geom_col="geom",
            index_col="huc_12",
        )
    # Estimate today's rainfall so to delay triggers
    estimate_rainfall(huc12df, dt)
    # Any HUC12 over 10mm gets skipped
    huc12df.loc[huc12df["precip_mm"] > 9.9]["limited_by_precip"] = True
    # Estimate soil temperature via GFS forecast
    estimate_soiltemp(huc12df, dt)
    # Any HUC12 under 6C gets skipped
    huc12df.loc[huc12df["tsoil"] > 5.9]["limited_by_soiltemp"] = True
    # The soil moisture state is the day before
    yesterday = dt - timedelta(days=1)
    smdf = pd.read_feather(f"smstate{yesterday:%Y%m%d}.feather")

    # Need to run from project dir so local userdb is found
    os.chdir(PROJDIR)

    progress = tqdm(total=len(huc12df.index))
    LOG.warning("%s threads for %s huc12s", CPU_COUNT, len(huc12df.index))
    with ThreadPool(CPU_COUNT, initializer=setup_thread) as pool:

        def _error(exp):
            """Uh oh."""
            LOG.warning("Got exception, aborting....")
            LOG.exception(exp)
            pool.terminate()

        def _job(huc12):
            """Do the job."""
            progress.set_description(huc12)
            do_huc12(dt, huc12, smdf[smdf["huc12"] == huc12])
            progress.update()

        for huc12 in huc12df.index.values:
            pool.apply_async(_job, (huc12,), error_callback=_error)
        pool.close()
        pool.join()


if __name__ == "__main__":
    main()
