"""Tease out some differences."""
import glob

from tqdm import tqdm
import numpy as np
from pyiem.plot.use_agg import plt
import pandas as pd
from pydep.io.wepp import read_env

MYHUCS = [
    "070600060701",
    "070801020905",
    "101702040703",
    "070600020602",
    "071000090201",
    "102300020202",
    "102300060407",
    "071000091101",
    "101702032003",
    "071000081503",
    "102300031404",
    "070801021001",
    "101702031903",
    "071000070402",
    "102400030501",
    "070600040401",
    "102300030402",
    "070802050304",
    "070801060604",
    "071000061401",
    "102802010402",
    "102400090404",
    "070802070602",
    "071000050703",
    "070802090401",
    "102400050501",
    "070802060403",
]


def main():
    """Go Main Go."""
    fig, ax = plt.subplots(1, 1)

    for huc12 in tqdm(MYHUCS):
        dfs = []

        for scenario in [0, 1002]:
            for fn in glob.glob(
                "/i/%s/env/%s/%s/*.env" % (scenario, huc12[:8], huc12[8:])
            ):
                fpath = int(fn.split("/")[-1].split(".")[0].split("_")[1])
                df = read_env(fn)
                df["fpath"] = fpath
                df["av_det"] = df["av_det"] * 4.463
                df["scenario"] = scenario
                dfs.append(df)
        df = pd.concat(dfs)
        df["year"] = df["date"].dt.year
        gdf = (
            df[["year", "scenario", "fpath", "av_det"]]
            .groupby(["year", "scenario", "fpath"])
            .sum()
        )
        gdf = gdf.reset_index()
        ptiles = np.arange(95, 100.01, 0.1)
        pc1 = np.percentile(gdf[gdf["scenario"] == 0]["av_det"].values, ptiles)
        pc2 = np.percentile(
            gdf[gdf["scenario"] == 1002]["av_det"].values, ptiles
        )
        ax.plot(pc1, pc2)
        ax.scatter(pc1[-1], pc2[-1], s=40, marker="s", color="b", zorder=3)
    ax.grid(True)
    ax.set_title(
        "95th Percentile and Higher Yearly Soil Delivery\n"
        "Max value shown by dot"
    )
    ax.set_xlabel("Production Yearly Soil Delivery T/a")
    ax.set_ylabel("New Flowpaths Yearly Soil Delivery T/a")
    ymax = max([ax.get_xlim()[1], ax.get_ylim()[1]])
    ax.plot([0, ymax], [0, ymax], color="k", lw=2, label="x=y")
    fig.savefig("/tmp/test.png")


if __name__ == "__main__":
    main()
