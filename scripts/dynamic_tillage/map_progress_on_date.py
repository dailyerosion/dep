"""Create a lapse of progress for a given year and HUC12."""

from datetime import date

import click
import geopandas as gpd
from matplotlib.colors import BoundaryNorm
from pyiem.database import get_sqlalchemy_conn, sql_helper
from pyiem.plot import MapPlot, get_cmap
from pyiem.reference import Z_OVERLAY
from pyiem.util import logger

LOG = logger()


@click.command()
@click.option(
    "--date", "dt", required=True, type=click.DateTime(), help="Date to plot"
)
@click.option(
    "--crop",
    required=True,
    help="Crop type to plot, either C or B.",
    type=click.Choice(["C", "B"]),
)
def main(dt: date, crop: str):
    """Go Main Go."""
    with get_sqlalchemy_conn("dep") as conn:
        huc12df = gpd.read_postgis(
            sql_helper("""
    with myfields as (
        select field_id, huc12_id from field WHERE
        substr(landuse, :charat, 1) = :crop and scenario_id = 0
    ), plant_status as (
        select o.field_id, o.plant, f.huc12_id
        from field_operations o JOIN myfields f
        on (o.field_id = f.field_id) where o.year = :year
    ), agg as (
        select h.huc12_id,
        sum(case when s.plant <= :dt then 1 else 0 end) as planted,
        count(*) as count
        from huc12 h JOIN plant_status s on (h.huc12_id = s.huc12_id)
        group by h.huc12_id
    )
    select h.huc12_code, h.simple_geom, a.planted, a.count
    from agg a JOIN huc12 h
    on (a.huc12_id = h.huc12_id) WHERE h.states = 'MN'
        """),
            conn,
            params={
                "dt": dt,
                "crop": crop,
                "year": dt.year,
                "charat": dt.year - 2007 + 1,
            },
            index_col="huc12_code",
            geom_col="simple_geom",
            crs="EPSG:5070",
        )  # type: ignore

    huc12df["percent"] = huc12df["planted"] / huc12df["count"] * 100.0
    print(huc12df["percent"].describe())

    tt = "Corn" if crop == "C" else "Soybeans"
    mp = MapPlot(
        logo="dep",
        sector="state",
        state="MN",
        title=(
            f"Percentage of {tt} Planted by NASS 50% date of: {dt:%Y-%m-%d}"
        ),
    )

    cmap = get_cmap("RdBu")
    bins = list(range(0, 101, 10))
    norm = BoundaryNorm(bins, cmap.N)

    huc12df.to_crs(mp.panels[0].crs).plot(
        ax=mp.panels[0].ax,
        aspect=None,
        color=cmap(norm(huc12df["percent"].to_numpy())),
        zorder=Z_OVERLAY,
    )

    mp.draw_colorbar(
        bins,
        cmap,
        norm,
        label="Percent Planted",
        extend="neither",
    )
    mp.fig.savefig("test.png")


if __name__ == "__main__":
    main()
