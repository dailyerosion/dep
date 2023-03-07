"""Diagnostic plot of operation demand."""
import sys

import pandas as pd
import geopandas as gpd
from sqlalchemy import text
from pyiem.dep import read_wb
from pyiem.plot import figure_axes, MapPlot
from pyiem.util import get_sqlalchemy_conn


def main(year, huc12):
    """Go Main Go."""
    with get_sqlalchemy_conn("idep") as conn:
        huc12df = gpd.read_postgis(
            "SELECT geom, huc_12 from huc12 where "
            "huc_12 = '102300070305' and scenario = 0",
            conn,
            geom_col="geom",
        )
        # build up the cross reference of everyhing we need to know
        df = gpd.read_postgis(
            text(
                """
            with myofes as (
                select o.ofe, p.fpath, o.fbndid,
                g.plastic_limit
                from flowpaths p, flowpath_ofes o, gssurgo g
                WHERE o.flowpath = p.fid and p.huc_12 = :huc12
                and p.scenario = 0 and o.gssurgo_id = g.id)
            SELECT ofe, fpath, f.fbndid, plastic_limit, f.geom, f.landuse,
            f.management, f.acres
            from fields f JOIN myofes m on (f.fbndid = m.fbndid)
            WHERE f.huc12 = :huc12
            ORDER by fpath, ofe
            """
            ),
            conn,
            params={"huc12": huc12},
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
    print(fields[["crop", "acres"]].groupby("crop").sum())
    print(
        fields[["crop", "tillage", "acres"]].groupby(["crop", "tillage"]).sum()
    )

    fields["status"] = 0
    fields["planted"] = False
    fields["operations"] = 1
    fields.loc[fields["tillage"] == "2", "operations"] = 2
    fields.loc[fields["tillage"].isin(["3", "4", "5", "6"]), "operations"] = 3
    total_acres = fields["acres"].sum()
    operation_acres = (fields["operations"] * fields["acres"]).sum()
    # 10% acres can get planted and 10% of acres can get tilled
    print(f"Theoretical min days {operation_acres / (total_acres / 10.) / 2.}")
    limit = total_acres / 10.0

    acres_not_planted = []
    acres_to_plant = []
    acres_planted = []
    acres_to_till = []
    acres_tilled = []

    for i, dt in enumerate(pd.date_range(f"{year}/04/15", f"{year}/06/01")):
        acres_not_planted.append(fields[~fields["planted"]]["acres"].sum())
        # Can we plant upto 10% of the acreage today?
        running = 0
        pop = fields[
            ~fields["planted"]
            & ((fields["operations"] - fields["status"]) == 1)
        ]
        acres_to_plant.append(pop["acres"].sum())
        print(f"{dt} acres to plant: {pop['acres'].sum()}")
        # random iter
        for fbndid, row in pop.sample(frac=1).iterrows():
            # Go get the soil moisture state
            sm = smdf[(smdf["fbndid"] == fbndid) & (smdf["date"] == dt)]
            # Are we all below?
            if (sm["sw1"] > row["plastic_limit"]).any():
                continue
            fields.at[fbndid, "planted"] = True
            running += row["acres"]
            if running > limit:
                break
        acres_planted.append(running)
        print(f"{dt} acres to plant: {pop['acres'].sum()}, did {running}")
        # Can we do 10% of tillage operations
        running = 0
        pop = fields[
            ~fields["planted"]
            & ((fields["operations"] - fields["status"]) > 1)
        ]
        acres_to_till.append(pop["acres"].sum())
        # random iter
        for fbndid, row in pop.sample(frac=1).iterrows():
            # Go get the soil moisture state
            sm = smdf[(smdf["fbndid"] == fbndid) & (smdf["date"] == dt)]
            # Are we all below?
            if (sm["sw1"] > row["plastic_limit"]).any():
                continue
            fields.at[fbndid, "status"] += 1
            running += row["acres"]
            if running > limit:
                break
        acres_tilled.append(running)
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
        print(f"{dt} acres to till: {pop['acres'].sum()}, did {running}")

    (fig, ax) = figure_axes(
        logo="dep",
        title=f"DEP {year} Tillage/Plant Operation Timing for 102300070305",
        subtitle="<=10% Daily Rate, All Field OFEs below 0.9 Plastic Limit",
    )
    ax2 = ax.twinx()
    x = pd.date_range(f"{year}/04/15", f"{year}/06/01")
    ax2.bar(
        x - pd.Timedelta(hours=8),
        acres_planted,
        color="#00ff00",
        alpha=0.5,
        width=0.3,
        align="edge",
        zorder=2,
    )
    ax2.bar(
        x,
        acres_tilled,
        color="#ff0000",
        alpha=0.5,
        width=0.3,
        align="edge",
        zorder=2,
    )

    ax.plot(
        x, acres_not_planted, color="k", label="Not Planted", zorder=3, lw=3
    )
    ax.plot(x, acres_to_till, color="r", label="Tillage", zorder=3, lw=3)
    ax.plot(
        x,
        acres_to_plant,
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


if __name__ == "__main__":
    main(int(sys.argv[1]), "102300070305")
