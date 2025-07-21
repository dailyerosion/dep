"""A four panel showing the limiter climo."""

import click
import geopandas as gpd
import numpy as np
import pandas as pd
from matplotlib.cm import ScalarMappable
from matplotlib.colors import BoundaryNorm
from pyiem.database import get_sqlalchemy_conn
from pyiem.plot import figure, get_cmap
from pyiem.util import load_geodf


@click.command()
def main():
    """Go Main Go."""
    states = load_geodf("us_states", 4326)

    with get_sqlalchemy_conn("idep") as conn:
        huc12df = gpd.read_postgis(
            "SELECT huc_12, st_transform(simple_geom, 4326) as geom "
            "from huc12 where scenario = 0 and "
            "(states ~* 'IA' or states ~* 'MN')",
            conn,
            geom_col="geom",
            index_col="huc_12",
        )

    huc12data = pd.read_csv(
        "plots/huc12_limiter_climo.csv",
        index_col="huc12",
        dtype={"huc12": str},
    )
    huc12df = huc12df.join(huc12data, how="inner")
    for col in huc12df.columns:
        if col.startswith("limit"):
            huc12df[f"{col}_pct"] = huc12df[col] / huc12df["total"] * 100.0
    bins = np.array([0, 5, 10, 20, 30, 40, 50, 60, 70])
    cmap = get_cmap("YlGnBu")
    norm = BoundaryNorm(bins, cmap.N)

    fig = figure(
        title="",
        logo=None,
        figsize=(8.24, 7.68),
    )
    opts = [
        [0.03, 0.52, "Soil Temp Limit", "limited_by_soiltemp_pct"],
        [0.45, 0.52, "Rainfall Limit", "limited_by_precip_pct"],
        [0.03, 0.03, "Plastic Limit", "limited_by_soilmoisture_pct"],
        [0.45, 0.03, "Combined Limit", "limited_pct"],
    ]
    labels = ["a", "b", "c", "d"]
    for i, opt in enumerate(opts):
        ax = fig.add_axes([opt[0], opt[1], 0.37, 0.42])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_title(opt[2], fontsize=16)
        # plot in red when limited is true, else blue
        huc12df.plot(
            ax=ax,
            aspect=None,
            color=cmap(norm(huc12df[opt[3]].values)).tolist(),
        )
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        states.plot(ax=ax, color="None", edgecolor="k", lw=0.5, aspect=None)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.text(
            0.01,
            0.01,
            labels[i],
            transform=ax.transAxes,
            fontsize=16,
            fontweight="bold",
            va="bottom",
            bbox={"facecolor": "white", "alpha": 0.8, "pad": 2},
        )

    # Add a colorbar
    cax = fig.add_axes([0.87, 0.03, 0.02, 0.8])
    cbar = fig.colorbar(
        ScalarMappable(norm=norm, cmap=cmap),
        cax=cax,
        ticks=bins,
        orientation="vertical",
        spacing="proportional",
    )
    cbar.set_label("Percent of Dates Limited (%)")

    # plots directory is symlinked
    fig.savefig("plots/huc12limiter_climo.png", dpi=300)


if __name__ == "__main__":
    main()
