"""A four panel plot diagnostic showing the limiting factor."""

import click
import geopandas as gpd
import numpy as np
import pandas as pd
from pyiem.database import get_sqlalchemy_conn
from pyiem.plot import figure
from pyiem.util import load_geodf


@click.command()
@click.option(
    "--date", "dt", required=True, type=click.DateTime(), help="Date to plot."
)
def main(dt):
    """Go Main Go."""
    with get_sqlalchemy_conn("idep") as conn:
        huc12df = gpd.read_postgis(
            "SELECT huc_12, st_transform(simple_geom, 4326) as geom "
            "from huc12 where scenario = 0",
            conn,
            geom_col="geom",
            index_col="huc_12",
        )

    huc12data = pd.read_feather(
        f"/mnt/idep2/data/huc12status/{dt:%Y}/{dt:%Y%m%d}.feather"
    )
    huc12df = huc12df.join(huc12data, how="inner")

    states = load_geodf("us_states", 4326)

    fig = figure(
        title=f"{dt:%d %b %Y} Dynamic Tillage Limiting Factor",
        subtitle="Red indicates limiting factor",
        logo="dep",
        figsize=(10.24, 7.68),
    )
    opts = [
        [0.03, 0.03, "Plastic Limit", "limited_by_soilmoisture"],
        [0.5, 0.03, "Combined Limit", "limited"],
        [0.03, 0.48, "Soil Temp Limit", "limited_by_soiltemp"],
        [0.5, 0.48, "Rainfall Limit", "limited_by_precip"],
    ]
    for opt in opts:
        ax = fig.add_axes([opt[0], opt[1], 0.42, 0.38])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        title = (
            f"{opt[2]} {huc12df[opt[3]].sum()}/{len(huc12df)} "
            f"{huc12df[opt[3]].sum() / len(huc12df):.1%}"
        )
        ax.set_title(title, fontsize=16)
        # plot in red when limited is true, else blue
        huc12df.plot(
            ax=ax,
            aspect=None,
            color=np.where(huc12df[opt[3]], "r", "b"),
        )
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        states.plot(ax=ax, color="None", edgecolor="k", lw=0.5, aspect=None)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
    fig.savefig(f"plotsv2/huc12limiter_{dt:%Y%m%d}.png")


if __name__ == "__main__":
    main()
