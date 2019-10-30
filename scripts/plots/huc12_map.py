"""General HUC12 mapper"""
from __future__ import print_function

import datetime
import sys

import matplotlib

matplotlib.use("agg")
import matplotlib.pyplot as plt
from pyiem.plot import MapPlot, nwsprecip
from shapely.wkb import loads
import numpy as np
import cartopy.crs as ccrs
from matplotlib.patches import Polygon
import matplotlib.colors as mpcolors
from pyiem.util import get_dbconn

MYHUCS = [
    "071000060202",
    "071000060307",
    "070802051004",
    "070802051003",
    "070802051102",
    "070802050907",
    "070802051201",
    "070802051202",
    "070802050808",
    "070802050807",
    "070802090401",
    "070802090101",
    "070802090102",
    "070802090103",
    "070802090406",
    "070802090302",
    "070802090301",
]


def main(argv):
    """Do Great Things"""
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()

    mp = MapPlot(
        continentalcolor="#EEEEEE",
        nologo=True,
        # sector='custom',
        # south=36.8, north=45.0, west=-99.2, east=-88.9,
        subtitle="",
        title=("DEP MLRA identifier assignment using HUC12 Centroid"),
    )

    cursor.execute(
        """
    select st_transform(geom, 4326), mlra_id from huc12 where scenario = 0
    """
    )

    bins = [
        106,
        107,
        108,
        109,
        121,
        137,
        150,
        155,
        166,
        175,
        176,
        177,
        178,
        179,
        181,
        182,
        186,
        187,
        188,
        196,
        197,
        204,
        205,
    ]
    cmap = plt.get_cmap("terrain")
    cmap.set_under("white")
    cmap.set_over("black")
    norm = mpcolors.BoundaryNorm(bins, cmap.N)

    for row in cursor:
        for polygon in loads(row[0].decode("hex")):
            arr = np.asarray(polygon.exterior)
            points = mp.ax.projection.transform_points(
                ccrs.Geodetic(), arr[:, 0], arr[:, 1]
            )
            color = cmap(norm([float(row[1])]))[0]
            poly = Polygon(
                points[:, :2], fc=color, ec="None", zorder=2, lw=0.1
            )
            mp.ax.add_patch(poly)

    mp.draw_colorbar(bins, cmap, norm, units="MLRA ID")

    # mp.drawcounties()
    mp.postprocess(filename="test.png")


if __name__ == "__main__":
    main(sys.argv)
