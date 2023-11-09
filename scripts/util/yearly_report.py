"""Generate a report for the yearly DEP totals"""
import datetime
import sys

import matplotlib.pyplot as plt
from pandas import read_sql
from pyiem.reference import state_names
from pyiem.util import get_dbconnstr


def main(argv):
    """Do What We Wanted"""
    scenario = int(argv[1])
    state = argv[2]
    lyear = datetime.date.today().year - 1
    print(f"This report covers the inclusive years 2008-{lyear} for {state}")

    df = read_sql(
        """
        WITH iahuc12 as (
            SELECT huc_12 from huc12 where states = %s and scenario = 0
        ), agg as (
            SELECT r.huc_12, extract(year from valid)::int as yr,
            sum(qc_precip) as precip, sum(avg_runoff) as runoff,
            sum(avg_delivery) as delivery,
            sum(avg_loss) as detachment from results_by_huc12 r JOIN iahuc12 i
            on (r.huc_12 = i.huc_12) WHERE r.scenario = %s
            and r.valid >= '2008-01-01'
            and r.valid <= %s GROUP by r.huc_12, yr
        )

        SELECT yr, round((avg(precip) / 25.4)::numeric, 2) as precip_in,
        round((avg(runoff) / 25.4)::numeric, 2) as runoff_in,
        round((avg(delivery) * 4.463)::numeric, 2) as delivery_ta,
        round((avg(detachment) * 4.463)::numeric, 2) as detachment_ta
        from agg GROUP by yr ORDER by yr
    """,
        get_dbconnstr("idep"),
        params=(state, scenario, datetime.date(lyear, 12, 31)),
        index_col="yr",
    )

    print(df)
    print(df.mean())

    (fig, ax) = plt.subplots(1, 1)
    ax.bar(df.index.values, df["detachment_ta"].values)
    for year, row in df.iterrows():
        ax.text(
            year,
            row["detachment_ta"] + 0.2,
            f"{row['detachment_ta']:.1f}",
            ha="center",
        )
    ax.axhline(
        df["detachment_ta"].mean(),
        label=f"mean {df['detachment_ta'].mean():.2f}",
        zorder=5,
        color="k",
        lw=1.5,
    )
    ax.legend(loc="best")
    ax.grid(True)
    ax.set_xlim(df.index.values[0] - 0.5, df.index.values[-1] + 0.5)
    ax.set_ylim(0, 3.5)
    ax.set_ylabel("Yearly Detatchment [tons/acre]")
    ax.set_title(
        f"{state_names[state]} Daily Erosion Project Iowa's Yearly Detachment"
    )
    fig.text(
        0.01,
        0.01,
        f"Plot generated {datetime.datetime.now():%d %B %Y}",
    )
    fig.savefig("test.png")


if __name__ == "__main__":
    main(sys.argv)
