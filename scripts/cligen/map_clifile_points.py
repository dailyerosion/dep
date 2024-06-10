"""Create a map of where we have climate files!"""

import glob
import os
from typing import List, Tuple

from pyiem.plot import MapPlot
from pyiem.reference import Z_OVERLAY
from tqdm import tqdm


def get_points() -> Tuple[List[float], List[float]]:
    """Plot vals."""
    os.chdir("/i/0/cli")
    lons = []
    lats = []
    for mydir in tqdm(glob.glob("*")):
        os.chdir(mydir)
        for fn in glob.glob("*.cli"):
            tokens = fn[:-4].split("x")
            lons.append(0 - float(tokens[0]))
            lats.append(float(tokens[1]))
        os.chdir("..")
    return lons, lats


def main():
    """make maps, not war."""
    lons, lats = get_points()
    mp = MapPlot(
        logo="dep",
        sector="conus",
        title="7 June 2024 :: DEP Daily Updated Climate File Locations",
        subtitle=f"Total Climate Files: {len(lons)}",
        caption="Daily Erosion Project",
    )
    # All points will overwhelm matplotlib, so we need to plot them in chunks
    for i in tqdm(range(0, len(lons), 1000)):
        mp.panels[0].scatter(
            lons[i : i + 1000],
            lats[i : i + 1000],
            c="r",
            s=0.1,
            zorder=Z_OVERLAY,
        ).set_rasterized(True)
    mp.fig.savefig("map_clipoints.png")


if __name__ == "__main__":
    main()
