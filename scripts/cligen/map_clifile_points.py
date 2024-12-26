"""Create a map of where we have climate files!"""

import click
import geopandas as gpd
import numpy as np
from matplotlib.colors import BoundaryNorm
from pyiem.database import get_sqlalchemy_conn
from pyiem.plot import MapPlot, get_cmap
from pyiem.reference import Z_OVERLAY
from sqlalchemy import text

"""
select geom from climate_files where id in (
        select distinct climate_file_id from climate_file_yearly_summary
        where rfactor < 1 and year = 2024) and scenario = 0
"""


@click.command()
@click.option("--year", default=2024, help="Year to plot")
def main(year: int):
    """make maps, not war."""
    with get_sqlalchemy_conn("idep") as pgconn:
        pts = gpd.read_postgis(
            text("""
    with climo as (
        select climate_file_id, avg(rfactor) as rr from
        climate_file_yearly_summary
        GROUP by climate_file_id)
    select geom, (rfactor - rr) / rr  * 100. as ratio from
    climate_files f, climate_file_yearly_summary s, climo c
    WHERE f.id = s.climate_file_id and s.year = :year
    and f.id = c.climate_file_id and f.scenario = 0
"""),
            pgconn,
            params={"year": year},
            geom_col="geom",
        )
    cmap = get_cmap("RdBu")
    # clevs = [0, 250, 500, 750, 1000, 1500, 2000, 2500, 3000, 4000, 5000]
    clevs = np.arange(-60, 61, 20)
    norm = BoundaryNorm(clevs, cmap.N)
    mp = MapPlot(
        logo="dep",
        sector="conus",
        title=f"{year} R-Factor % Difference from 2007-2024 Average",
        subtitle=f"Total Climate Files: {len(pts)}",
        caption="Daily Erosion Project",
    )
    # All points will overwhelm matplotlib, so we need to plot them in chunks
    pts.to_crs(mp.panels[0].crs).plot(
        ax=mp.panels[0].ax,
        aspect=None,
        marker="o",
        markersize=3,
        color=cmap(norm(pts["ratio"].values)),
        zorder=Z_OVERLAY,
    )
    mp.draw_colorbar(
        clevs=clevs,
        cmap=cmap,
        norm=norm,
        spacing="proportional",
        units="%",
        extend="both",
    )
    mp.fig.savefig(f"{year}_departure.png")


if __name__ == "__main__":
    main()
