"""Simulate what my algo is doing."""

from datetime import date

import click
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle
from pyiem.plot import figure

from dailyerosion.workflows.dyntillage import (
    do_planting,
    do_tillage,
    get_planting_fraction,
)


@click.command()
@click.option(
    "--workable", type=float, default=0.5, help="Fraction of workable days"
)
def main(workable: float):
    """Test things."""
    corn_fields = np.random.randint(1, 100)
    soybean_fields = 100 - corn_fields
    fields = pd.DataFrame(
        {
            "acres": np.ones(100) * 100,
            "crop": ["C"] * corn_fields + ["B"] * soybean_fields,
            "plant_needed": [True] * 100,
            "till_needed": [True] * 100,
            "till1": pd.to_datetime([date(2000, 7, 1)] * 100),
            "till2": pd.to_datetime([date(2000, 7, 1)] * 100),
            "till3": pd.to_datetime([date(2000, 7, 1)] * 100),
            "plant": pd.to_datetime([date(2000, 7, 1)] * 100),
            "operation_done": [False] * 100,
        },
    )
    # Randomize the field size between 20 and 100 acres
    fields["acres"] = np.random.randint(20, 100, size=100)

    # randomize the number of tillage events needed
    for idx in fields.index:
        events = np.random.randint(0, 4)
        if events == 0:
            fields.loc[idx, ("till1", "till2", "till3")] = pd.NaT
            fields.loc[idx, "till_needed"] = False
        elif events == 1:
            fields.loc[idx, ("till2", "till3")] = pd.NaT
        elif events == 2:
            fields.loc[idx, "till3"] = pd.NaT

    # Randomize the dataframe
    fields = fields.sample(frac=1).reset_index(drop=True)

    tottill = (
        fields["till1"].notna().sum()
        + fields["till2"].notna().sum()
        + fields["till3"].notna().sum()
    )
    total_acres = fields["acres"].sum()
    fig = figure(
        title="DEP Dynamic Tillage Simulator",
        subtitle=(
            f"100 Fld ({corn_fields} corn, {soybean_fields} soybeans), "
            f"{total_acres:.0f} acres, "
            f"{tottill} total tillage events, {workable:.0%} workable days"
        ),
        logo="dep",
        figsize=(10.72, 10.72),
    )
    dates = pd.date_range("2000/04/11", "2000/06/14")

    ax = fig.add_axes((0.1, 0.05, 0.45, 0.8))
    ax.set_xlim(-1, 101)
    ax.set_ylim(-1, len(dates))
    ax.text(
        101,
        len(dates) + 1,
        "Till PltCor PltSoy PltEff",
        fontdict={"family": "monospace"},
    )
    data = np.zeros((len(dates), 100))
    cmap = ListedColormap(
        [
            "r",  # wait tillage
            "brown",  # tilled
            "b",  # wait planted
            "g",  # planted today
            "tan",  # done
        ]
    )

    labelcolors = ["r"] * len(dates)
    for ypos, dt in enumerate(dates):
        print(f"Doing {dt:%Y-%m-%d}")
        # Update accounting
        fields["operation_done"] = False
        fields["plant_needed"] = fields["plant"] > pd.Timestamp(dt)
        fields["till_needed"] = (
            (fields["till1"] > pd.Timestamp(dt))
            | (fields["till2"] > pd.Timestamp(dt))
            | (fields["till3"] > pd.Timestamp(dt))
        )
        mud_it_in = f"{dt:%m%d}" >= "0611"
        cp = 0
        sp = 0
        tillage_acres = 0
        if np.random.random() < workable or mud_it_in:
            tillage_acres = do_tillage(fields, dt, mud_it_in, 0)
            do_planting(fields, dt, mud_it_in, 0)
            labelcolors[ypos] = "g"
        for idx, row in fields.iterrows():
            val = 0
            if row["plant"] <= pd.Timestamp(dt):
                val = 4
                if row["plant"] == pd.Timestamp(dt):
                    if row["crop"] == "C":
                        cp += row["acres"]
                    else:
                        sp += row["acres"]
                    val = 3
            elif row["operation_done"]:  # Must have been tilled today
                val = 1
            elif row["till_needed"]:
                val = 0
            elif row["plant_needed"]:
                val = 2
            data[ypos, idx] = val
        possible = (
            total_acres * get_planting_fraction()[dt.timetuple().tm_yday - 1]
        )
        eff = (cp + sp) / possible * 100.0
        label = f"{tillage_acres:4.0f}   {cp:4.0f}   {sp:4.0f}  {eff:3.1f}"

        ax.text(
            101,
            ypos,
            label,
            fontdict={"family": "monospace"},
            color=labelcolors[ypos],
        )

    ax.set_yticks(np.arange(0, len(dates)))
    labels = ax.set_yticklabels(
        [f"{dt:%b %-d}" for dt in dates],
    )
    for label, color in zip(labels, labelcolors, strict=True):
        label.set_color(color)
    ax.imshow(data, aspect="auto", cmap=cmap, origin="lower")
    ax.legend(
        [
            Rectangle((0, 0), 1, 1, fc=cmap.colors[0]),
            Rectangle((0, 0), 1, 1, fc=cmap.colors[1]),
            Rectangle((0, 0), 1, 1, fc=cmap.colors[2]),
            Rectangle((0, 0), 1, 1, fc=cmap.colors[3]),
            Rectangle((0, 0), 1, 1, fc=cmap.colors[4]),
        ],
        ["Tillage Needed", "Tilled", "Planting Needed", "Planted", "Done"],
        loc=(-0.1, 1.04),
        ncol=5,
    )
    ax.set_xlabel("Sequential Randomized Field")

    # Create the planting progress CDF
    ax2 = fig.add_axes((0.8, 0.6, 0.19, 0.15))
    for crop, label in zip(["C", "B"], ["Corn", "Soybeans"], strict=True):
        subset = fields[fields["crop"] == crop]
        planted = (
            subset[["plant", "acres"]].groupby("plant").sum().cumsum()
            / subset["acres"].sum()
            * 100.0
        )
        ax2.plot(
            planted.index,
            planted.values,
            label=label,
        )

    labeldates = [
        date(2000, 4, 15),
        date(2000, 5, 1),
        date(2000, 5, 15),
        date(2000, 6, 1),
        date(2000, 6, 15),
    ]

    ax2.set_xticks(labeldates)
    ax2.set_xticklabels([dt.strftime("%b\n%-d") for dt in labeldates])

    ax2.annotate(
        "Planting Progress",
        xy=(0, 1.2),
        xycoords="axes fraction",
        bbox=dict(boxstyle="round", fc="w"),
    )

    ax2.grid(True)
    ax2.legend(loc=(0, 1), ncol=2)

    fig.savefig("plots/simulation.png")


if __name__ == "__main__":
    main()
