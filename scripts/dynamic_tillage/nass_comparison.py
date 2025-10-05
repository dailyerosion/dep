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
    "IA_NW": "IAC001",
    "IA_NC": "IAC002",
    "IA_NE": "IAC003",
    "IA_WC": "IAC004",
    "IA_C": "IAC005",
    "IA_EC": "IAC006",
    "IA_SW": "IAC007",
    "IA_SC": "IAC008",
    "IA_SE": "IAC009",
    "MN_NW": "MNC001",
    "MN_NC": "MNC002",
    "MN_NE": "MNC003",
    "MN_WC": "MNC004",
    "MN_C": "MNC005",
    "MN_EC": "MNC006",
    "MN_SW": "MNC007",
    "MN_SC": "MNC008",
    "MN_SE": "MNC009",
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


def get_geo_bounds(datum: str, ugc: str | None):
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
    if len(datum) == 2:
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
                params={"state": datum},
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
            params={"sid": XREF[datum]},
            geom_col="geo",
            index_col="iemid",
        )


def get_nass(year: int, datum: str, crop: str) -> pd.DataFrame:
    """Get the NASS data."""
    with get_sqlalchemy_conn("coop") as conn:
        nass = pd.read_sql(
            sql_helper(
                f"""
            select num_value,
            case when statisticcat_desc = 'DAYS SUITABLE'
            then 'days suitable' else '{crop} planted' end as metric,
            week_ending as date,
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
        if datum.startswith("IA"):  # Iowa has district
            district = pd.read_sql(
                sql_helper(
                    f"""
                select valid as date, metric, nw, nc, ne, wc, c, ec, sw, sc, se
                from nass_iowa
                where metric in ('{crop} planted', 'days suitable')
                and extract(year from valid) = :year ORDER by valid ASC
                """
                ),
                conn,
                params={"year": year},
            )
            slices = []
            for dist in ["nw", "nc", "ne", "wc", "c", "ec", "sw", "sc", "se"]:
                ddf = (
                    district[["date", "metric", dist]]
                    .copy()
                    .rename(columns={dist: "num_value"})
                )
                ddf["datum"] = f"IA_{dist.upper()}"
                slices.append(ddf)
            nass = pd.concat([nass, *slices])
    # NASS does not always include 0% and 100% in their data, so we need to
    # fill in the blanks
    metric = f"{crop} planted"
    newrows = []
    for datum, gdf in nass[nass["metric"] == metric].groupby("datum"):
        if gdf["num_value"].min() > 0:
            firstrow = gdf.loc[gdf["num_value"] > 0, "date"].values[0]
            newrows.append(
                {
                    "num_value": 0,
                    "metric": metric,
                    "date": firstrow - pd.Timedelta(days=7),
                    "datum": datum,
                }
            )
        # TODO, this may not always be right for in-progress years
        if gdf["num_value"].max() < 100:
            lastrow = gdf.loc[gdf["num_value"] > 0, "date"].values[-1]
            newrows.append(
                {
                    "num_value": 100,
                    "metric": metric,
                    "date": lastrow + pd.Timedelta(days=7),
                    "datum": datum,
                }
            )
    if newrows:
        nass = pd.concat([nass, pd.DataFrame(newrows)])
    # Make dataframe more usable
    nass = nass.pivot_table(
        index=["datum", "date"], columns="metric", values="num_value"
    ).reset_index()
    # Create space for DEP to store things
    nass[f"dep_{crop}_planted"] = np.nan
    nass["dep_days_suitable"] = np.nan
    nass["date"] = pd.to_datetime(nass["date"])
    return nass


def get_fields(year, datum: str, ugc: str | None, crop) -> pd.DataFrame:
    """Compute the fields."""
    charidx = year - 2007 + 1
    boundsdf = get_geo_bounds(datum, ugc)
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
    for dt, row in nass[nass["days suitable"].notna()].iterrows():
        ax3.add_patch(
            Rectangle(
                (dt - pd.Timedelta(days=7), 0),
                pd.Timedelta(days=7),
                1,
                ec="k",
                fc="None",
            )
        )
        ax3.text(
            dt - pd.Timedelta(days=3.5),
            0.5,
            f"{row['days suitable']:.1f}",
            ha="center",
            va="center",
        ).set_clip_on(True)
        # Value estimted from daily_limits
        thisweek = daily_limits.loc[dt - pd.Timedelta(days=6) : dt]["limited"]
        depdays = 7.0 - thisweek.mean() / 100.0 * 7
        if pd.notna(depdays) and len(thisweek.index) == 7:
            nass.at[dt, "dep_days_suitable"] = depdays
            ax3.add_patch(
                Rectangle(
                    (dt - pd.Timedelta(days=7), 1),
                    pd.Timedelta(days=7),
                    1,
                    ec="k",
                    fc="None",
                )
            )
            ax3.text(
                dt - pd.Timedelta(days=3.5),
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
        for dt, gdf in nass_all[nass_all["datum"] != "IA"].groupby("date"):
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
        nass = nass_all[nass_all["datum"] == datum].copy().set_index("date")
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
        for dt, row in nass[nass["days suitable"].notna()].iterrows():
            if dt not in accum.index:
                continue
            dep = accum.at[dt, "percent"]
            val = row[f"{crop} planted"]
            txt.append(f"{dt:%b %-2d}:  {val:3.0f} {dep:3.0f}")
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


def plot_dep(ax, year: int, datum: str):
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
    if datum == "IA":
        dates = [date(year, 4, 30), date(year, 5, 5), date(year, 5, 10)]
        progress = [33, 66, 100]
    else:
        key = "MN"
        dates = [lookup[key]]
    dates.insert(0, dates[0] - timedelta(days=1))
    progress.insert(0, 0)
    dates.append(dates[-1] + timedelta(days=1))
    progress.append(100)
    ax.plot(dates, progress, label="DEP Static")


def get_deines(year: int, datum, _ugc, crop) -> pd.DataFrame | None:
    """Sample what we need."""
    if year > 2020:
        return None
    df = pd.read_csv(f"deines2023_datum_{crop}.csv", parse_dates=["date"])
    return df[(df["year"] == year) & (df["datum"] == datum)].set_index("date")


@click.command()
@click.option("--year", required=True, type=int, help="Year to plot")
@click.option("--datum", type=str, help="Datum to Process.")
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
    datum: Optional[str],
    ugc: Optional[str],
    crop: str,
    plotv2: bool,
    plotv3: bool,
    plotdep: bool,
):
    """Go Main Go."""
    nass_all = None
    nass = None
    if ugc is not None:
        datum = ugc
    elif len(datum) == 2 or datum.startswith("IA"):
        nass_all = get_nass(year, datum, crop)
        nass = nass_all[nass_all["datum"] == datum].copy().set_index("date")

    finaldf = pd.DataFrame(
        index=pd.date_range(f"{year}/04/01", f"{year}/07/01", name="date")
    )
    finaldf["datum"] = datum

    deinesdf = get_deines(year, datum, ugc, crop)
    if deinesdf is not None:
        finaldf[f"deines2023_{crop}_pct"] = deinesdf["pct"]
        finaldf[f"deines2023_{crop}_acres"] = deinesdf["acres"]

    pngname = f"plots/{crop}_progress_{year}_{datum}.png"
    fields = get_fields(year, datum, ugc, crop)

    xticks, xticklabels = get_labels(year)

    # Spatially filter fields that are inside the climdiv region
    daily_limits = compute_limits(fields["huc12"].unique(), year)

    # accumulate acres planted by date
    fgb = fields[["plant", "acres"]].groupby("plant")
    accum = fgb.sum().cumsum()
    accum["percent"] = accum["acres"] / fields["acres"].sum() * 100.0
    # Need to forward fill so that we have comparables with NASS
    ldate = f"{year}-06-22"
    if ldate >= f"{date.today():%Y-%m-%d}":
        ldate = f"{(date.today() - timedelta(days=1)):%Y-%m-%d}"
    accum = accum.reindex(pd.date_range(f"{year}-04-11", ldate))
    finaldf[f"dep_{crop}_pct"] = accum["percent"]
    finaldf[f"dep_{crop}_acres"] = fgb.sum()
    if nass is not None:
        nass = nass.reindex(accum.index)
        nass.index.name = "date"
        nass[f"dep_{crop}_planted"] = accum["percent"]
        finaldf[f"nass_{crop}_pct"] = nass[f"{crop} planted"]

    if len(datum) == 2:
        title = f"state of {state_names[datum]}"
    elif ugc is not None:
        title = f"UGC {ugc.upper()}"
    else:
        title = f"Crop Reporting District of {datum}"
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
    if deinesdf is not None:
        ax2.plot(deinesdf.index, deinesdf["pct"], label="Deines2023")
    ax2.set_xticks(xticks)
    ax2.set_xticklabels(xticklabels)
    if plotv2:
        plot_v(ax2, 2, crop, year, datum)
    if plotv3:
        plot_v(ax2, 3, crop, year, datum)
    if plotdep:
        plot_dep(ax2, year, datum)
    ax2.legend(loc=2)

    # Sync up the two xaxes

    ax.set_xlim(*ax2.get_xlim())
    if ax3:
        ax3.set_xlim(*ax2.get_xlim())

    # plots is symlinked
    finaldf.to_csv(f"plots/{crop}_{year}_{datum}.csv", float_format="%.2f")

    # plots is symlinked
    fig.savefig(pngname)
    LOG.info("%s %s done", year, datum)


if __name__ == "__main__":
    main()
