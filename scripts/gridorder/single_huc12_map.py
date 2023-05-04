"""Map a HUC12"""
import sys

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import psycopg2
from cartopy.io.img_tiles import GoogleTiles
from geopandas import read_postgis


class ShadedReliefESRI(GoogleTiles):
    # shaded relief
    def _image_url(self, tile):
        x, y, z = tile
        url = (
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "ESRI_Imagery_World_2D/MapServer/tile/{z}/{y}/{x}.jpg"
        ).format(z=z, y=y, x=x)
        return url


def main(argv):
    """Go Main"""
    huc12 = argv[1]
    pgconn = psycopg2.connect(database="idep")
    df = read_postgis(
        """
    SELECT ST_Transform(geom, 4326) as geo from huc12
    where scenario = 0 and huc_12 = %s
    """,
        pgconn,
        params=(huc12,),
        geom_col="geo",
    )
    row = df.iloc[0]

    (fig, ax) = plt.subplots(
        1,
        1,
        figsize=(10.24, 7.68),
        subplot_kw=dict(projection=ShadedReliefESRI().crs),
    )
    padding = 0.01
    for poly in row["geo"]:
        bnds = poly.bounds
        ax.set_extent(
            [
                bnds[0] - padding,
                bnds[2] + padding,
                bnds[1] - padding,
                bnds[3] + padding,
            ]
        )
        ax.add_geometries(
            [poly], ccrs.PlateCarree(), edgecolor="k", facecolor="None", lw=2
        )

    df = read_postgis(
        """
    SELECT ST_Transform(geom, 4326) as geo, fpath from flowpaths
    where scenario = 0
    and huc_12 = %s
    """,
        pgconn,
        params=(huc12,),
        geom_col="geo",
        index_col="fpath",
    )
    for fpath, row in df.iterrows():
        points = row["geo"].xy
        ax.plot(
            points[0],
            points[1],
            color="k",
            lw=2.0,
            transform=ccrs.PlateCarree(),
        )
    # ax.add_image(GoogleTiles(), 4)
    print(ax.get_extent())
    fig.savefig("test.png")


if __name__ == "__main__":
    main(sys.argv)
