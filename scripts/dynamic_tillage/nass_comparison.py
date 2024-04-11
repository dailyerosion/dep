"""Plot our planting progress vs that of NASS."""

import click
import geopandas as gpd
import pandas as pd
from pyiem.database import get_sqlalchemy_conn
from pyiem.plot import figure_axes
from sqlalchemy import text

XREF = {
    "nw": "IAC001",
    "nc": "IAC002",
    "ne": "IAC003",
    "wc": "IAC004",
    "c": "IAC005",
    "ec": "IAC006",
    "sw": "IAC007",
    "sc": "IAC008",
    "se": "IAC009",
}


@click.command()
@click.option("--year", type=int, help="Year to plot")
@click.option("--district", type=str, help="NASS District")
def main(year, district):
    """Go Main Go."""
    charidx = year - 2007 + 1
    with get_sqlalchemy_conn("coop") as conn:
        climdiv = gpd.read_postgis(
            text(
                """
                select t.iemid, r.geom from climodat_regions r JOIN stations t
                on (r.iemid = t.iemid) where t.id = :sid
                """
            ),
            conn,
            params={"sid": XREF[district]},
            geom_col="geom",
            index_col="iemid",
        )

    # Get the NASS data
    with get_sqlalchemy_conn("coop") as conn:
        nass = pd.read_sql(
            text(
                """
            select * from nass_iowa where metric = 'corn planted'
            and extract(year from valid) = :year ORDER by valid ASc
            """
            ),
            conn,
            params={"year": year},
        )

    # Figure out the planting dates
    with get_sqlalchemy_conn("idep") as conn:
        fields = gpd.read_postgis(
            text("""
            select st_transform(geom, 4326) as geom, plant, huc12, fbndid,
            acres from fields f LEFT JOIN field_operations o
            on (f.field_id = o.field_id and o.year = :year)
            where scenario = 0 and
            substr(landuse, :charidx, 1) = 'C'
            """),
            conn,
            params={"year": year, "charidx": charidx},
            geom_col="geom",
            parse_dates="plant",
        )

    # Spatially filter fields that are inside the climdiv region
    fields = gpd.sjoin(fields, climdiv, predicate="intersects")

    # accumulate acres planted by date
    accum = fields[["plant", "acres"]].groupby("plant").sum().cumsum()
    accum["percent"] = accum["acres"] / fields["acres"].sum() * 100.0
    accum = accum.reindex(
        pd.date_range(f"{year}-04-15", f"{year}-06-23")
    ).ffill()

    fig, ax = figure_axes(
        logo="dep",
        title=(
            f"{year} Corn Planting Progress vs "
            f"NASS Iowa Crop District {district.upper()}"
        ),
        figsize=(10.24, 7.68),
    )
    ax.set_ylim(0, 100)
    ax.set_ylabel("Percent of Acres Planted")
    ax.set_xlabel("Date")
    ax.grid(True)
    ax.plot(
        accum.index,
        accum["acres"] / fields["acres"].sum() * 100.0,
        label="DEP",
    )

    ax.scatter(
        nass["valid"],
        nass[district],
        marker="*",
        s=30,
        color="r",
        label="NASS",
    )
    ax.legend(loc=2)

    # create a table in the lower right corner with the values from
    txt = ["Date       | NASS | DEP"]
    for _, row in nass.iterrows():
        dep = accum.at[pd.Timestamp(row["valid"]), "percent"]
        txt.append(f"{row['valid']} | {row['se']:.0f} | {dep:.1f}")
    print("\n".join(txt))
    ax.text(
        0.99,
        0.01,
        "\n".join(txt),
        transform=ax.transAxes,
        fontsize=10,
        va="bottom",
        ha="right",
        bbox=dict(facecolor="white", edgecolor="black", pad=5),
    )

    fig.savefig(f"corn_progress_{year}_{district}.png")


if __name__ == "__main__":
    main()
