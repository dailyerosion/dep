"""HUC12 Diagnostic."""

import os

import click
import pandas as pd
from matplotlib.dates import DateFormatter
from pyiem.database import get_sqlalchemy_conn
from pyiem.plot import figure
from sqlalchemy import text


def get_plastic_limit(huc12: str) -> pd.DataFrame:
    """Figure out what the plastic limit is."""
    with get_sqlalchemy_conn("idep") as conn:
        # build up the cross reference of everyhing we need to know
        return pd.read_sql(
            text(
                """
                select o.ofe, p.fpath, o.fbndid, g.plastic_limit,
                p.fpath || '_' || o.ofe as combo
                from flowpaths p, flowpath_ofes o, gssurgo g
                WHERE o.flowpath = p.fid and p.huc_12 = :huc12
                and p.scenario = 0 and o.gssurgo_id = g.id
            """
            ),
            conn,
            params={
                "huc12": huc12,
            },
            index_col=None,
        )


@click.command()
@click.option("--huc12", help="HUC12 To Plot")
@click.option("--year", type=int, help="Year to Plot")
def main(huc12, year):
    """Go Main Go."""
    pldf = get_plastic_limit(huc12)
    smdfs = []
    hucstatusdfs = []
    for dt in pd.date_range(f"{year}/04/14", f"{year}/05/31"):
        fn = f"/mnt/idep2/data/smstate/{dt:%Y}/smstate{dt:%Y%m%d}.feather"
        if not os.path.isfile(fn):
            continue
        smdf = pd.read_feather(fn)
        smdfs.append(smdf[smdf["huc12"] == huc12])

        fn = f"/mnt/idep2/data/huc12status/{dt:%Y}/{dt:%Y%m%d}.feather"
        if not os.path.isfile(fn):
            continue
        statusdf = pd.read_feather(fn)
        statusdf["date"] = dt
        hucstatusdfs.append(statusdf.loc[[huc12]])
    hucstatusdf = pd.concat(hucstatusdfs)
    print(hucstatusdf)
    huc12sm = pd.concat(smdfs)
    huc12sm["combo"] = (
        huc12sm["fpath"].astype(str) + "_" + huc12sm["ofe"].astype(str)
    )
    huc12sm["plastic_limit"] = (
        huc12sm["combo"].map(pldf.set_index("combo")["plastic_limit"]) * 0.8
    )
    huc12sm["below_pl"] = huc12sm["sw1"] < huc12sm["plastic_limit"]

    fig = figure(
        title=f"DEP: {huc12} Walnut Creek Dynamic Tillage Diagnostic",
        subtitle="15 April - 23 April 2024",
        logo="dep",
        figsize=(8, 6),
    )
    yaxsize = 0.2
    ax = fig.add_axes([0.1, 0.68, 0.8, yaxsize])
    ax.text(
        0, 1, "* SM Evaluation using previous date", transform=ax.transAxes
    )
    for dt, gdf in huc12sm.groupby("date"):
        ax.bar(
            dt + pd.Timedelta(hours=24),
            gdf["below_pl"].sum() / gdf["below_pl"].size * 100,
            color="r",
            width=0.5,
            align="center",
            edgecolor="black",
        )
    ax.axhline(50, lw=2, color="k")
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 10, 25, 50, 75, 90, 100])
    ax.grid(True)
    ax.set_ylabel("Percent of OFEs\nBelow 0.8*PL")
    ax.xaxis.set_major_formatter(DateFormatter("%-d %b"))

    ax2 = fig.add_axes([0.1, 0.4, 0.8, yaxsize], sharex=ax)
    ax2.bar(
        hucstatusdf["date"],
        hucstatusdf["precip_mm"],
        width=0.4,
        color="b",
        lw=2,
    )
    ax2.set_ylabel("Precipitation [mm]")
    ax2.axhline(10, lw=2, color="k")
    ax2.grid(True)

    ax3 = fig.add_axes([0.1, 0.1, 0.8, yaxsize], sharex=ax)
    ax3.bar(
        hucstatusdf["date"],
        hucstatusdf["tsoil_avg"],
        width=0.4,
        color="b",
        lw=2,
    )
    ax3.set_ylabel("Forecast Soil Temp [C]")
    ax3.axhline(6, lw=2, color="k")
    ax3.grid(True)

    for _ax, label in zip(
        [ax, ax2, ax3], ["soilmoisture", "precip", "soiltemp"]
    ):
        for _idx, row in hucstatusdf.iterrows():
            _ax.annotate(
                "\u2718" if row[f"limited_by_{label}"] else "\u2714",
                (row["date"], -0.3),
                xycoords=("data", "axes fraction"),
                ha="center",
                va="center",
                fontsize=20,
                fontproperties="DeJaVu Sans",
                color="red" if row[f"limited_by_{label}"] else "green",
            )

    fig.savefig(f"sm_{huc12}_{year}.png")


if __name__ == "__main__":
    main()
