"""Dynamic Tillage Workflow.

On a given date between 11 April and 10 June, we will attempt to plant or till
fields within a HUC12.  We run this script at 9 PM and needs to be done by
about 12:30 AM.

The `bootstrap_year.py` script creates database entries with default June
dates and dates that may not be needed given the actual tillage in play.

"""

import os
import shutil
import subprocess
import tempfile
import threading
from datetime import date, datetime, timedelta
from multiprocessing import cpu_count
from multiprocessing.pool import Pool
from typing import Tuple

import click
import geopandas as gpd
import numpy as np
import pandas as pd
from pyiem.database import get_dbconnc, get_sqlalchemy_conn
from pyiem.iemre import SOUTH, WEST, daily_offset, get_daily_mrms_ncname
from pyiem.util import archive_fetch, logger, ncopen
from sqlalchemy import text
from tqdm import tqdm

pd.set_option("future.no_silent_downcasting", True)
LOG = logger()
CPU_COUNT = min([4, cpu_count() / 2])
HUC12STATUSDIR = "/mnt/idep2/data/huc12status"
PROJDIR = "/opt/dep/prj2wepp"
EXE = f"{PROJDIR}/prj2wepp"
RUNTIME = {
    "edit_rotfile": False,
    "run_prj2wepp": False,
}


def setup_thread():
    """Ensure that we have temp folders and sym links constructed."""
    tmpdir = tempfile.mkdtemp()
    # Store the reference for later use
    threading.current_thread().tmpdir = tmpdir
    os.makedirs(f"{tmpdir}/wepp/runs", exist_ok=True)
    for dn in ["data", "output", "wepp", "weppwin"]:
        subprocess.call(
            ["ln", "-s", f"{PROJDIR}/wepp/{dn}"], cwd=f"{tmpdir}/wepp"
        )


def prj2wepp(huc12, fpath):
    """Run prj2wepp."""
    mydir = threading.current_thread().tmpdir
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


def do_huc12(dt, huc12) -> Tuple[int, int]:
    """Process a HUC12.

    Returns the number of acres planted and tilled.  A negative value is a
    sentinel that the HUC12 failed due to soil moisture constraint.
    """
    dbcolidx = dt.year - 2007 + 1
    crops = ["B", "C", "L", "W"]
    tillagerate = 0.10
    maxrate = 0.06
    # If before April 20, we only plant corn
    if f"{dt:%m%d}" < "0420":
        crops = ["C"]
        maxrate = 0.03  # Life choice
    elif f"{dt:%m%d}" > "0510":
        maxrate = 0.10
    with get_sqlalchemy_conn("idep") as conn:
        # build up the cross reference of everyhing we need to know
        df = pd.read_sql(
            text(
                """
            with myofes as (
                select o.ofe, p.fpath, o.fbndid
                from flowpaths p, flowpath_ofes o, gssurgo g
                WHERE o.flowpath = p.fid and p.huc_12 = :huc12
                and p.scenario = 0 and o.gssurgo_id = g.id),
            agg as (
                SELECT ofe, fpath, f.fbndid, f.landuse,
                f.management, f.acres, f.field_id
                from fields f LEFT JOIN myofes m on (f.fbndid = m.fbndid)
                WHERE f.huc12 = :huc12 and
                substr(landuse, :dbcolidx, 1) = ANY(:crops)
                ORDER by fpath, ofe)
            select a.*, o.till1, o.till2, o.till3, o.plant, o.year,
            plant >= :dt as plant_needed,
            coalesce(
                greatest(till1, till2, till3) >= :dt, false) as till_needed,
            false as operation_done, 0 as sw1
            from agg a, field_operations o
            where a.field_id = o.field_id and o.year = :year
            and o.plant is not null
            """
            ),
            conn,
            params={
                "huc12": huc12,
                "year": dt.year,
                "dt": dt,
                "crops": crops,
                "dbcolidx": dbcolidx,
            },
            index_col=None,
        )
    if df.empty:
        LOG.debug(
            "No fields found for %s %s %s %s",
            huc12,
            dt,
            crops,
            dbcolidx,
        )
        return 0, 0

    # Screen out when there are no fields that need planting or tilling
    if (
        not df["plant_needed"].any()
        and not df["till_needed"].any()
        and f"{dt:%m%d}" < "0614"
    ):
        LOG.debug("No fields need planting or tilling for %s", huc12)
        return 0, 0

    # There is an entry per OFE + field combination, but we only want 1
    fields = df.groupby("fbndid").first().copy()

    # We could be re-running for a given date, so we first total up the acres
    acres_planted = fields[fields["plant"] == dt]["acres"].sum()
    acres_tilled = (
        fields[fields["till1"] == dt]["acres"].sum()
        + fields[fields["till2"] == dt]["acres"].sum()
        + fields[fields["till3"] == dt]["acres"].sum()
    )
    if pd.isnull(acres_planted):
        acres_planted = 0
    if pd.isnull(acres_tilled):
        acres_tilled = 0

    mud_it_in = f"{dt:%m%d}" >= "0610"

    # Compute things for year
    char_at = (dt.year - 2007) + 1
    fields["crop"] = fields["landuse"].str.slice(char_at - 1, char_at)
    fields["tillage"] = fields["management"].str.slice(char_at - 1, char_at)

    total_acres = fields["acres"].sum()
    # NB: Crude assessment of NASS peak daily planting rate, was 10%
    limit = (total_acres * tillagerate) if not mud_it_in else total_acres + 1

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

    # Redine limit for planting
    limit = (total_acres * maxrate) if not mud_it_in else total_acres + 1
    # Now we need to plant
    for fbndid, row in fields[fields["plant_needed"]].iterrows():
        # We can't plant fields that were tilled or need tillage GH251
        if row["operation_done"] or row["till_needed"]:
            continue
        acres_planted += row["acres"]
        fields.at[fbndid, "plant"] = dt
        fields.at[fbndid, "operation_done"] = True
        if acres_planted > limit:
            break

    LOG.debug(
        "plant: %.1f[%.1f%%] tilled: %.1f[%.1f%%] total: %.1f",
        acres_planted,
        acres_planted / total_acres * 100.0,
        acres_tilled,
        acres_tilled / total_acres * 100.0,
        total_acres,
    )

    # Update the database
    df2 = fields[fields["operation_done"]].reset_index()
    if not df2.empty:
        conn, cursor = get_dbconnc("idep")
        cursor.executemany(
            "update field_operations set plant = %s, till1 = %s, "
            "till2 = %s, till3 = %s where field_id = %s and year = %s",
            df2[
                ["plant", "till1", "till2", "till3", "field_id", "year"]
            ].itertuples(index=False),
        )
        cursor.close()
        conn.commit()
    # Update all the .rot files
    if dt.month == 6 and dt.day == 14:
        df2 = df[df["ofe"].notna()]
    elif not df2.empty:
        df2 = df[(df["field_id"].isin(df2["field_id"])) & (df["ofe"].notna())]
    if RUNTIME["edit_rotfile"] or f"{dt:%m%d}" == "0614":
        for _, row in df2.iterrows():
            edit_rotfile(dt.year, huc12, row)
        if RUNTIME["run_prj2wepp"]:
            for fpath in df2["fpath"].unique():
                prj2wepp(huc12, fpath)
    return acres_planted, acres_tilled


def estimate_soiltemp(huc12df, dt):
    """Write mean GFS soil temperature C into huc12df."""
    # Look back from 12z at most 24 hours for a file to use
    z12 = datetime(dt.year, dt.month, dt.day, 12)
    for offset in range(0, 25, 6):
        now = z12 - timedelta(hours=offset)
        ppath = f"{now:%Y/%m/%d}/model/gfs/gfs_{now:%Y%m%d%H}_iemre.nc"
        with archive_fetch(ppath) as ncfn:
            if ncfn is None:
                continue
            LOG.info("Using GFS@%s for soil temperature", now)
            with ncopen(ncfn) as nc:
                tmin = np.min(nc.variables["tsoil"][1:7], axis=0) - 273.15
                tavg = np.mean(nc.variables["tsoil"][1:7], axis=0) - 273.15
                tmax = np.max(nc.variables["tsoil"][1:7], axis=0) - 273.15
                y = np.digitize(huc12df["lat"].values, nc.variables["lat"][:])
                x = np.digitize(huc12df["lon"].values, nc.variables["lon"][:])
                for i, idx in enumerate(huc12df.index.values):
                    # The crude GFS may have this cell in the great lakes, so
                    # we do a crude check
                    off = 0 if tmin[y[i], x[i]] > -40 else 5
                    huc12df.at[idx, "tsoil_min"] = tmin[y[i] - off, x[i] - off]
                    huc12df.at[idx, "tsoil_avg"] = tavg[y[i] - off, x[i] - off]
                    huc12df.at[idx, "tsoil_max"] = tmax[y[i] - off, x[i] - off]
                break


def estimate_rainfall(huc12df: pd.DataFrame, dt: date):
    """Figure out our rainfall estimate."""
    tidx = daily_offset(dt)
    ncfn = get_daily_mrms_ncname(dt.year)
    depncfn = ncfn.replace("daily", "dep")
    if os.path.isfile(depncfn):
        ncfn = depncfn
        tidx = daily_offset(dt) - daily_offset(dt.replace(month=4, day=11))
    LOG.info("Using %s[tidx:%s] for precip", ncfn, tidx)
    with ncopen(ncfn) as nc:
        p01d = nc.variables["p01d"][tidx].filled(0)
    for idx, row in huc12df.iterrows():
        y = int((row["lat"] - SOUTH) * 100.0)
        x = int((row["lon"] - WEST) * 100.0)
        huc12df.at[idx, "precip_mm"] = p01d[y, x]


def job(arg):
    """Do the job."""
    dt, huc12 = arg
    planted, tilled = do_huc12(dt, huc12)
    return huc12, planted, tilled


@click.command()
@click.option("--scenario", type=int, default=0)
@click.option("--date", "dt", type=click.DateTime(), required=True)
@click.option("--huc12", type=str, required=False)
@click.option("--edit_rotfile", "edr", type=bool, default=False)
@click.option("--run_prj2wepp", type=bool, default=False)
def main(scenario, dt, huc12, edr, run_prj2wepp):
    """Go Main Go."""
    RUNTIME["edit_rotfile"] = edr
    RUNTIME["run_prj2wepp"] = run_prj2wepp
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
            99.9 as tsoil_min,
            99.9 as tsoil_avg,
            99.9 as tsoil_max,
            ST_x(st_transform(st_centroid(geom), 4326)) as lon,
            ST_y(st_transform(st_centroid(geom), 4326)) as lat
            from huc12 where scenario = :scenario {huc12_filter}
            """),
            conn,
            params={"scenario": scenario, "huc12": huc12},
            geom_col="geom",
            index_col="huc_12",
        )
    huc12df["tilled"] = pd.NA
    huc12df["planted"] = pd.NA

    # After June 10th, we mud it in.
    if f"{dt:%m%d}" < "0610":
        # Estimate today's rainfall so to delay triggers
        estimate_rainfall(huc12df, dt)
        # Any HUC12 over 10mm gets skipped
        huc12df.loc[huc12df["precip_mm"] > 9.9, "limited_by_precip"] = True
        # Estimate soil temperature via GFS forecast
        estimate_soiltemp(huc12df, dt)
        # Any HUC12 under 6C gets skipped
        huc12df.loc[huc12df["tsoil_avg"] < 6, "limited_by_soiltemp"] = True
        # The soil moisture state is the day before
        yesterday = dt - timedelta(days=1)
        smdf = pd.read_feather(
            f"/mnt/idep2/data/smstate/{yesterday:%Y}/"
            f"smstate{yesterday:%Y%m%d}.feather"
        )
        # Only consider rows that are in either Corn or Soybean
        smdf = smdf[smdf["crop"].isin(["C", "S"])]
        for huc12, gdf in smdf.groupby("huc12"):
            if huc12 not in huc12df.index:
                continue
            # Require that 50% of modelled OFEs are 0.8 of plastic limit
            toowet = gdf["sw1"].gt(gdf["plastic_limit"] * 0.8).sum()
            if toowet > (len(gdf.index) * 0.9):
                huc12df.at[huc12, "limited_by_soilmoisture"] = True

    # restrict to HUC12s that are not limited
    huc12df["limited"] = (
        huc12df["limited_by_precip"]
        | huc12df["limited_by_soiltemp"]
        | huc12df["limited_by_soilmoisture"]
    )
    LOG.info(
        "%s/%s HUC12s failed precip + soiltemp check",
        huc12df["limited"].sum(),
        len(huc12df.index),
    )

    # Need to run from project dir so local userdb is found
    os.chdir(PROJDIR)

    queue = []
    for huc12 in huc12df[~huc12df["limited"]].index:
        queue.append((dt, huc12))

    LOG.warning("%s processes for %s huc12s", CPU_COUNT, len(queue))
    progress = tqdm(total=len(queue), disable=not os.isatty(1))

    with Pool(CPU_COUNT, initializer=setup_thread) as pool:
        for huc12, planted, tilled in pool.imap_unordered(job, queue):
            progress.set_description(huc12)
            progress.update()
            huc12df.at[huc12, "planted"] = planted
            huc12df.at[huc12, "tilled"] = tilled

        pool.close()
        pool.join()

    LOG.warning(
        "Planted: %.1f Tilled: %.1f Limited SM: %s Precip: %s Temp: %s",
        huc12df["planted"].sum(),
        huc12df["tilled"].sum(),
        huc12df["limited_by_soilmoisture"].sum(),
        huc12df["limited_by_precip"].sum(),
        huc12df["limited_by_soiltemp"].sum(),
    )

    # save a debug output file
    mydir = f"{HUC12STATUSDIR}/{dt:%Y}"
    os.makedirs(mydir, exist_ok=True)
    if len(huc12df.index) == 1:  # Don't save when run for single huc12
        return
    huc12df.drop(columns="geom").to_feather(f"{mydir}/{dt:%Y%m%d}.feather")


if __name__ == "__main__":
    main()
