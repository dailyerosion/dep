"""Plot a Q-Q plot of slopes."""

import glob
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyiem.util import utc

from pydep.io.wepp import read_slp


def read_data():
    """Do intensive stuff"""
    scenarios = []
    res = []
    peakslopes = []
    lengths = []
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
            os.chdir("/i/%s/slp/%s/%s" % (scenario, huc12[:8], huc12[8:]))
            for fn in glob.glob("*.slp"):
                slp = read_slp(fn)
                # The peak instantaneous slope
                maxval = 0
                for seg in slp:
                    maxval = max([maxval, np.max(seg["slopes"])])
                # The bulk slope
                bulk = (slp[-1]["y"][-1]) / slp[-1]["x"][-1]
                res.append((0 - bulk) * 100.0)
                scenarios.append(scenario)
                peakslopes.append(maxval * 100.0)
                lengths.append(slp[-1]["x"][-1])
                # check for sanity
                if (res[-1] - 0.01) > peakslopes[-1]:
                    print("max: %s bulk: %s" % (res[-1], peakslopes[-1]))
                    print(slp)
                    print(fn)
                    sys.exit(1)
    df = pd.DataFrame(
        {
            "slopes": res,
            "scenario": scenarios,
            "maxslope": peakslopes,
            "length": lengths,
        }
    )
    df.to_csv("/tmp/slopes.csv", index=False)


def main():
    """Go Main Go"""
    # huc12 = argv[1]
    read_data()
    fig, ax = plt.subplots(1, 1)
    df = pd.read_csv("/tmp/slopes.csv")
    for scenario, gdf in df.groupby("scenario"):
        print(gdf["length"].describe())
        gdf["length"].plot.hist(
            bins=500,
            cumulative=True,
            density=1,
            ax=ax,
            label="%s avg: %.1fm" % (scenario, gdf["length"].mean()),
            histtype="step",
        )
        # gdf["maxslope"].plot.hist(
        #    bins=500, cumulative=True, density=1, ax=ax,
        #    label="%s peak, avg: %.1f%%" % (scenario, gdf['maxslope'].mean()),
        #    histtype='step')
    ax.set_yticks(np.arange(0, 1.01, 0.1))
    ax.set_xlim(0, 375)
    ax.grid(True)
    ax.legend(loc=4, ncol=2)
    ax.set_title("Length Comparison between new and old flowpaths")
    ax.set_xlabel("Length (m), generated %s" % (utc().strftime("%d %b %Y"),))
    fig.savefig("/tmp/test.png")


if __name__ == "__main__":
    main()
