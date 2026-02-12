import glob
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LogNorm

from dailyerosion.reference import KG_M2_TO_TON_ACRE

GRIDORDER = sys.argv[1]


def summarize():
    """Placeholder."""
    res = []
    for fn in glob.glob("dfs/*.csv"):
        df = pd.read_csv(fn)
        sdf = df.groupby("flowpath").sum() / 10.0
        adf = df[["flowpath", "length"]].groupby("flowpath").mean()
        for fp, row in sdf.iterrows():
            length = adf.at[fp, "length"]
            res.append(
                dict(
                    flowpath=fp,
                    length=length,
                    avg_det=(row["av_det"] * KG_M2_TO_TON_ACRE),
                    runoff=row["runoff"],
                    delivery=(row["delivery"] * KG_M2_TO_TON_ACRE),
                )
            )

    df = pd.DataFrame(res)
    df.to_csv("flowpaths%s.csv" % (GRIDORDER,))


def plot1(df):
    """Placeholder."""
    (fig, ax) = plt.subplots(1, 1)
    plt.hist2d(df["length"], df["avg_det"], bins=[160, 320], norm=LogNorm())
    plt.colorbar(label="Flowpaths")
    ax.set_ylabel("Soil Detachment [T/a per year]")
    ax.set_xlabel("Flowpath Length [m]")
    ax.set_xlim(0, 400)
    ax.set_ylim(0, 50)

    df["ilength"] = (df["length"] / 5.0).astype("i")
    gdf = df.groupby("ilength").mean()
    ax.plot(
        gdf.index.values * 5.0,
        gdf["avg_det"].values,
        lw=2,
        color="k",
        label="Avg",
        zorder=5,
    )
    ax.plot(
        gdf.index.values * 5.0,
        gdf["avg_det"].values,
        lw=4,
        color="w",
        zorder=4,
    )
    ax.grid(True)
    ax.set_title("Iowa DEP:: Yearly Avg Detachment by Flowpath Length")
    ax.legend()
    fig.savefig("test.png")


def main():
    """Placeholder."""
    df = pd.read_csv("flowpaths%s.csv" % (GRIDORDER,))
    x = []
    y = []
    y2 = []
    for i in np.arange(0, 50, 0.5):
        x.append(i)
        y.append(df[df["length"] >= i]["delivery"].mean())
        y2.append(df[df["length"] >= i]["avg_det"].mean())
    (fig, ax) = plt.subplots(1, 1)
    ax.plot(x, y, label="Delivery")
    ax.plot(x, y2, label="Detachment")
    ax.set_xlabel(
        "Flowpath Length Floor [m], (average computed for len >= floor)"
    )
    ax.set_title("Iowa DEP: Yearly Averages by Truncated Flowpath Length")
    ax.legend(loc="best")
    ax.grid(True)
    ax.set_ylabel("Soil Delivery or Detachment [T/a per year]")
    fig.savefig("test.png")


if __name__ == "__main__":
    summarize()
