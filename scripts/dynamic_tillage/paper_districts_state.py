"""Potential paper plot showingt the Iowa districts, MN, and planting dates."""

import geopandas as gpd
from matplotlib.patches import Rectangle
from pyiem.database import get_sqlalchemy_conn, sql_helper
from pyiem.plot import MapPlot
from pyiem.reference import Z_OVERLAY

DATES_AND_COLORS = {
    "April 30": "#f7fcb9",
    "May 5": "#addd8e",
    "May 10": "#31a354",
}
LOOKUP = {
    "MN": DATES_AND_COLORS["May 10"],
    "IAC001": DATES_AND_COLORS["May 10"],
    "IAC002": DATES_AND_COLORS["May 10"],
    "IAC003": DATES_AND_COLORS["May 10"],
    "IAC004": DATES_AND_COLORS["May 5"],
    "IAC005": DATES_AND_COLORS["May 5"],
    "IAC006": DATES_AND_COLORS["May 5"],
    "IAC007": DATES_AND_COLORS["April 30"],
    "IAC008": DATES_AND_COLORS["April 30"],
    "IAC009": DATES_AND_COLORS["April 30"],
}


def overlay_iowa_districts(mp: MapPlot) -> None:
    """Overlay Iowa districts."""
    with get_sqlalchemy_conn("coop") as conn:
        districts = gpd.read_postgis(
            sql_helper(
                """
                SELECT c.geom, t.id
                from climodat_regions c JOIN stations t on
                (c.iemid = t.iemid) WHERE t.network = 'IACLIMATE'
                and substr(id, 1, 3) = 'IAC'
                """
            ),
            conn,
            geom_col="geom",
        )
    districts["color"] = districts["id"].apply(
        lambda x: LOOKUP.get(x, "#000000")
    )
    districts.to_crs(mp.panels[0].crs).plot(
        ax=mp.panels[0].ax,
        color=districts["color"],
        edgecolor="blue",
        linewidth=2,
        aspect=None,
        zorder=Z_OVERLAY + 1,
    )


def overlay_states(mp: MapPlot) -> gpd.GeoDataFrame:
    """Overlay Iowa and Minnesota."""
    with get_sqlalchemy_conn("postgis") as conn:
        states = gpd.read_postgis(
            sql_helper("SELECT * from states"),
            conn,
            geom_col="the_geom",
        )
    states["color"] = states["state_abbr"].apply(
        lambda x: LOOKUP.get(x, "#ffffff")
    )
    states.to_crs(mp.panels[0].crs).plot(
        ax=mp.panels[0].ax,
        color=states["color"],
        edgecolor="black",
        linewidth=2,
        aspect=None,
        zorder=Z_OVERLAY,
    )
    return states


def main():
    """Go Main Go."""
    mp = MapPlot(
        logo=None,
        title="",
        subtitle="",
        sector="custom",
        south=40.1,
        north=49.4,
        west=-96.2,
        east=-91.9,
        continentalcolor="white",
        stateborderwidth=0,
        nocaption=True,
    )
    states = overlay_states(mp)
    overlay_iowa_districts(mp)

    # Create inset map showing contiguous US with a frame color of #eee
    inset_ax = mp.fig.add_axes([0.02, 0.02, 0.2, 0.15], xticks=[], yticks=[])
    inset_ax.set_facecolor("#eee")
    states.to_crs(4326).plot(
        ax=inset_ax,
        color="white",
        edgecolor="black",
        linewidth=0.5,
        aspect=None,
    )
    inset_ax.add_patch(
        Rectangle(
            (-101.2, 40.1), 14.3, 9.3, fill=False, edgecolor="red", linewidth=2
        )
    )
    inset_ax.set_xlim(-125, -66.5)
    inset_ax.set_ylim(24, 50)

    # Add a legend for the planting dates
    legend = mp.ax.legend(
        handles=[
            Rectangle(
                [0, 0],
                1,
                1,
                facecolor=DATES_AND_COLORS["April 30"],
                edgecolor="black",
                label="Corn: April 30\nSoybean: May 12",
            ),
            Rectangle(
                [0, 0],
                1,
                1,
                facecolor=DATES_AND_COLORS["May 5"],
                edgecolor="black",
                label="Corn: May 5\nSoybean: May 17",
            ),
            Rectangle(
                [0, 0],
                1,
                1,
                facecolor=DATES_AND_COLORS["May 10"],
                edgecolor="black",
                label="Corn: May 10\nSoybean: May 22",
            ),
        ],
        loc=(0.03, 0.65),
        title="Static Planting Dates",
    )
    legend.set_zorder(Z_OVERLAY + 2)
    mp.ax.add_artist(legend)

    # Add a legend for cartographic elements
    clegend = mp.ax.legend(
        handles=[
            Rectangle(
                [0, 0],
                1,
                1,
                facecolor="None",
                edgecolor="blue",
                label="Iowa Crop Reporting Districts",
            ),
            Rectangle(
                [0, 0],
                1,
                1,
                facecolor="None",
                edgecolor="black",
                label="U.S. States",
            ),
        ],
        loc=(0.03, 0.45),
        title="Map Elements",
    )
    clegend.set_zorder(Z_OVERLAY + 2)

    mp.fig.savefig("plots/districts_state.png", dpi=300, bbox_inches="tight")


if __name__ == "__main__":
    main()
