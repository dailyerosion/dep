"""Figure out what the progress / days suitable looks like."""

from datetime import date, timedelta

import click
import numpy as np
import pandas as pd
from pyiem.database import get_sqlalchemy_conn, sql_helper
from pyiem.plot import figure_axes

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

    (fig, ax) = figure_axes(
        title=f"NASS Weekly {crop} Planting Progress / Days Suitable",
        figsize=(10.72, 7.2),
        logo="dep",
    )
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

    ax.set_xlim(*xlim)

    ax.set_ylabel(f"Weekly {crop} Planting Progress / Days Suitable [pp/d]")
    fig.savefig(f"plots/nass_weekly_ratio_{crop}.png")


if __name__ == "__main__":
    main()
