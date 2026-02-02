"""See what their data shows."""

from datetime import date, timedelta

import numpy as np
import pandas as pd
from pyiem.plot import figure_axes


def read_csvs() -> list[pd.DataFrame, pd.DataFrame]:
    """Load up the csvs."""
    corndf = pd.read_csv(
        "deines2023/deines2023_datum_corn.csv", parse_dates=["date"]
    )
    corndf["doy"] = corndf["date"].dt.day_of_year
    soybeansdf = pd.read_csv(
        "deines2023/deines2023_datum_soybeans.csv", parse_dates=["date"]
    )
    soybeansdf["doy"] = soybeansdf["date"].dt.day_of_year

    return corndf, soybeansdf


def explore_rates():
    """Figure out if we can tease out rates."""
    corndf, soybeansdf = read_csvs()

    for df, crop in zip(
        [corndf, soybeansdf], ["corn", "soybeans"], strict=True
    ):
        for datum in df["datum"].unique():
            vals = []
            for year in range(2000, 2021):
                ddf = df[(df["datum"] == datum) & (df["year"] == year)]
                totalacres = ddf["acres"].sum()
                maxval = (
                    ddf["acres"].rolling(7).sum() / totalacres
                ).max() * 100.0
                vals.append(maxval)
            ar = np.array(vals)
            print(
                f"{crop},{datum},{ar.min():.2f},{ar.mean():.2f},{ar.max():.2f}"
            )


def main():
    """Go Main Go."""
    corndf, soybeansdf = read_csvs()

    fig, ax = figure_axes(
        title=(
            "Deines 2023: Daily Soybean to (Soybean + Corn) "
            "Planting Percentage"
        ),
        logo=None,
        figsize=(8, 6),
    )
    for datum in ["IA", "MN", "KS", "NE"]:
        dcorn = corndf[corndf["datum"] == datum]

        dcornsum = dcorn[["acres", "doy"]].groupby("doy").sum().copy()

        dsoy = soybeansdf[soybeansdf["datum"] == datum]

        dsoy_sum = dsoy[["acres", "doy"]].groupby("doy").sum().copy()

        dsoy_sum["corn"] = dcornsum["acres"]
        dsoy_sum["pct"] = (
            dsoy_sum["acres"] / (dsoy_sum["corn"] + dsoy_sum["acres"]) * 100.0
        )

        ax.plot(
            dsoy_sum.index.to_numpy(),
            dsoy_sum["pct"],
            lw=3 if len(datum) == 2 else 1,
            label=datum,
        )

    # dyntillv5 algo
    x = np.arange(110, 117)
    y = np.zeros(x.shape)
    x = np.concatenate((x, np.arange(117, 125)))
    y = np.concatenate((y, np.linspace(0, 10, 8)))
    x = np.concatenate((x, np.arange(124, 137)))
    y = np.concatenate((y, np.linspace(10, 80, 13)))
    x = np.concatenate((x, np.arange(136, 161)))
    y = np.concatenate((y, np.linspace(80, 100, 25)))

    ax.plot(x, y, lw=2, color="k", linestyle=":", label="DEP DynTillv5")

    ax.legend()
    ax.grid(True)
    xlim = ax.get_xlim()
    xticks = []
    xticklabels = []
    for x in range(int(xlim[0]), int(xlim[1])):
        dt = date(2000, 1, 1) + timedelta(days=x - 1)
        if dt.day in [1, 8, 15, 22]:
            xticks.append(x)
            xticklabels.append(f"{dt:%-d %b}\n({x})")

    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels)

    ax.set_ylabel("Percentage of Daily Acres Planted to Soybeans")
    ax.set_yticks([0, 5, 10, 25, 50, 75, 90, 95, 100])
    ax.set_xlabel("Approximate Date for (Day of Year)")
    fig.savefig("plots/ratio.png")


if __name__ == "__main__":
    explore_rates()
