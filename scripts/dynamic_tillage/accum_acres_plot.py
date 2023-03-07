"""Plot accumulated acres diagnostic."""

import pandas as pd
from pyiem.plot import figure_axes
from pyiem.util import get_sqlalchemy_conn


def main():
    """Go Main Go."""
    fig, ax = figure_axes(
        logo="dep",
        title="DEP 102300070305 2007-2022 Accumulated Plant Completion",
    )

    with get_sqlalchemy_conn("idep") as conn:
        df = pd.read_sql(
            """
            select f.acres, o.year, o.plant,
            plant - (o.year || '-03-01')::date as doy
            from fields f JOIN field_operations o
            on (f.field_id = o.field_id) WHERE f.huc12 = '102300070305'
            ORDER by plant asc
            """,
            conn,
            parse_dates=["plant"],
        )
    for year in range(2007, 2023):
        df2 = (
            df[df["year"] == year]
            .groupby("doy")
            .sum(numeric_only=True)
            .cumsum()
        )
        ax.plot(
            df2.index.values,
            df2["acres"] / df2["acres"].max() * 100.0,
            label=f"{year}",
        )

    xticks = []
    xticklabels = []
    for dt in pd.date_range("2000/04/15", "2000/06/05"):
        x = (dt - pd.Timestamp(f"{dt.year}/03/01")).days
        if dt.day in [1, 8, 15, 22]:
            xticks.append(x)
            xticklabels.append(f"{dt:%-d %b}")
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels)
    ax.grid()
    ax.set_ylabel("Acres Planted [%]")
    ax.set_yticks([0, 5, 10, 25, 50, 75, 90, 95, 100])
    ax.legend(loc=4, ncol=3)
    fig.savefig("test.png")


if __name__ == "__main__":
    main()
