"""Figure out what the progress / days suitable looks like."""

from datetime import date, timedelta

import click
import numpy as np
import pandas as pd
from pyiem.database import get_sqlalchemy_conn, sql_helper
from pyiem.plot import figure

from pydep.workflows.dyntillage import (
    get_planting_fraction,
    get_soybeans_planting_fraction,
)


@click.command()
@click.option("--crop", required=True)
def main(crop: str):
    """Go Main Go."""
    total_traction = get_planting_fraction()
    soybeans_fraction = get_soybeans_planting_fraction()
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
            and year > 2006
            order by week_ending asc
            """
            ),
            conn,
            parse_dates=["date"],
        )
    nass = nass.pivot(
        index="date", columns=["metric", "datum"], values="num_value"
    ).reset_index()
    nass["doy"] = nass["date"].dt.dayofyear
    nass["year"] = nass["date"].dt.year

    # Compute the weekly delta in 'corn planted'
    for state in ["IA", "NE", "KS", "MN"]:
        col_name = (f"{crop} planted delta", state)
        source_col = (f"{crop} planted", state)
        nass[col_name] = nass[source_col].diff().shift(1)

    fig = figure(
        title=f"NASS Weekly {crop} Planting Progress / Days Suitable",
        figsize=(10.72, 7.2),
        logo="dep",
    )
    ax = fig.add_axes((0.1, 0.5, 0.8, 0.4))
    for state in ["IA", "NE", "KS", "MN"]:
        ax.scatter(
            nass["doy"].to_numpy(),
            nass[(f"{crop} planted delta", state)].to_numpy()
            / nass[("days suitable", state)].to_numpy(),
            label=state,
        )
    ax.grid(True)
    ax.legend()

    xticks = []
    xticklabels = []
    xlim = ax.get_xlim()
    for i in range(int(xlim[0]), int(xlim[1])):
        dt = date(2000, 1, 1) + timedelta(days=i - 1)
        if dt.day in [1, 8, 15, 22]:
            xticks.append(i)
            xticklabels.append(dt.strftime("%-d\n%b"))
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels)

    if crop == "soybeans":
        rates = total_traction * soybeans_fraction * 100.0
    else:
        rates = total_traction * (1.0 - soybeans_fraction) * 100.0

    ax.plot(
        np.arange(1, 367),  # hack around leap day
        rates,
        ds="steps-post",
        lw=2,
        color="k",
    )
    # Tricky to plot, but here we are
    rates2 = np.where(rates > 4.99, 10.0, rates)
    ax.plot(
        np.arange(1, 367),  # hack around leap day
        rates2,
        ds="steps-post",
        lw=3,
        color="yellow",
    )
    ax.plot(
        np.arange(1, 367),  # hack around leap day
        rates2,
        ds="steps-post",
        lw=1,
        color="k",
    )

    ax.set_xlim(*xlim)
    ax.set_ylabel(f"Weekly {crop} Progress /\nDays Suitable [pp/d]")

    # -----------------------
    # Plot the percentage of obs above the threshold
    ax2 = fig.add_axes((0.1, 0.1, 0.8, 0.3))
    xvals = list(range(int(xlim[0]), int(xlim[1]) + 1))
    yvals = []
    for x in xvals:
        # Get nass data within five days of this x value
        df2 = nass[(nass["doy"] >= x - 2) & (nass["doy"] <= x + 2)]
        total = 0
        hits = 0
        for state in ["MN", "IA", "KS", "NE"]:
            df3 = (
                df2[(f"{crop} planted delta", state)].to_numpy()
                / df2[("days suitable", state)].to_numpy()
            ) >= rates2[x]
            hits += np.sum(df3)
            total += df3.shape[0]
        yvals.append(100.0 * hits / total if total > 0 else 0)

    ax2.plot(xvals, yvals, lw=2, color="k")
    ax2.set_ylabel("% of Rates Above Algo")
    ax2.grid(True)
    ax2.set_xlim(*xlim)
    ax2.set_xticks(xticks)
    ax2.set_xticklabels(xticklabels)

    fig.savefig(f"plots/nass_weekly_ratio_{crop}.png")


if __name__ == "__main__":
    main()
