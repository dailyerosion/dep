"""Legacy."""

import matplotlib.pyplot as plt
import pandas as pd
from pyiem.database import get_sqlalchemy_conn, sql_helper

from dailyerosion.reference import KG_M2_TO_TON_ACRE


def main():
    """Go Main Go."""
    with get_sqlalchemy_conn("idep") as conn:
        df = pd.read_sql(
            sql_helper("""
            SELECT * from results_by_huc12 where scenario in (0, 7, 9)
            and huc_12 = '102300031504' and valid >= '2008-01-01'
            and valid < '2016-01-01' ORDER by valid ASC
            """),
            conn,
            index_col=None,
        )

    (fig, ax) = plt.subplots(1, 1)
    for scenario, label in zip(
        [0, 7, 9], ["Baseline", "UCS 4 Year", "UCS 3 Year"], strict=False
    ):
        df2 = df[df["scenario"] == scenario]
        x = []
        y = []
        accum = 0
        for _, row in df2.iterrows():
            x.append(row["valid"])
            accum += row["avg_loss"] * KG_M2_TO_TON_ACRE
            y.append(accum)
        ax.plot(x, y, label=label)

    ax.legend(loc="best")
    ax.set_title("Accumulated Soil Detachment for 102300031504")
    ax.set_ylabel("Soil Detachment [t/a]")
    ax.grid(True)
    fig.savefig("test.png")


if __name__ == "__main__":
    main()
