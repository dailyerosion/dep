"""A plot of the deltas for erosion between scenarios."""
import datetime
import sys
import os

from pyiem.dep import read_env
from pyiem.plot.use_agg import plt
from tqdm import tqdm
import numpy as np


def plot():
    """Plot."""
    y = [...]
    fig, ax = plt.subplots(1, 1)
    ax.set_title(
        "DEP +/- 14 Day Shift in Weather (2007-2020)\n"
        "30 HUC12 Averaged Change [%] over Baseline"
    )
    ax.bar(np.arange(-14, 15), np.array(y) * 100.0)
    ax.set_xlabel("Shift in Days (negative is earlier)")
    ax.set_ylim(-12, 12)
    ax.set_ylabel("Change in Detachment over Baseline [%]")
    ax.grid(True)
    fig.savefig("test.png")


def main():
    """Go Main Go."""
    hucs = open("myhucs.txt").read().split("\n")
    scenarios = [0]
    scenarios.extend(list(range(102, 130)))
    deltas = []
    baseline = None
    for scenario in tqdm(scenarios):
        vals = []
        for huc12 in hucs:
            mydir = f"/i/{scenario}/env/{huc12[:8]}/{huc12[8:]}"
            data = []
            for fn in os.listdir(mydir):
                res = read_env(os.path.join(mydir, fn)).set_index("date")
                data.append(res["av_det"].sum())
            vals.append(np.average(data))
        if scenario > 0:
            deltas.append((np.average(vals) - baseline) / baseline)
        else:
            baseline = np.average(vals)


if __name__ == "__main__":
    # main()
    plot()
