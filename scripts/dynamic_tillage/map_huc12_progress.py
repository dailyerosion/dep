"""Create a lapse of progress for a given year and HUC12."""

from datetime import date

import click
import geopandas as gpd
import pandas as pd
from matplotlib.patches import Rectangle
from pyiem.database import get_sqlalchemy_conn
from pyiem.plot import MapPlot
from pyiem.util import logger
from sqlalchemy import text
from tqdm import tqdm

LOG = logger()


def plot_map_progress(
    huc12: str,
    huc12df: gpd.GeoDataFrame,
    fieldsdf: gpd.GeoDataFrame,
    dt: date,
    i: int,
):
    """Make a map diagnostic"""
    # Get the fields and their status

    minx, miny, maxx, maxy = huc12df["geom"].total_bounds
    buffer = 0.01

    mp = MapPlot(
        title=f"DEP Planting Progress {dt:%Y %b %d}",
        subtitle=f"For HUC12: {huc12df.iloc[0]['name']} [{huc12}]",
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
    fdf = fieldsdf
    fdf["color"] = "yellow"
    te = "tillage_events"
    fdf.loc[fdf["plant"].notna(), "color"] = "white"
    fdf.loc[fdf["till1"] <= dt, "color"] = "r"
    fdf.loc[(fdf["till1"] <= dt) & (fdf[te] == 1), "color"] = "tan"
    fdf.loc[(fdf["till2"] <= dt) & (fdf[te] == 2), "color"] = "tan"
    fdf.loc[(fdf["till3"] <= dt) & (fdf[te] == 3), "color"] = "tan"
    fieldsdf.loc[fieldsdf["plant"] <= dt, "color"] = "g"
    fieldsdf.to_crs(mp.panels[0].crs).plot(
        ax=mp.panels[0].ax,
        aspect=None,
        facecolor=fieldsdf["color"],
        edgecolor="k",
        linewidth=1,
        zorder=100,
    )
    pn = Rectangle((0, 0), 1, 1, fc="yellow", ec="k")
    p0 = Rectangle((0, 0), 1, 1, fc="white", ec="k")
    p1 = Rectangle((0, 0), 1, 1, fc="r", ec="k")
    p2 = Rectangle((0, 0), 1, 1, fc="tan", ec="k")
    p3 = Rectangle((0, 0), 1, 1, fc="g", ec="k")
    mp.panels[0].ax.legend(
        (pn, p0, p1, p2, p3),
        (
            "Non-Ag",
            "Awaiting",
            "Tillage Started",
            "Tillage Complete",
            "Planted",
        ),
        ncol=2,
        fontsize=11,
        loc=2,
    )

    mp.fig.savefig(f"{i:04.0f}.png")
    mp.close()


@click.command()
@click.option("--huc12", required=True, type=str, help="HUC12 to plot")
@click.option("--year", required=True, type=int, help="Year to plot")
def main(huc12: str, year: int):
    """Go Main Go."""
    with get_sqlalchemy_conn("idep") as conn:
        huc12df = gpd.read_postgis(
            text("""
    select huc_12, name, ST_Transform(geom, 4326) as geom
    from huc12 where huc_12 = :huc12 and scenario = 0
        """),
            conn,
            params={"huc12": huc12},
            index_col="huc_12",
            geom_col="geom",
            crs="EPSG:4326",
        )
        fieldsdf = gpd.read_postgis(
            text("""
    select o.*, ST_Transform(f.geom, 4326) as geom, 0 as tillage_events
    from fields f LEFT JOIN field_operations o
    on (f.field_id = o.field_id and o.year = :year)
    where huc12 = :huc12
        """),
            conn,
            params={"year": year, "huc12": huc12},
            index_col="field_id",
            parse_dates=["till1", "till2", "till3", "plant"],
            geom_col="geom",
            crs="EPSG:4326",
        )
        fieldsdf.loc[fieldsdf["till1"].notna(), "tillage_events"] = 1
        fieldsdf.loc[fieldsdf["till2"].notna(), "tillage_events"] = 2
        fieldsdf.loc[fieldsdf["till3"].notna(), "tillage_events"] = 3
    LOG.info("Found %s fields for plotting", len(fieldsdf))
    progress = tqdm(pd.date_range(f"{year}-04-11", f"{year}-06-14"))
    for i, dt in enumerate(progress):
        progress.set_description(f"Plotting {dt}")
        plot_map_progress(huc12, huc12df, fieldsdf, dt, i)


if __name__ == "__main__":
    main()
