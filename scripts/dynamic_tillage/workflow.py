"""
Our Dynamic Tillage Workflow!

"""
from datetime import date
import sys

import numpy as np
import pandas as pd
import geopandas as gpd
from sqlalchemy import text
from pyiem.iemre import daily_offset
from pyiem.mrms import WEST, SOUTH
from pyiem.plot import figure_axes, MapPlot
from pyiem.util import get_sqlalchemy_conn, get_dbconn, logger, ncopen
from pydep.io.dep import read_wb

LOG = logger()
MAKE_PLOTS = False
DBSET_DATE_THRESHOLD = pd.Timestamp(date.today())


def plot_map(i, dt, huc12df, fields):
    """Make a map diagnostic"""
    minx, miny, maxx, maxy = huc12df["geom"].to_crs(4326).total_bounds
    buffer = 0.01

    mp = MapPlot(
        title=f"DEP Planting Progress {dt:%Y %b %d}",
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
        edgecolor="k",
        linewidth=2,
        zorder=100,
    )
    fields["color"] = "tan"
    fields.loc[fields["planted"], "color"] = "g"
    fields.to_crs(mp.panels[0].crs).plot(
        ax=mp.panels[0].ax,
        aspect=None,
        facecolor=fields["color"],
        edgecolor=fields["color"],
        zorder=100,
    )
    mp.fig.savefig(f"{i:04.0f}.png")
    mp.close()


def plot_timeseries(year, df):
    """Make a diagnostic."""
    (fig, ax) = figure_axes(
        logo="dep",
        title=f"DEP {year} Tillage/Plant Operation Timing for 102300070305",
        subtitle="<=10% Daily Rate, All Field OFEs below 0.9 Plastic Limit",
    )
    ax2 = ax.twinx()
    x = pd.date_range(f"{year}/04/15", f"{year}/06/01")
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


def do_huc12(year, huc12, huc12row):
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
    # Figure out soil moisture state for each of our flowpaths and ofes
    dfs = []
    sts = pd.Timestamp(f"{year}/04/15")
    ets = pd.Timestamp(f"{year}/06/01")
    for flowpath in df["fpath"].unique():
        flowpath = int(flowpath)
        smdf = read_wb(
            f"/i/0/wb/{huc12[:8]}/{huc12[8:]}/{huc12}_{flowpath}.wb"
        )
        smdf = smdf[(smdf["date"] >= sts) & (smdf["date"] <= ets)]
        # Each flowpath + ofe should be associated with a fbndid
        for ofe, gdf in smdf.groupby("ofe"):
            fbndid = df[(df["fpath"] == flowpath) & (df["ofe"] == ofe)].iloc[
                0
            ]["fbndid"]
            smdf.loc[gdf.index, "fbndid"] = fbndid
        dfs.append(smdf[["fbndid", "date", "sw1"]])  # save space
    smdf = pd.concat(dfs)

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
    startdate = max([pd.Timestamp(f"{year}/04/15"), DBSET_DATE_THRESHOLD])
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
        # random iter
        for fbndid, row in pop.sample(frac=1).iterrows():
            # Go get the soil moisture state
            sm = smdf[(smdf["fbndid"] == fbndid) & (smdf["date"] == dt)]
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
            sm = smdf[(smdf["fbndid"] == fbndid) & (smdf["date"] == dt)]
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
        if MAKE_PLOTS:
            plot_map(i, dt, huc12row, fields)
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
    # Estimate soil temperature via GFS forecast
    estimate_soiltemp(huc12df)
    # Any HUC12 under 6C gets skipped
    huc12df = huc12df[huc12df["tsoil"] > 5.9]
    LOG.warning("Running for %s huc12s", len(huc12df.index))
    for huc12, row in huc12df.iterrows():
        do_huc12(year, huc12, row)


if __name__ == "__main__":
    main(sys.argv)
