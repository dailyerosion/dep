"""Create a map of where we have climate files!"""

import glob
import os

import cartopy.crs as ccrs
from pyiem.plot import MapPlot


def update_grid(ax):
    """Plot vals."""
    os.chdir("/i/0/cli")
    lons = []
    lats = []
    for mydir in glob.glob("*"):
        os.chdir(mydir)
        for fn in glob.glob("*.cli"):
            tokens = fn[:-4].split("x")
            lons.append(0 - float(tokens[0]))
            lats.append(float(tokens[1]))
        os.chdir("..")
    ax.scatter(
        lons,
        lats,
        transform=ccrs.PlateCarree(),
        zorder=1000,
        marker="+",
        color="r",
    )


def draw_map():
    """make maps, not war."""
    m = MapPlot(sector="conus", title="4 March 2019 :: DEP Precip Points")
    update_grid(m.ax)
    m.postprocess(filename="/tmp/map_clipoints.png")
    m.close()


def main():
    """Go Main Go."""
    draw_map()


if __name__ == "__main__":
    main()
