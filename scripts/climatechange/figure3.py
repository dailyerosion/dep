"""A plot of the deltas for erosion between scenarios."""
import os
import sys

from pyiem.dep import read_env
from pyiem.plot.use_agg import plt
from pyiem.util import logger, get_dbconn
from tqdm import tqdm
import numpy as np

LOG = logger()

DATA = [
    0.07532299938501776,
    0.15766216345170533,
    0.24007253103022136,
    0.3350761437226657,
    0.42331557042071166,
    0.53209366910133,
    0.6315990841977428,
    0.7482604383664925,
    0.8539429154383379,
    0.9631476509401304,
]


def main():
    """Plot."""
    fig, ax = plt.subplots(1, 1)
    ax.set_title(
        "Iowa DEP Future Precipitation Scenarios\n"
        "Change in Hill Slope Delivery[%] with Additional 25 mm/hr Events"
    )
    y = np.array(DATA) * 100.0
    ax.bar(np.arange(1, 11), y)
    for i, val in enumerate(y):
        ax.text(i + 1, val + 1, f"{val:.1f}%", ha="center")
    ax.set_xlabel("Additional 25 mm/hr Storms per Spring Season per Year")
    ax.set_ylim(0, 110)
    ax.set_ylabel("Change in Detachment over Baseline [%]")
    ax.grid(True)
    fig.savefig("test.png")


if __name__ == "__main__":
    main()
