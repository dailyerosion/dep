"""Plot a histogram of slopes used in DEP"""

import glob
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pydep.io.wepp import read_slp


def read_data():
    """Do intensive stuff"""
    os.chdir("/i/0/slp")
    res = []
    for huc8 in glob.glob("*"):
        os.chdir(huc8)
        for huc12 in glob.glob("*"):
            os.chdir(huc12)
            for fn in glob.glob("*.slp"):
                slp = read_slp(fn)
                bulk = (slp[-1]["y"][-1]) / slp[-1]["x"][-1]
                if bulk < -1:
                    print("Greater than 100%% slope, %s %s" % (fn, bulk))
                    continue
                res.append((0 - bulk) * 100.0)
            os.chdir("..")
        os.chdir("..")
    df = pd.DataFrame({"slopes": res})
    df.to_csv("/tmp/slopes.csv", index=False)


def main():
    """Go Main Go"""
    read_data()
    fig, ax = plt.subplots(1, 1)
    df = pd.read_csv("/tmp/slopes.csv")
    df["slopes"].plot.hist(bins=100, cumulative=True, normed=1, ax=ax)
    ax.set_yticks(np.arange(0, 1.01, 0.1))
    ax.set_xlim(0, 30)
    ax.grid(True)
    ax.set_title("21 Dec 2017 DEP Bulk Slope Histogram")
    ax.set_xlabel("Slope %")
    fig.savefig("test.png")


if __name__ == "__main__":
    main()
