"""Plot our planting progress vs that of NASS."""

import os
from datetime import date, timedelta

import click
import geopandas as gpd
import matplotlib.colors as mpcolors
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle
from pyiem.database import get_sqlalchemy_conn
from pyiem.plot import figure, get_cmap
from pyiem.reference import state_names
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


def compute_limits(huc12s, year):
    """Figure out how our algorithm worked."""
    rows = []
    # June 10th is mud-it-in and we have no estimates then
    for dt in pd.date_range(f"{year}-04-11", f"{year}-06-09"):
        pfn = f"/mnt/idep2/data/huc12status/{year}/{dt:%Y%m%d}.feather"
        if not os.path.isfile(pfn):
            continue
        status = pd.read_feather(pfn)
        status = status.loc[huc12s]
        sz = len(huc12s)
        rows.append(
            {
                "date": dt,
                "limited": status["limited"].sum() / sz * 100.0,
                "limited_by_soilmoisture": status[
                    "limited_by_soilmoisture"
                ].sum()
                / sz
                * 100.0,
                "limited_by_soiltemp": status["limited_by_soiltemp"].sum()
                / sz
                * 100.0,
                "limited_by_precip": status["limited_by_precip"].sum()
                / sz
                * 100.0,
            }
        )
    return pd.DataFrame(rows).set_index("date")


def get_geo_bounds(district, state):
    """Figure out what the bounds are."""
    if state is not None:
        with get_sqlalchemy_conn("postgis") as conn:
            return gpd.read_postgis(
                text(
                    """
                    select state_abbr, the_geom from states
                    where state_abbr = :state
                    """
                ),
                conn,
                params={"state": state},
                geom_col="the_geom",
                index_col="state_abbr",
            )
    with get_sqlalchemy_conn("coop") as conn:
        return gpd.read_postgis(
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


def get_nass(year, state, district, crop) -> pd.DataFrame:
    with get_sqlalchemy_conn("coop") as conn:
        if state is not None:
            nass = pd.read_sql(
                text(
                    f"""
                select num_value,
                case when statisticcat_desc = 'DAYS SUITABLE'
                then 'days suitable' else '{crop} planted' end as metric,
                week_ending as valid from nass_quickstats where
                state_alpha = :state and 
                (statisticcat_desc = 'DAYS SUITABLE' or
                 short_desc =
                 '{crop.upper()} - PROGRESS, MEASURED IN PCT PLANTED')
                and extract(year from week_ending) = :year
                order by week_ending asc
                """
                ),
                conn,
                params={"year": year, "state": state},
            )
        else:
            nass = pd.read_sql(
                text(
                    f"""
                select valid, metric, {district} as num_value from nass_iowa
                where metric in ('{crop} planted', 'days suitable')
                and extract(year from valid) = :year ORDER by valid ASc
                """
                ),
                conn,
                params={"year": year},
            )
    nass["valid"] = pd.to_datetime(nass["valid"])
    nass = nass.pivot(index="valid", columns="metric", values="num_value")
    # NASS does not always include 0% and 100% in their data, so we need to
    # fill in the blanks
    col = f"{crop} planted"
    if nass[col].min() > 0:
        firstrow = nass[nass[col] > 0].index[0]
        nass.loc[firstrow - pd.Timedelta(days=7), col] = 0
    # TODO, this may not always be right for in-progress years
    if nass[col].max() < 100:
        lastrow = nass[nass[col] > 0].index[-1]
        nass.loc[lastrow + pd.Timedelta(days=7), col] = 100
    # Create space for DEP to store things
    nass[f"dep_{crop}_planted"] = np.nan
    nass["dep_days_suitable"] = np.nan
    return nass


def get_fields(year, district, state, crop) -> gpd.GeoDataFrame:
    """Compute the fields."""
    charidx = year - 2007 + 1
    boundsdf = get_geo_bounds(district, state)
    # Figure out the planting dates
    with get_sqlalchemy_conn("idep") as conn:
        fields = gpd.read_postgis(
            text("""
            select st_transform(geom, 4326) as geom, plant, huc12, fbndid,
            acres from fields f JOIN field_operations o
            on (f.field_id = o.field_id and o.year = :year)
            where scenario = 0 and substr(landuse, :charidx, 1) = :ccode
            """),
            conn,
            params={
                "year": year,
                "ccode": "C" if crop == "corn" else "B",
                "charidx": charidx,
            },
            geom_col="geom",
            parse_dates="plant",
        )
    fields = gpd.sjoin(fields, boundsdf, predicate="intersects")
    return fields


def get_labels(year):
    """Figure out where we should place xticks."""
    xticks = []
    xticklabels = []
    for dt in pd.date_range(f"{year}-04-11", f"{year}-06-20"):
        if dt.dayofweek == 6:
            xticks.append(dt)
            xticklabels.append(f"{dt:%b %-d}")
    return xticks, xticklabels


@click.command()
@click.option("--year", type=int, help="Year to plot")
@click.option("--district", type=str, help="NASS District (lowercase)")
@click.option("--state", type=str, help="State to Process.")
@click.option(
    "--crop",
    type=click.Choice(["corn", "soybeans"]),
    default="corn",
    help="Crop to Process",
)
def main(year, district, state, crop):
    """Go Main Go."""
    nass = get_nass(year, state, district, crop)
    fields = get_fields(year, district, state, crop)

    xticks, xticklabels = get_labels(year)

    # Spatially filter fields that are inside the climdiv region
    daily_limits = compute_limits(fields["huc12"].unique(), year)

    # accumulate acres planted by date
    accum = fields[["plant", "acres"]].groupby("plant").sum().cumsum()
    accum["percent"] = accum["acres"] / fields["acres"].sum() * 100.0
    # Need to forward fill so that we have comparables with NASS
    ldate = f"{year}-06-22"
    if ldate >= f"{date.today():%Y-%m-%d}":
        ldate = f"{(date.today() - timedelta(days=1)):%Y-%m-%d}"
    accum = accum.reindex(pd.date_range(f"{year}-04-11", ldate)).ffill()
    nass = nass.reindex(accum.index)
    nass.index.name = "valid"
    nass["dep_corn_planted"] = accum["percent"]

    if state is not None:
        title = f"state of {state_names[state]}"
    else:
        title = f"Iowa District {district.upper()}"
    fig = figure(
        logo="dep",
        title=(
            f"{year} DEP Dynamic Tillage {crop.capitalize()} "
            "Planting Progress"
        ),
        subtitle=f"Comparison with USDA NASS Weekly Progress for {title}",
        figsize=(10.24, 7.68),
    )

    ax = fig.add_axes([0.1, 0.05, 0.8, 0.14])
    # Going to create a imshow plot with each day being a column and then
    # four cells per day for the four different limiting factors
    data = np.zeros((4, len(daily_limits.index)))
    i = 0
    for _, row in daily_limits.iterrows():
        data[:, i] = [
            row["limited"],
            row["limited_by_soilmoisture"],
            row["limited_by_soiltemp"],
            row["limited_by_precip"],
        ]
        i += 1
    cmap = get_cmap("viridis")
    norm = mpcolors.BoundaryNorm(np.arange(0, 101, 10), cmap.N)
    res = ax.imshow(
        data,
        extent=[
            daily_limits.index[0],
            daily_limits.index[-1] + pd.Timedelta(days=1),
            3.5,
            -0.5,
        ],
        aspect="auto",
        interpolation="nearest",
        norm=norm,
        cmap=cmap,
    )
    ax.set_yticks(range(4))
    ax.set_yticklabels(
        ["Combined", "Soil Moisture", "Soil Temp", "Precipitation"]
    )
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels)
    ax.text(0.02, 1.05, "Limiting Factors", transform=ax.transAxes)
    cax = fig.add_axes([0.92, 0.05, 0.02, 0.2])
    fig.colorbar(res, cax=cax, label="Percent of HUC12s Limited")

    # ////////////////////////////////////////////////////////////
    # axes showing the days suitable as little boxes for each seven day period
    # and the value of the days suitable for that period in the middle
    ax3 = fig.add_axes([0.1, 0.25, 0.8, 0.07])
    for valid, row in nass.iterrows():
        ax3.add_patch(
            Rectangle(
                (valid - pd.Timedelta(days=7), 0),
                pd.Timedelta(days=7),
                1,
                ec="k",
                fc="None",
            )
        )
        ax3.text(
            valid - pd.Timedelta(days=3.5),
            0.5,
            f"{row['days suitable']:.1f}",
            ha="center",
            va="center",
        ).set_clip_on(True)
        # Value estimted from daily_limits
        thisweek = daily_limits.loc[valid - pd.Timedelta(days=6) : valid][
            "limited"
        ]
        depdays = 7.0 - thisweek.mean() / 100.0 * 7
        if pd.notna(depdays) and len(thisweek.index) == 7:
            nass.at[valid, "dep_days_suitable"] = depdays
            ax3.add_patch(
                Rectangle(
                    (valid - pd.Timedelta(days=7), 1),
                    pd.Timedelta(days=7),
                    1,
                    ec="k",
                    fc="None",
                )
            )
            ax3.text(
                valid - pd.Timedelta(days=3.5),
                1.5,
                f"{depdays:.1f}",
                ha="center",
                va="center",
            ).set_clip_on(True)
    ax3.set_ylim(0, 2)
    ax3.set_yticks([0.5, 1.5])
    ax3.set_yticklabels(["NASS", "DEP Est."])
    ax3.set_xticks([])
    ax3.text(0.02, 1.05, "Days Suitable", transform=ax3.transAxes)

    # ////////////////////////////////////////////////////////////
    ax2 = fig.add_axes([0.1, 0.4, 0.8, 0.5])
    ax2.set_ylim(-2, 102)
    ax2.set_yticks(range(0, 101, 10))
    ax2.set_ylabel("Percent of Acres Planted")
    ax2.grid(True)
    ax2.plot(
        accum.index,
        accum["acres"] / fields["acres"].sum() * 100.0,
        label="DEP DynTillv2",
    )
    ax2.scatter(
        nass.index.values,
        nass[f"{crop} planted"],
        marker="*",
        s=30,
        color="r",
        label="NASS",
    )
    ax2.legend(loc=2)

    # create a table in the lower right corner with the values from
    txt = ["Weekly Progress", "Date   NASS DEP"]
    for valid, row in nass.iterrows():
        if valid not in accum.index:
            continue
        dep = accum.at[valid, "percent"]
        val = row[f"{crop} planted"]
        txt.append(f"{valid:%b %-2d}:  {val:3.0f} {dep:3.0f}")
    ax2.text(
        1.05,
        0.05,
        "\n".join(txt),
        transform=ax2.transAxes,
        fontsize=10,
        fontfamily="monospace",
        va="bottom",
        ha="right",
        bbox=dict(facecolor="white", edgecolor="black", pad=5),
    )
    ax2.set_xticks(xticks)
    ax2.set_xticklabels(xticklabels)

    # Sync up the two xaxes

    ax.set_xlim(*ax2.get_xlim())
    ax3.set_xlim(*ax2.get_xlim())

    nass.to_csv(
        f"plotsv2/{crop}_{year}_"
        f"{district if district is not None else state}.csv",
        float_format="%.2f",
    )

    ss = f"state_{state}"
    fig.savefig(
        f"plotsv2/{crop}_progress_{year}_"
        f"{district if district is not None else ss}.png"
    )


if __name__ == "__main__":
    main()
