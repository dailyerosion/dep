"""Diagnostic on HUC12 flowpath counts."""

import matplotlib.colors as mpcolors
from geopandas import read_postgis
from pyiem.plot import MapPlot, get_cmap
from pyiem.reference import Z_POLITICAL
from pyiem.util import get_dbconn


def main():
    """Go Main Go."""
    pgconn = get_dbconn("idep")
    df = read_postgis(
        """
        select f.huc_12, count(*) as fps, simple_geom
        from flowpaths f JOIN huc12 h on
        (f.huc_12 = h.huc_12) WHERE f.scenario = 0 and h.scenario = 0 and
        h.states ~* 'MN'
        GROUP by f.huc_12, simple_geom ORDER by fps ASC
    """,
        pgconn,
        index_col=None,
        geom_col="simple_geom",
    )
    bins = [1, 5, 10, 15, 20, 25, 30, 35, 40]
    cmap = get_cmap("copper")
    cmap.set_over("white")
    cmap.set_under("thistle")
    norm = mpcolors.BoundaryNorm(bins, cmap.N)
    mp = MapPlot(
        continentalcolor="thistle",
        logo="dep",
        sector="state",
        state="MN",
        caption="Daily Erosion Project",
        title="Minnesota DEP HUC12 Flowpath Counts",
        subtitle=(
            "Number of HUC12s with <40 Flowpaths "
            f"({len(df[df['fps'] < 40].index):.0f}/{len(df.index):.0f} "
            f"{(len(df[df['fps'] < 40].index) / len(df.index) * 100.0):.2f}%)"
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
    mp.draw_colorbar(bins, cmap, norm, extend="max", title="Count")
    mp.postprocess(filename="/tmp/huc12_cnts.png")


if __name__ == "__main__":
    main()
