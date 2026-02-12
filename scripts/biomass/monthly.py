"""Make plots of monthly values or differences"""

import calendar

import matplotlib.pyplot as plt
from pandas.io.sql import read_sql
from pyiem.database import get_dbconn

from pydep.reference import KG_M2_TO_TON_ACRE

PGCONN = get_dbconn("idep")


def get_scenario(scenario):
    """Placeholder."""
    return read_sql(
        """
        WITH yearly as (
            SELECT huc_12, generate_series(2008, 2016) as yr
            from huc12 where states = 'IA' and scenario = 0),
        combos as (
            SELECT huc_12, yr, generate_series(1, 12) as mo from yearly),
        results as (
            SELECT r.huc_12, extract(year from valid)::int as yr,
            extract(month from valid)::int as mo,
            sum(qc_precip) as precip, sum(avg_runoff) as runoff,
            sum(avg_delivery) as delivery,
            sum(avg_loss) as detachment from results_by_huc12 r
            WHERE r.scenario = %s and r.valid >= '2008-01-01'
            and r.valid < '2017-01-01' GROUP by r.huc_12, yr, mo),
        agg as (
            SELECT c.huc_12, c.yr, c.mo, coalesce(r.precip, 0) as precip,
            coalesce(r.runoff, 0) as runoff,
            coalesce(r.delivery, 0) as delivery,
            coalesce(r.detachment, 0) as detachment
            from combos c LEFT JOIN results r on (c.huc_12 = r.huc_12 and
            c.yr = r.yr and c.mo = r.mo))
        select mo,
        avg(runoff) / 25.4 as runoff_in,
        avg(delivery) * %s as delivery_ta,
        avg(detachment) * %s as detachment_ta
        from agg GROUP by mo ORDER by mo ASC
    """,
        PGCONN,
        params=(scenario, KG_M2_TO_TON_ACRE, KG_M2_TO_TON_ACRE),
        index_col="mo",
    )


def main():
    """Go Main"""
    adf = get_scenario(0)
    b25 = get_scenario(25)
    b26 = get_scenario(26)

    delta25 = b25 - adf
    delta26 = b26 - adf
    (fig, ax) = plt.subplots(1, 1)
    ax.bar(
        delta25.index.values - 0.2,
        delta25["delivery_ta"].values,
        width=0.4,
        label="HI 0.8",
    )
    ax.bar(
        delta26.index.values + 0.2,
        delta26["delivery_ta"].values,
        width=0.4,
        label="HI 0.9",
    )
    ax.legend(loc="best")
    ax.grid(True)
    ax.set_title("2008-2016 Change in Delivery vs DEP Baseline")
    ax.set_ylabel("Change [tons/acre]")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(calendar.month_abbr[1:])
    fig.savefig("test.png")


if __name__ == "__main__":
    main()
