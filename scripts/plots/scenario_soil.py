"""Plot soil stuff."""
import glob
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyiem.util import utc


def read_data():
    """Do intensive stuff"""
    scenarios = []
    kr = []
    for huc12 in [
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
    ]:
        for scenario in [0, 1002]:
            os.chdir("/i/%s/sol/%s/%s" % (scenario, huc12[:8], huc12[8:]))
            for fn in glob.glob("*.sol"):
                lines = open(fn).readlines()
                # this fails sometimes
                kr.append(float(lines[3].split()[-3]))
                if kr[-1] > 0.1:
                    print(kr[-1])
                    print(
                        "/i/%s/sol/%s/%s/%s"
                        % (scenario, huc12[:8], huc12[8:], fn)
                    )
                scenarios.append(scenario)
    df = pd.DataFrame({"kr": kr, "scenario": scenarios})
    df.to_csv("/tmp/soils.csv", index=False)


def main():
    """Go Main Go"""
    # huc12 = argv[1]
    read_data()
    fig, ax = plt.subplots(1, 1)
    df = pd.read_csv("/tmp/soils.csv")
    for scenario, gdf in df.groupby("scenario"):
        print(gdf["kr"].describe())
        gdf["kr"].plot.hist(
            bins=500,
            cumulative=True,
            density=1,
            ax=ax,
            label="%s avg: %.4f" % (scenario, gdf["kr"].mean()),
            histtype="step",
        )
        # gdf["maxslope"].plot.hist(
        #    bins=500, cumulative=True, density=1, ax=ax,
        #    label="%s peak, avg: %.1f%%" % (scenario, gdf['maxslope'].mean()),
        #    histtype='step')
    ax.set_yticks(np.arange(0, 1.01, 0.1))
    ax.set_xlim(0, 0.012)
    ax.grid(True)
    ax.legend(loc=4, ncol=2)
    ax.set_title("Length Comparison between new and old flowpaths")
    ax.set_xlabel("Length (m), generated %s" % (utc().strftime("%d %b %Y"),))
    fig.savefig("/tmp/test.png")


if __name__ == "__main__":
    main()
