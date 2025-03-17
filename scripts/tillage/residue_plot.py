"""KDE Ridge plot of residue data"""

import os

import pandas as pd
import seaborn as sns
from pyiem.database import get_sqlalchemy_conn, sql_helper
from pyiem.plot import figure_axes


def magic(df, prefix):
    """Do magic"""
    return (
        df[
            [
                f"{prefix}2017",
                f"{prefix}2018",
                f"{prefix}2019",
                f"{prefix}2020",
                f"{prefix}2021",
                f"{prefix}2022",
            ]
        ]
        .rename(columns=lambda x: x.replace(prefix, ""))
        .reset_index()
        .melt(
            id_vars=["field_id"],
            var_name="year",
            value_name=prefix,
            value_vars=[
                "2017",
                "2018",
                "2019",
                "2020",
                "2021",
                "2022",
            ],
        )
        .set_index(["field_id", "year"])
    )


def curate():
    """Make feather file."""
    with get_sqlalchemy_conn("idep") as conn:
        residues = pd.read_sql(
            sql_helper("""
                select field_id, residue2017, residue2018, residue2019,
                residue2020, residue2021, residue2022,
                substr(man_2017_2022, 1, 1) as man2017,
                substr(man_2017_2022, 2, 1) as man2018,
                substr(man_2017_2022, 3, 1) as man2019,
                substr(man_2017_2022, 4, 1) as man2020,
                substr(man_2017_2022, 5, 1) as man2021,
                substr(man_2017_2022, 6, 1) as man2022,
                substr(landuse, 11, 1) as landuse2017,
                substr(landuse, 12, 1) as landuse2018,
                substr(landuse, 13, 1) as landuse2019,
                substr(landuse, 14, 1) as landuse2020,
                substr(landuse, 15, 1) as landuse2021,
                substr(landuse, 16, 1) as landuse2022,
                null as prevlanduse2017,
                substr(landuse, 11, 1) as prevlanduse2018,
                substr(landuse, 12, 1) as prevlanduse2019,
                substr(landuse, 13, 1) as prevlanduse2020,
                substr(landuse, 14, 1) as prevlanduse2021,
                substr(landuse, 15, 1) as prevlanduse2022,
                substr(management, 11, 1) as management2017,
                substr(management, 12, 1) as management2018,
                substr(management, 13, 1) as management2019,
                substr(management, 14, 1) as management2020,
                substr(management, 15, 1) as management2021,
                substr(management, 16, 1) as management2022
                from fields where scenario = 0
            """),
            conn,
            index_col="field_id",
        )
    # This dataframe has three sets of yearly columns, we want this in long
    # format with a row for each year and then the three column values
    fields = magic(residues, "residue")
    fields["man"] = magic(residues, "man")["man"].astype(int)
    fields["landuse"] = magic(residues, "landuse")["landuse"]
    fields["prevlanduse"] = magic(residues, "prevlanduse")["prevlanduse"]
    fields["management"] = magic(residues, "management")["management"]
    fields = fields.reset_index()
    fields["year"] = fields["year"].astype(int)
    fields.to_feather("residue.feather")


def plot_assignment(fields):
    """"""
    fig, ax = figure_axes(
        title="DEP Tillage Code Assignment after Corn with Residue",
        logo="dep",
        figsize=(8, 6),
    )
    sns.set_theme(style="dark")

    sns.boxenplot(
        data=fields,
        x="man",
        y="residue",
        hue="landuse",
        palette={"C": "g", "B": "r"},
        ax=ax,
    )

    ax.set_xlabel("Assigned Tillage Code")
    ax.set_ylabel("Residue Cover [%]")
    ax.set_yticks(range(0, 101, 10))
    ax.grid(True)

    fig.savefig("test.png")


def main():
    """Go Main."""
    if not os.path.isfile("residue.feather"):
        curate()
    fields = pd.read_feather("residue.feather")
    fields = fields[
        (fields["prevlanduse"].isin(["C", "B"]))
        & (fields["landuse"].isin(["C", "B"]) & (fields["residue"] >= 0))
    ]
    fig, ax = figure_axes(
        title=(
            "2017-2022 Distribution of Residue Cover Estimate after Given Crop"
        ),
        logo="dep",
        figsize=(8, 6),
    )

    sns.despine(fig)

    sns.histplot(
        fields,
        x="residue",
        hue="prevlanduse",
        element="step",
        bins=100,
    )
    ax.grid(True)

    fig.savefig("test.png")


if __name__ == "__main__":
    main()
