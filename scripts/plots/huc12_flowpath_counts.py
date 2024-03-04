"""Diagnostic on HUC12 flowpath counts."""

import sys

import geopandas as gpd
import matplotlib.colors as mpcolors
from pyiem.plot import MapPlot, get_cmap
from pyiem.reference import Z_POLITICAL, state_names
from pyiem.util import get_sqlalchemy_conn


def main(argv):
    """Go Main Go."""
    state = argv[1]
    with get_sqlalchemy_conn("idep") as conn:
        df = gpd.read_postgis(
            """
            select f.huc_12, count(*) as fps, simple_geom
            from flowpaths f JOIN huc12 h on
            (f.huc_12 = h.huc_12) WHERE f.scenario = 0 and h.scenario = 0 and
            h.states ~* %s
            GROUP by f.huc_12, simple_geom ORDER by fps ASC
        """,
            conn,
            index_col=None,
            params=(state,),
            geom_col="simple_geom",
        )
    bins = [1, 5, 10, 20]
    cmap = get_cmap("copper")
    cmap.set_over("white")
    cmap.set_under("thistle")
    norm = mpcolors.BoundaryNorm(bins, cmap.N)
    vv = len(df[df["fps"] < bins[-1]].index) / len(df.index) * 100.0
    mp = MapPlot(
        continentalcolor="thistle",
        logo="dep",
        sector="state",
        state=state,
        caption="Daily Erosion Project",
        title=f"{state_names[state]} DEP HUC12 Flowpath Counts",
        subtitle=(
            f"Number of HUC12s with <{bins[-1]} Flowpaths "
            f"({len(df[df['fps'] < bins[-1]].index):.0f}/{len(df.index):.0f} "
            f"{vv:.2f}%)"
        ),
    )
    colors = cmap(norm(df["fps"]))
    df.to_crs(mp.panels[0].crs).plot(
        fc=colors,
        ax=mp.panels[0].ax,
        ec="None",
        zorder=Z_POLITICAL,
    )

    mp.drawcounties()
    mp.draw_colorbar(
        bins,
        cmap,
        norm,
        extend="max",
        title="Count",
        spacing="proportional",
    )
    mp.postprocess(filename=f"/tmp/huc12_cnts_{state}.png")


if __name__ == "__main__":
    main(sys.argv)
