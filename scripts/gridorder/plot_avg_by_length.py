import matplotlib.pyplot as plt
import pandas as pd
from pandas.io.sql import read_sql
from pyiem.database import get_dbconn


def old():
    """Placeholder."""
    (fig, ax) = plt.subplots(1, 1)
    ax.grid(True)
    for gridorder in range(1, 7):
        df = pd.read_csv("flowpaths%s.csv" % (gridorder,))
        df["ilength"] = df["length"].astype("i") / 5
        gdf = df.groupby("ilength").mean()
        ax.plot(
            gdf.index.values * 5,
            gdf["delivery"],
            label="G%s" % (gridorder,),
            lw=2,
        )

    ax.set_xlim(0, 200)
    ax.set_ylim(0, 25)
    ax.legend(loc=2)
    ax.set_xlabel("Flowpath Length, (5m bin averages)")
    ax.set_title("Average Soil Delivery by Flowpath Length + Grid Order")
    ax.set_ylabel("Soil Delivery [t/a per year]")
    ax.set_xticks([0, 25, 50, 75, 100, 150, 200])
    fig.savefig("test.png")


def main():
    """Placeholder."""
    pgconn = get_dbconn("wepp")
    dfv1 = read_sql(
        """
    SELECT id,  len * 0.3048 as length from nri
    """,
        pgconn,
        index_col="id",
    )
    (fig, ax) = plt.subplots(1, 1)
    ax.grid(True)
    for gridorder in range(1, 7):
        df = pd.read_csv("flowpaths%s.csv" % (gridorder,))
        ax.hist(
            df["length"],
            bins=100,
            range=[0, 400],
            label="G%s" % (gridorder,),
            cumulative=True,
            histtype="step",
            normed=True,
        )
    ax.hist(
        dfv1["length"],
        bins=100,
        range=[0, 400],
        label="IDEPv1",
        cumulative=True,
        histtype="step",
        normed=True,
        lw=3,
    )

    ax.set_xlim(0, 400)
    ax.legend(loc=4)
    ax.set_ylim(0, 1)
    ax.set_yticks([0, 0.1, 0.25, 0.5, 0.75, 0.9, 1])
    ax.set_xlabel("Flowpath Length")
    ax.set_title("Distribution of Flowpath Lengths by Grid Order")
    ax.set_ylabel("Normalized Accumulated Frequency")
    ax.set_xticks([0, 25, 50, 75, 100, 150, 200, 300, 400])
    fig.savefig("test.png")


if __name__ == "__main__":
    main()
