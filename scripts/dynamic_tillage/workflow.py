"""
Our Dynamic Tillage Workflow!

"""

import sys
from datetime import date, timedelta
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool

import geopandas as gpd
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle

# The MRMS netcdf file use the IEMRE grid domain
from pyiem.iemre import SOUTH, WEST, daily_offset
from pyiem.plot import MapPlot, figure_axes
from pyiem.util import get_dbconn, get_sqlalchemy_conn, logger, ncopen
from sqlalchemy import text
from tqdm import tqdm

LOG = logger()
CPU_COUNT = min([4, cpu_count() / 2])
MAKE_PLOTS = False
DBSET_DATE_THRESHOLD = pd.Timestamp(date.today())


def plot_map(i, dt, huc12df, fields):
    """Make a map diagnostic"""
    minx, miny, maxx, maxy = huc12df["geom"].to_crs(4326).total_bounds
    buffer = 0.01
    huc12 = huc12df.index.values[0]

    mp = MapPlot(
        title=f"DEP Planting Progress {dt:%Y %b %d} for HUC12: {huc12}",
        logo="dep",
        sector="custom",
        west=minx - buffer,
        north=maxy + buffer,
        south=miny - buffer,
        east=maxx + buffer,
        caption="Daily Erosion Project",
        continentalcolor="white",
    )
    huc12df.to_crs(mp.panels[0].crs).plot(
        ax=mp.panels[0].ax,
        aspect=None,
        facecolor="None",
        edgecolor="b",
        linewidth=2,
        zorder=100,
    )
    fields["color"] = "white"
    fields.loc[fields["till1"].notna(), "color"] = "tan"
    fields.loc[fields["plant"].notna(), "color"] = "g"
    fields.to_crs(mp.panels[0].crs).plot(
        ax=mp.panels[0].ax,
        aspect=None,
        facecolor=fields["color"],
        edgecolor="k",
        linewidth=1,
        zorder=100,
    )
    p0 = Rectangle((0, 0), 1, 1, fc="white", ec="k")
    p1 = Rectangle((0, 0), 1, 1, fc="tan", ec="k")
    p2 = Rectangle((0, 0), 1, 1, fc="g", ec="k")
    mp.panels[0].ax.legend(
        (p0, p1, p2),
        ("Awaiting", "Tilled", "Planted"),
        ncol=3,
        fontsize=11,
        loc=2,
    )

    mp.fig.savefig(f"{i:04.0f}.png")
    mp.close()


def plot_timeseries(year, df, huc12):
    """Make a diagnostic."""
    (fig, ax) = figure_axes(
        logo="dep",
        title=f"DEP {year} Tillage/Plant Operation Timing for HUC12: {huc12}",
        subtitle="<=10% Daily Rate, All Field OFEs below 0.9 Plastic Limit",
    )
    ax2 = ax.twinx()
    x = pd.date_range(f"{year}/04/15", f"{year}/06/03")
    print(df)
    ax2.bar(
        x - pd.Timedelta(hours=8),
        df["acres_planted"],
        color="#00ff00",
        alpha=0.5,
        width=0.3,
        align="edge",
        zorder=2,
    )
    ax2.bar(
        x,
        df["acres_tilled"],
        color="#ff0000",
        alpha=0.5,
        width=0.3,
        align="edge",
        zorder=2,
    )

    ax.plot(
        x,
        df["acres_not_planted"],
        color="k",
        label="Not Planted",
        zorder=3,
        lw=3,
    )
    ax.plot(x, df["acres_to_till"], color="r", label="Tillage", zorder=3, lw=3)
    ax.plot(
        x,
        df["acres_to_plant"],
        c="g",
        label="Plant",
        zorder=3,
        lw=3,
    )
    ax.set_ylabel("Acres Available for Operations")
    ax.legend(loc=1)
    ax.grid(True)
    ax.set_ylim(bottom=-10)
    ax2.set_ylim(bottom=-10)
    ax2.set_ylabel("Acreas Worked per Day (bars)")
    ax.set_zorder(ax2.get_zorder() + 1)
    ax.patch.set_visible(False)
    fig.savefig(f"{year}_timeseries.png")


def dbset(cursor, field_id, dt, col):
    """Update the database."""
    if dt >= DBSET_DATE_THRESHOLD:
        return
    cursor.execute(
        f"UPDATE field_operations SET {col} = %s WHERE field_id = %s and "
        "year = %s",
        (dt, field_id, dt.year),
    )
    if cursor.rowcount == 0:
        cursor.execute(
            f"INSERT into field_operations(field_id, year, {col}) "
            "VALUES(%s, %s, %s)",
            (field_id, dt.year, dt),
        )


def edit_rotfile(year, huc12, ofedf):
    """Edit up our .rot files."""
    yearindex = str(year - 2007 + 1)
    for _, row in ofedf.iterrows():
        dates = []
        for col in ["till1", "till2", "plant", "plant"]:  # Hack dupe plant
            if not pd.isna(row[col]):
                dates.append(row[col])
        rotfn = (
            f"/i/0/rot/{huc12[:8]}/{huc12[8:]}/"
            f"{huc12}_{row['fpath']}_{row['ofe']}.rot"
        )
        with open(rotfn, encoding="ascii") as fh:
            lines = fh.readlines()
        for i, line in enumerate(lines):
            pos = line.find(f" {yearindex} ")  # false positives
            if pos == -1:
                continue
            tokens = line.split()
            if (
                tokens[2] == yearindex
                and int(tokens[0]) < 6
                and (
                    tokens[4].startswith("Tillage")
                    or tokens[4].startswith("Plant")
                )
            ):
                lines[i] = (
                    f"{dates.pop(0):%m %d} {yearindex} "
                    f"{' '.join(tokens[3:])}\n"
                )
                if not dates:
                    break
        with open(rotfn, "w", encoding="ascii") as fh:
            fh.write("".join(lines))


def do_huc12(year, huc12, smdf):
    """Go Main Go."""
    with get_sqlalchemy_conn("idep") as conn:
        # build up the cross reference of everyhing we need to know
        df = gpd.read_postgis(
            text(
                """
            with myofes as (
                select o.ofe, p.fpath, o.fbndid,
                g.plastic_limit
                from flowpaths p, flowpath_ofes o, gssurgo g
                WHERE o.flowpath = p.fid and p.huc_12 = :huc12
                and p.scenario = 0 and o.gssurgo_id = g.id),
            agg as (
                SELECT ofe, fpath, f.fbndid, plastic_limit, f.geom, f.landuse,
                f.management, f.acres, f.field_id
                from fields f JOIN myofes m on (f.fbndid = m.fbndid)
                WHERE f.huc12 = :huc12 ORDER by fpath, ofe)
            select a.*, o.till1, o.till2, o.plant
            from agg a LEFT JOIN field_operations o on
            (a.field_id = o.field_id and o.year = :year)
            """
            ),
            conn,
            params={"huc12": huc12, "year": year},
            index_col=None,
            geom_col="geom",
        )

    # Compute things for year
    char_at = (year - 2007) + 1
    fields = df.groupby("fbndid").first().copy()
    fields["geom"].crs = 5070
    fields["crop"] = fields["landuse"].str.slice(char_at - 1, char_at)
    fields["tillage"] = fields["management"].str.slice(char_at - 1, char_at)
    # augh, Pasture
    fields = fields[fields["crop"] != "P"]

    fields["status"] = 0
    # Update status based on what has been done already
    fields.loc[fields["plant"].notna(), "status"] += 1
    fields.loc[fields["till1"].notna(), "status"] += 1
    fields.loc[fields["till2"].notna(), "status"] += 1
    fields["operations"] = 1
    fields.loc[fields["tillage"] == "2", "operations"] = 2
    fields.loc[fields["tillage"].isin(["3", "4", "5", "6"]), "operations"] = 3
    total_acres = fields["acres"].sum()
    operation_acres = (fields["operations"] * fields["acres"]).sum()
    # 10% acres can get planted and 10% of acres can get tilled
    LOG.info(
        "Theoretical min days %s", operation_acres / (total_acres / 10.0) / 2.0
    )
    limit = total_acres / 10.0

    acres_not_planted = []
    acres_to_plant = []
    acres_planted = []
    acres_to_till = []
    acres_tilled = []

    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()
    if year == DBSET_DATE_THRESHOLD.year:
        startdate = max([pd.Timestamp(f"{year}/04/15"), DBSET_DATE_THRESHOLD])
    else:
        startdate = pd.Timestamp(f"{year}/04/15")
    # NOTE once we get to 1 June, everything goes into the ground, so we need
    # three days to clear the backlog...
    for i, dt in enumerate(pd.date_range(startdate, f"{year}/06/03")):
        acres_not_planted.append(fields[fields["plant"].isna()]["acres"].sum())
        # Can we plant upto 10% of the acreage today?
        running = 0
        pop = fields[
            fields["plant"].isna()
            & ((fields["operations"] - fields["status"]) == 1)
        ]
        acres_to_plant.append(pop["acres"].sum())
        LOG.info("%s acres to plant: %s", dt, pop["acres"].sum())
        yesterday = dt - timedelta(days=1)
        # random iter
        for fbndid, row in pop.sample(frac=1).iterrows():
            # Go get the soil moisture state for yesterday as it would be
            # what is valid at 12 AM today.
            sm = smdf[(smdf["fbndid"] == fbndid) & (smdf["date"] == yesterday)]
            # Are we all below?
            if dt.month < 6 and (sm["sw1"] > row["plastic_limit"]).any():
                continue
            fields.at[fbndid, "plant"] = dt
            dbset(cursor, row["field_id"], dt, "plant")
            running += row["acres"]
            if dt.month < 6 and running > limit:
                break
        acres_planted.append(running)
        LOG.info(
            "%s acres to plant: %s, did %s", dt, pop["acres"].sum(), running
        )
        # Can we do 10% of tillage operations
        running = 0
        pop = fields[
            fields["plant"].isna()
            & ((fields["operations"] - fields["status"]) > 1)
        ]
        acres_to_till.append(pop["acres"].sum())
        # random iter
        for fbndid, row in pop.sample(frac=1).iterrows():
            # Go get the soil moisture state
            sm = smdf[(smdf["fbndid"] == fbndid) & (smdf["date"] == yesterday)]
            # Are we all below?
            if dt.month < 6 and (sm["sw1"] > row["plastic_limit"]).any():
                continue
            fields.at[fbndid, f"till{row['status'] + 1}"] = dt
            fields.at[fbndid, "status"] += 1
            dbset(
                cursor,
                row["field_id"],
                dt,
                f"till{fields.at[fbndid, 'status']}",
            )
            running += row["acres"]
            if dt.month < 6 and running > limit:
                break
        acres_tilled.append(running)
        LOG.info(
            "%s acres to till: %s, did %s", dt, pop["acres"].sum(), running
        )
    # Merge field info back into main dataframe
    df = df[["ofe", "fpath", "fbndid"]].merge(
        fields[["till1", "till2", "plant", "crop", "tillage"]],
        left_on="fbndid",
        right_index=True,
    )
    edit_rotfile(year, huc12, df[df["crop"].isin(["C", "B"])])
    cursor.close()
    pgconn.commit()
    if MAKE_PLOTS:
        plot_timeseries(
            year,
            pd.DataFrame(
                {
                    "acres_to_plant": acres_to_plant,
                    "acres_to_till": acres_to_till,
                    "acres_not_planted": acres_not_planted,
                    "acres_planted": acres_planted,
                    "acres_tilled": acres_tilled,
                }
            ),
            huc12,
        )


def estimate_soiltemp(huc12df):
    """GFS soil temperature."""
    with ncopen("/mesonet/data/iemre/gfs_current.nc") as nc:
        tsoil = np.mean(nc.variables["tsoil"][1:7], axis=0) - 273.15
        y = np.digitize(huc12df["lat"].values, nc.variables["lat"][:])
        x = np.digitize(huc12df["lon"].values, nc.variables["lon"][:])
    for i, idx in enumerate(huc12df.index.values):
        huc12df.at[idx, "tsoil"] = tsoil[y[i], x[i]]


def estimate_rainfall(huc12df):
    """Figure out our rainfall estimate."""
    today = date.today()
    tidx = daily_offset(today)
    with ncopen(f"/mesonet/data/mrms/{today:%Y}_mrms_daily.nc") as nc:
        p01d = nc.variables["p01d"][tidx].filled(0)
    for idx, row in huc12df.iterrows():
        y = int((row["lat"] - SOUTH) * 100.0)
        x = int((row["lon"] - WEST) * 100.0)
        huc12df.at[idx, "precip_mm"] = p01d[y, x]


def main(argv):
    """Go Main Go."""
    scenario = int(argv[1])
    year = int(argv[2])
    with get_sqlalchemy_conn("idep") as conn:
        huc12df = gpd.read_postgis(
            """
            SELECT geom, huc_12,
            ST_x(st_transform(st_centroid(geom), 4326)) as lon,
            ST_y(st_transform(st_centroid(geom), 4326)) as lat
            from huc12 where scenario = %s
            """,
            conn,
            params=(scenario,),
            geom_col="geom",
            index_col="huc_12",
        )
    # Allows for isolated testing.
    if len(argv) == 4:
        huc12df = huc12df.loc[[argv[3]]]
    # Estimate today's rainfall so to delay triggers
    estimate_rainfall(huc12df)
    # Any HUC12 over 10mm gets skipped
    huc12df = huc12df[huc12df["precip_mm"] < 10]
    if year == date.today().year:
        # Estimate soil temperature via GFS forecast
        estimate_soiltemp(huc12df)
        # Any HUC12 under 6C gets skipped
        huc12df = huc12df[huc12df["tsoil"] > 5.9]

    LOG.warning("%s threads for %s huc12s", CPU_COUNT, len(huc12df.index))
    progress = tqdm(total=len(huc12df.index))

    smdf = pd.read_feather(f"smstate{year}.feather")

    with ThreadPool(CPU_COUNT) as pool:

        def _error(exp):
            """Uh oh."""
            LOG.warning("Got exception, aborting....")
            LOG.exception(exp)
            pool.terminate()

        def _job(huc12):
            """Do the job."""
            progress.set_description(huc12)
            do_huc12(year, huc12, smdf[smdf["huc12"] == huc12])
            progress.update()

        for huc12 in huc12df.index.values:
            pool.apply_async(_job, (huc12,), error_callback=_error)
        pool.close()
        pool.join()


if __name__ == "__main__":
    main(sys.argv)
