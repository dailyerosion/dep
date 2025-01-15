"""Period of record plot summaries"""

import datetime
import sys

import matplotlib.colors as mpcolors
import numpy as np
from geopandas import read_postgis
from matplotlib.patches import Polygon
from pyiem.plot import MapPlot
from pyiem.plot.use_agg import plt
from pyiem.util import get_dbconn

V2NAME = {
    "avg_loss": "Detachment",
    "qc_precip": "Precipitation",
    "avg_delivery": "Delivery",
    "avg_runoff": "Runoff",
    "avg_loss_metric": "Detachment",
    "qc_precip_metric": "Precipitation",
    "avg_delivery_metric": "Delivery",
    "avg_runoff_metric": "Runoff",
}
V2MULTI = {
    "avg_loss": 4.463,
    "qc_precip": 1.0 / 25.4,
    "avg_delivery": 4.463,
    "avg_runoff": 1.0 / 25.4,
    "avg_loss_metric": 10.0,
    "qc_precip_metric": 1.0,
    "avg_delivery_metric": 10.0,
    "avg_runoff_metric": 1.0,
}
V2UNITS = {
    "avg_loss": "tons/acre",
    "qc_precip": "inches",
    "avg_delivery": "tons/acre",
    "avg_runoff": "inches",
    "avg_loss_metric": "tonnes/hectare",
    "qc_precip_metric": "mm",
    "avg_delivery_metric": "tonnes/hectare",
    "avg_runoff_metric": "mm",
}
R1 = [0, 2.5, 5, 10, 20, 40, 60]
R1M = [0, 5, 10, 20, 40, 80, 120]
R3M = [0, 25, 50, 100, 150, 200]
R2 = [15, 25, 35, 45, 55]
R2M = [600, 700, 900, 1000, 1200]
V2RAMP = {
    "avg_loss": R1,
    "qc_precip": R2,
    "avg_delivery": R1,
    "avg_runoff": R1,
    "avg_loss_metric": R1M,
    "qc_precip_metric": R2M,
    "avg_delivery_metric": R1M,
    "avg_runoff_metric": R3M,
}


def main(argv):
    """Go Main Go"""
    v = argv[1]
    agg = argv[2]
    ts = datetime.date(2008, 1, 1)
    ts2 = datetime.date(2020, 12, 31)
    scenario = 0

    # suggested for runoff and precip
    if V2UNITS[v] in ["mm", "inches"]:
        colors = ["#ffffa6", "#9cf26d", "#76cc94", "#6399ba", "#5558a1"]
    # suggested for detachment
    elif v in ["avg_loss", "avg_loss_metric"]:
        colors = [
            "#cbe3bb",
            "#c4ff4d",
            "#ffff4d",
            "#ffc44d",
            "#ff4d4d",
            "#c34dee",
        ]
    # suggested for delivery
    else:  # v in ["avg_delivery", "avg_delivery_metric"]:
        colors = [
            "#ffffd2",
            "#ffff4d",
            "#ffe0a5",
            "#eeb74d",
            "#ba7c57",
            "#96504d",
        ]
    cmap = mpcolors.ListedColormap(colors, "james")
    cmap.set_under("white")
    cmap.set_over("black")

    pgconn = get_dbconn("idep")

    title = "for %s" % (ts.strftime("%-d %B %Y"),)
    if ts != ts2:
        title = "between %s and %s" % (
            ts.strftime("%-d %b %Y"),
            ts2.strftime("%-d %b %Y"),
        )
    mp = MapPlot(
        axisbg="#EEEEEE",
        logo="dep",
        sector="iowa",
        nocaption=True,
        title=("DEP %s %s %s")
        % (
            V2NAME[v.replace("_metric", "")],
            "Yearly Average" if agg == "avg" else "Total",
            title,
        ),
        caption="Daily Erosion Project",
    )

    df = read_postgis(
        f"""
    WITH data as (
      SELECT huc_12, extract(year from valid) as yr,
      sum({v.replace("_metric", "")})  as d from results_by_huc12
      WHERE scenario = %s and valid >= %s and valid <= %s
      GROUP by huc_12, yr),

    agg as (
      SELECT huc_12, {agg}(d) as d from data GROUP by huc_12)

    SELECT ST_Transform(simple_geom, 4326) as geo, coalesce(d.d, 0) as data
    from huc12 i LEFT JOIN agg d
    ON (i.huc_12 = d.huc_12) WHERE i.scenario = %s and i.states ~* 'IA'
    """,
        pgconn,
        params=(scenario, ts, ts2, scenario),
        geom_col="geo",
        index_col=None,
    )
    df["data"] = df["data"] * V2MULTI[v]
    if df["data"].max() < 0.01:
        bins = [0.01, 0.02, 0.03, 0.04, 0.05]
    else:
        bins = np.array(V2RAMP[v]) * (10.0 if agg == "sum" else 1.0)
    norm = mpcolors.BoundaryNorm(bins, cmap.N)

    df = df.to_crs(mp.panels[0].crs)
    for _, row in df.iterrows():
        c = cmap(norm([row["data"]]))[0]
        arr = np.asarray(row["geo"].exterior.coords)
        p = Polygon(arr[:, :2], fc=c, ec="k", zorder=2, lw=0.1)
        mp.panels[0].ax.add_patch(p)

    mp.drawcounties()
    mp.drawcities()
    lbl = [round(_, 2) for _ in bins]
    u = "%s, Avg: %.2f" % (V2UNITS[v], df["data"].mean())
    mp.draw_colorbar(
        bins,
        cmap,
        norm,
        clevlabels=lbl,
        units=u,
        title="%s :: %s" % (V2NAME[v], V2UNITS[v]),
    )
    plt.savefig(
        "%s_%s_%s%s.png"
        % (ts.year, ts2.year, v, "_sum" if agg == "sum" else "")
    )


if __name__ == "__main__":
    main(sys.argv)
