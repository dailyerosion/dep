"""Summarize for MLRA, somehow"""

import sys

from pandas.io.sql import read_sql
from pyiem.plot.use_agg import plt
from pyiem.util import get_dbconn

LABELS = {
    29: "CC No-Till",
    30: "CS Conv w/ Cover",
    31: "CS Conv",
    32: "CS Plow",
    33: "CS No-Till",
    34: "CS No-Till Cover",
    35: "CSWC No-Till",
}


def main(argv):
    """Go Main Go"""
    mlra_id = int(argv[1])
    pgconn = get_dbconn("idep")

    fig, ax = plt.subplots(3, 7, figsize=(12, 6))

    mlraxref = read_sql(
        """
    select mlra_id, mlra_name from mlra
    """,
        pgconn,
        index_col="mlra_id",
    )
    fig.text(
        0.5,
        0.96,
        ("CSCAP Yearly Scenario Changes for MLRA: %s [%s]")
        % (mlraxref.at[mlra_id, "mlra_name"], mlra_id),
        ha="center",
        fontsize=16,
    )

    for col, scenario in enumerate(range(29, 36)):
        df = read_sql(
            """
        with myhucs as (
            SELECT huc_12 from huc12 where scenario = 0 and mlra_id = %s
        )
        select r.huc_12, scenario, extract(year from valid)::int as year,
        sum(avg_loss) * 4.463 as loss, sum(avg_runoff) as runoff,
        sum(avg_delivery) * 4.463 as delivery
        from results_by_huc12 r JOIN myhucs h on (r.huc_12 = h.huc_12)
        where r.valid >= '2008-01-01' and r.valid < '2017-01-01'
        and (scenario = 28 or scenario = %s)
        GROUP by r.huc_12, year, scenario
        """,
            pgconn,
            params=(mlra_id, scenario),
            index_col=None,
        )
        gdf = df.groupby(("scenario", "year")).mean()
        delta = gdf.loc[(scenario,)] - gdf.loc[(28,)]
        for row, varname in enumerate(["runoff", "loss", "delivery"]):
            ax[row, col].bar(
                delta.index.values,
                delta[varname],
                color=["b" if x > 0 else "r" for x in delta[varname].values],
            )
            if row == 0:
                ax[row, col].set_title(
                    "Scenario %s\n%s" % (scenario, LABELS[scenario])
                )
    ylabels = ["Runoff [mm]", "Loss [T/a]", "Delivery [T/a]"]
    for row in range(3):
        ymin = 99
        ymax = -99
        for col in range(7):
            ylim = ax[row, col].get_ylim()
            ymin = min([ylim[0], ymin])
            ymax = max([ylim[1], ymax])
        for col in range(7):
            ax[row, col].set_ylim(ymin, ymax)
            ax[row, col].grid(True)
            if col > 0:
                ax[row, col].set_yticklabels([])
            else:
                ax[row, col].set_ylabel(ylabels[row])

    fig.savefig("test.png")


if __name__ == "__main__":
    main(sys.argv)
