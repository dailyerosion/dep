"""A plot of the deltas for erosion between scenarios."""
import os

from pyiem.dep import read_env
from pyiem.plot.use_agg import plt
from tqdm import tqdm
import numpy as np


def plot():
    """Plot."""
    y = [...]
    y = np.array(y)
    fig, ax = plt.subplots(1, 1)
    ax.set_title(
        "DEP Additional Springtime 1 inch/hr Storms (2007-2020)\n"
        "30 HUC12 Averaged Change [%] over Baseline"
    )
    ax.bar(np.arange(1, 11), y * 100.0)
    for i, val in enumerate(y):
        ax.text(i + 1, val * 100.0 + 1, f"{val * 100.:.1f}%", ha="center")
    ax.set_xlabel("Additional 1 inch/hr Storms per Spring Season per Year")
    ax.set_ylim(0, 110)
    ax.set_ylabel("Change in Detachment over Baseline [%]")
    ax.grid(True)
    fig.savefig("test.png")


def main():
    """Go Main Go."""
    hucs = open("myhucs.txt").read().split("\n")
    scenarios = [0]
    scenarios.extend(list(range(130, 140)))
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
    print(deltas)


if __name__ == "__main__":
    # main()
    plot()
