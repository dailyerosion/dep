"""Explore some plastic limit issues."""

from pathlib import Path

import geopandas as gpd
import matplotlib.colors as mpcolors
import pandas as pd
from pyiem.database import get_sqlalchemy_conn, sql_helper
from pyiem.plot import MapPlot, get_cmap
from pyiem.reference import Z_OVERLAY2


def get_data():
    """Run the DB query."""
    with get_sqlalchemy_conn("idep") as conn:
        return pd.read_sql(
            sql_helper("""
    with layers as (
        select g.id, g.plastic_limit, sf.clay, sf.om,
        rank() OVER (PARTITION by sf.mukey ORDER by depthto_mm asc) as rank,
        wepp_min_sw1 + ((wepp_max_sw1 - wepp_min_sw1) * 0.58) as pl58
        from gssurgo g, gssurgo24.dep_soilfractions sf
        WHERE g.mukey = sf.mukey :: int and g.fiscal_year = 2024
    ), toplayer as (
        select id, clay, om, plastic_limit, pl58 from layers where rank = 1
    ), depsoils as (
        select ST_Transform(f.geom, 4326) as geo, f.huc_12, t.clay, t.om,
        t.plastic_limit, t.pl58
        from flowpath_ofes o, flowpaths f, toplayer t
        WHERE t.id = o.gssurgo_id and o.flowpath = f.fid
        and f.scenario = 0
    )
    select st_x(st_pointn(geo, 1)) as lon, st_y(st_pointn(geo, 1)) as lat,
    clay, om, plastic_limit, pl58, huc_12 from depsoils
                                       """),
            conn,
        )


def main():
    """Go Main Go."""
    csv = Path("/tmp/pldata.csv")
    if not csv.exists():
        soils = get_data()
        soils.index.name = "idx"
        soils.to_csv(csv)
    else:
        soils = pd.read_csv(csv, index_col="idx", dtype={"huc_12": str})

    with get_sqlalchemy_conn("idep") as conn:
        huc12df = gpd.read_postgis(
            sql_helper("""
    select huc_12, simple_geom from huc12 where scenario = 0
            """),
            conn,
            geom_col="simple_geom",
            index_col="huc_12",
        )

    soils["out_of_bounds"] = (
        (soils["clay"] < 11)
        | (soils["clay"] > 74)
        | (soils["om"] < 0.2)
        | (soils["om"] > 6.9)
    )
    ok = soils[~soils["out_of_bounds"]]

    huc12stats = (
        soils[["huc_12", "out_of_bounds"]]
        .groupby("huc_12")
        .value_counts()
        .unstack()
        .fillna(0)
        .rename(columns={False: "Plastic", True: "False"})
    )
    huc12df["freq"] = huc12stats["False"] / huc12stats.sum(axis=1) * 100.0
    huc12df["plastic_limit"] = (
        ok[["huc_12", "plastic_limit"]]
        .groupby("huc_12")
        .mean()["plastic_limit"]
    )
    huc12df["pl58"] = ok[["huc_12", "pl58"]].groupby("huc_12").mean()["pl58"]
    huc12df["diff"] = (huc12df["plastic_limit"] * 0.9) - huc12df["pl58"]
    print(huc12df["diff"].describe())

    mp = MapPlot(
        title=("DEP HUC12 Mean PL * 0.9 [SM%] for Plastic Soils minus PL58%"),
        subtitle=("Clay [11%-74%] and Organic Matter [0.2%-6.9%] "),
        caption="Daily Erosion Project",
        logo="dep",
        sector="custom",
        south=36.8,
        north=49.4,
        west=-99.2,
        east=-88.9,
    )
    cmap = get_cmap("managua")
    clevs = [-10, -7, -3, -1, 0, 1, 3, 7, 10]
    norm = mpcolors.BoundaryNorm(
        boundaries=clevs,
        ncolors=cmap.N,
    )
    huc12df.to_crs(mp.panels[0].crs).plot(
        facecolor=cmap(norm(huc12df["diff"])),
        zorder=Z_OVERLAY2,
        aspect=None,
        ax=mp.ax,
    )
    mp.draw_colorbar(
        clevs,
        cmap,
        norm,
        extend="both",
        spacing="proportional",
    )
    mp.fig.savefig("non_plastic_soils.png")


if __name__ == "__main__":
    main()
