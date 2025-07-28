"""Plot our planting progress vs that of NASS."""

import os
from datetime import date, timedelta
from typing import Optional

import click
import geopandas as gpd
import matplotlib.colors as mpcolors
import numpy as np
import pandas as pd
from matplotlib.dates import date2num
from matplotlib.patches import Rectangle
from pyiem.database import get_sqlalchemy_conn, sql_helper
from pyiem.plot import figure, get_cmap
from pyiem.reference import state_names
from pyiem.util import logger

LOG = logger()
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
UGCHACK = {
    "MNC005": "Becker",
    "MNC027": "Clay",
    "MNC127": "Redwood",
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


def get_geo_bounds(district, state, ugc: str | None):
    """Figure out what the bounds are."""
    if ugc is not None:
        with get_sqlalchemy_conn("postgis") as conn:
            return gpd.read_postgis(
                sql_helper(
                    """
                    select ugc, ST_Transform(geom, 5070) as geo
                    from ugcs where ugc = :ugc and end_ts is null
                    """
                ),
                conn,
                crs=5070,
                params={"ugc": ugc},
                geom_col="geo",
                index_col="ugc",
            )
    if state is not None:
        with get_sqlalchemy_conn("postgis") as conn:
            return gpd.read_postgis(
                sql_helper(
                    """
                    select state_abbr, ST_Transform(the_geom, 5070) as geo
                    from states where state_abbr = :state
                    """
                ),
                conn,
                crs=5070,
                params={"state": state},
                geom_col="geo",
                index_col="state_abbr",
            )
    with get_sqlalchemy_conn("coop") as conn:
        return gpd.read_postgis(
            sql_helper(
                """
                select t.iemid, ST_Transform(r.geom, 5070) as geo
                from climodat_regions r JOIN stations t
                on (r.iemid = t.iemid) where t.id = :sid
                """
            ),
            conn,
            crs=5070,
            params={"sid": XREF[district]},
            geom_col="geo",
            index_col="iemid",
        )


def get_nass(year, state, district, crop) -> pd.DataFrame:
    """Get the NASS data."""
    with get_sqlalchemy_conn("coop") as conn:
        nass = pd.read_sql(
            sql_helper(
                f"""
            select num_value,
            case when statisticcat_desc = 'DAYS SUITABLE'
            then 'days suitable' else '{crop} planted' end as metric,
            week_ending as valid,
            state_alpha as datum
            from nass_quickstats where
            state_alpha in ('IA', 'NE', 'KS', 'MN') and
            (statisticcat_desc = 'DAYS SUITABLE' or
                short_desc =
                '{crop.upper()} - PROGRESS, MEASURED IN PCT PLANTED')
            and extract(year from week_ending) = :year
            order by week_ending asc
            """
            ),
            conn,
            params={"year": year},
        )
        if state == "IA" or district is not None:  # Iowa has district
            district = pd.read_sql(
                sql_helper(
                    f"""
                select valid, metric, nw, nc, ne, wc, c, ec, sw, sc, se
                from nass_iowa
                where metric in ('{crop} planted', 'days suitable')
                and extract(year from valid) = :year ORDER by valid ASc
                """
                ),
                conn,
                params={"year": year},
            )
            slices = []
            for dist in ["nw", "nc", "ne", "wc", "c", "ec", "sw", "sc", "se"]:
                ddf = (
                    district[["valid", "metric", dist]]
                    .copy()
                    .rename(columns={dist: "num_value"})
                )
                ddf["datum"] = dist
                slices.append(ddf)
            nass = pd.concat([nass, *slices])
    # NASS does not always include 0% and 100% in their data, so we need to
    # fill in the blanks
    metric = f"{crop} planted"
    newrows = []
    for datum, gdf in nass[nass["metric"] == metric].groupby("datum"):
        if gdf["num_value"].min() > 0:
            firstrow = gdf.loc[gdf["num_value"] > 0, "valid"].values[0]
            newrows.append(
                {
                    "num_value": 0,
                    "metric": metric,
                    "valid": firstrow - pd.Timedelta(days=7),
                    "datum": datum,
                }
            )
        # TODO, this may not always be right for in-progress years
        if gdf["num_value"].max() < 100:
            lastrow = gdf.loc[gdf["num_value"] > 0, "valid"].values[-1]
            newrows.append(
                {
                    "num_value": 100,
                    "metric": metric,
                    "valid": lastrow + pd.Timedelta(days=7),
                    "datum": datum,
                }
            )
    if newrows:
        nass = pd.concat([nass, pd.DataFrame(newrows)])
    # Make dataframe more usable
    nass = nass.pivot_table(
        index=["datum", "valid"], columns="metric", values="num_value"
    ).reset_index()
    # Create space for DEP to store things
    nass[f"dep_{crop}_planted"] = np.nan
    nass["dep_days_suitable"] = np.nan
    nass["valid"] = pd.to_datetime(nass["valid"])
    return nass


def get_fields(year, district, state, ugc: str | None, crop) -> pd.DataFrame:
    """Compute the fields."""
    charidx = year - 2007 + 1
    boundsdf = get_geo_bounds(district, state, ugc)
    # Figure out the planting dates
    with get_sqlalchemy_conn("idep") as conn:
        return pd.read_sql(
            sql_helper("""
            select plant, huc12, fbndid, acres
            from fields f JOIN field_operations o
            on (f.field_id = o.field_id and o.year = :year)
            where scenario = 0 and substr(landuse, :charidx, 1) = :ccode and
            ST_Intersects(geom, ST_SetSRID(ST_GeomFromEWKT(:geom), 5070))
            """),
            conn,
            params={
                "year": year,
                "ccode": "C" if crop == "corn" else "B",
                "charidx": charidx,
                "geom": boundsdf["geo"].iloc[0].wkt,
            },
            parse_dates="plant",
        )


def get_labels(year):
    """Figure out where we should place xticks."""
    xticks = []
    xticklabels = []
    for dt in pd.date_range(f"{year}-04-11", f"{year}-06-20"):
        if dt.dayofweek == 6:
            xticks.append(dt)
            xticklabels.append(f"{dt:%b %-d}")
    return xticks, xticklabels


def plot_limiters(fig, daily_limits):
    """Heatmap of limiters."""
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
    ax.text(0.02, 1.05, "Limiting Factors", transform=ax.transAxes)
    cax = fig.add_axes([0.92, 0.05, 0.02, 0.2])
    fig.colorbar(res, cax=cax, label="Percent of HUC12s Limited")
    return ax


def plot_suitable(fig, nass, daily_limits):
    """Plot days suitable."""
    if nass is None:
        return None
    ax3 = fig.add_axes([0.1, 0.25, 0.8, 0.07])
    for valid, row in nass[nass["days suitable"].notna()].iterrows():
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
    return ax3


def plot_accum(
    fig, accum: pd.DataFrame, crop, nass_all: pd.DataFrame, datum: str
):
    """Plot the accumulation."""
    ax2 = fig.add_axes([0.1, 0.4, 0.8, 0.5])
    ax2.set_ylim(-2, 102)
    ax2.set_yticks(range(0, 101, 10))
    ax2.set_ylabel("Percent of Acres Planted")
    ax2.grid(True)
    ax2.plot(
        date2num(accum.index.date),
        accum["percent"].values,
        label="DEP DynTillv4",
    )
    if datum == "IA":
        # Plot the daily district data as a filled bar
        boxinfo = []
        positions = []
        for dt, gdf in nass_all[nass_all["datum"] != "IA"].groupby("valid"):
            stats = gdf[f"{crop} planted"].describe()
            if pd.isna(stats["mean"]):
                continue
            positions.append(date2num(dt))
            boxinfo.append(
                {
                    "med": stats["50%"],
                    "q1": stats["25%"],
                    "q3": stats["75%"],
                    "whislo": stats["min"],
                    "whishi": stats["max"],
                }
            )
        ax2.bxp(
            boxinfo,
            positions=positions,
            widths=1,
            showfliers=False,
            showmeans=False,
            shownotches=False,
            manage_ticks=False,
            label="District Range",
        )
    if nass_all is not None:
        nass = nass_all[nass_all["datum"] == datum].copy().set_index("valid")
        ax2.scatter(
            nass.index.values,
            nass[f"{crop} planted"],
            marker="s",
            s=30,
            color="r",
            label="NASS",
        )

        # create a table in the lower right corner with the values from
        txt = ["Weekly Progress", "Date   NASS DEP"]
        for valid, row in nass[nass["days suitable"].notna()].iterrows():
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
    return ax2


def plot_v(ax2, v: int, crop, year, district, state):
    """Plot v2."""
    v2df = pd.read_csv(
        f"plotsv{v}/{crop}_{year}_{district if state is None else state}.csv",
        parse_dates=["valid"],
    )
    v2df["valid"] = v2df["valid"].dt.date
    ax2.plot(
        v2df["valid"].values,
        v2df[f"dep_{crop}_planted"],
        label=f"DEP DynTillv{v}",
    )


def plot_dep(ax, year: int, state: Optional[str], district: Optional[str]):
    """Overlay the hard coded date."""
    progress = [100]
    lookup = {
        "MN": date(year, 5, 10),
        "nw": date(year, 5, 10),
        "nc": date(year, 5, 10),
        "ne": date(year, 5, 10),
        "wc": date(year, 5, 5),
        "c": date(year, 5, 5),
        "ec": date(year, 5, 5),
        "sw": date(year, 4, 30),
        "sc": date(year, 4, 30),
        "se": date(year, 4, 30),
    }
    # This is not an exact science and corn only at the moment
    if state == "IA":
        dates = [date(year, 4, 30), date(year, 5, 5), date(year, 5, 10)]
        progress = [33, 66, 100]
    else:
        key = state if state == "MN" else district
        dates = [lookup[key]]
    dates.insert(0, dates[0] - timedelta(days=1))
    progress.insert(0, 0)
    dates.append(dates[-1] + timedelta(days=1))
    progress.append(100)
    ax.plot(dates, progress, label="DEP Static")


@click.command()
@click.option("--year", required=True, type=int, help="Year to plot")
@click.option("--district", type=str, help="NASS District (lowercase)")
@click.option("--state", type=str, help="State to Process.")
@click.option("--ugc", type=str, help="UGC to Process, no NASS.")
@click.option(
    "--crop",
    type=click.Choice(["corn", "soybeans"]),
    default="corn",
    help="Crop to Process",
)
@click.option("--plotv2", is_flag=True, help="Plot v2")
@click.option("--plotv3", is_flag=True, help="Plot v3")
@click.option("--plotdep", is_flag=True, help="Plot DEP")
def main(
    year: int,
    district: Optional[str],
    state: Optional[str],
    ugc: Optional[str],
    crop: str,
    plotv2: bool,
    plotv3: bool,
    plotdep: bool,
):
    """Go Main Go."""
    datum: str = state if state is not None else district
    ss = f"state_{state}"
    pngname = (
        f"plots/{crop}_progress_{year}_"
        f"{district if district is not None else ss}.png"
    )
    if ugc is not None:
        datum = ugc
        nass_all = None
        nass = None
        pngname = f"plots/{crop}_progress_{year}_{ugc}.png"
    else:
        nass_all = get_nass(year, state, district, crop)
        nass = nass_all[nass_all["datum"] == datum].copy().set_index("valid")
    fields = get_fields(year, district, state, ugc, crop)

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
    if nass is not None:
        nass = nass.reindex(accum.index)
        nass.index.name = "valid"
        nass[f"dep_{crop}_planted"] = accum["percent"]

    if state is not None:
        title = f"state of {state_names[state]}"
    elif ugc is not None:
        title = f"UGC {ugc.upper()}"
    else:
        title = f"Iowa District {district.upper()}"
    subtitle = f"Comparison with USDA NASS Weekly Progress for {title}"
    if ugc:
        subtitle = f"Progress for [{ugc}] {UGCHACK.get(ugc, ugc)}"
    fig = figure(
        logo="dep",
        title=(
            f"{year} DEP Dynamic Tillage {crop.capitalize()} Planting Progress"
        ),
        subtitle=subtitle,
        figsize=(10.24, 7.68),
    )

    ax = plot_limiters(fig, daily_limits)
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels)

    # ////////////////////////////////////////////////////////////
    # axes showing the days suitable as little boxes for each seven day period
    # and the value of the days suitable for that period in the middle
    ax3 = plot_suitable(fig, nass, daily_limits)

    # ////////////////////////////////////////////////////////////
    ax2 = plot_accum(fig, accum, crop, nass_all, datum)
    ax2.set_xticks(xticks)
    ax2.set_xticklabels(xticklabels)
    if plotv2:
        plot_v(ax2, 2, crop, year, district, state)
    if plotv3:
        plot_v(ax2, 3, crop, year, district, state)
    if plotdep:
        plot_dep(ax2, year, state, district)
    ax2.legend(loc=2)

    # Sync up the two xaxes

    ax.set_xlim(*ax2.get_xlim())
    if ax3:
        ax3.set_xlim(*ax2.get_xlim())

    if nass is not None:
        # plots is symlinked
        nass.to_csv(
            f"plots/{crop}_{year}_"
            f"{district if district is not None else state}.csv",
            float_format="%.2f",
        )

    # plots is symlinked
    fig.savefig(pngname)
    LOG.info("%s done", year)


if __name__ == "__main__":
    main()
