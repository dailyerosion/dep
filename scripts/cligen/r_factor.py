"""R factor work."""

from pyiem.util import get_sqlalchemy_conn
from pyiem.plot.use_agg import plt
from pyiem.plot import MapPlot
import cartopy.crs as ccrs
import matplotlib.colors as mpcolors
from matplotlib.patches import Polygon
import numpy as np
from tqdm import tqdm
import geopandas as gpd
import pandas as pd
from pydep.io.wepp import read_cli


def plot():
    """Plot."""
    df2 = pd.read_csv("/tmp/data.csv", dtype={"huc12": str}).set_index("huc12")
    with get_sqlalchemy_conn("idep") as conn:
        df = gpd.read_postgis(
            "SELECT huc_12, ST_Transform(simple_geom, 4326) as geom "
            "from huc12 WHERE scenario = 0",
            conn,
            geom_col="geom",
            index_col="huc_12",
        )
    minx, miny, maxx, maxy = df["geom"].total_bounds
    colname = "rfactor_yr_avg"
    df2[colname] = df2[colname] * 0.05876
    desc = df2[colname].describe()
    buffer = 0.1
    mp = MapPlot(
        title="DEP 2007-2021 Average R Factor Yearly Total by HUC12",
        subtitle=(
            f"Min: {desc['min']:.1f} Mean: {desc['mean']:.1f} "
            f"Max: {desc['max']:.1f}, based on daily R factor"
        ),
        axisbg="#EEEEEE",
        logo="dep",
        sector="custom",
        south=miny - buffer,
        north=maxy + buffer,
        west=minx - buffer,
        east=maxx + buffer,
        projection=ccrs.PlateCarree(),
        caption="Daily Erosion Project",
    )
    cmap = plt.get_cmap("turbo")
    clevs = np.arange(0, 300.1, 25.0)
    # clevs = np.arange(0, 6000.1, 1000.0)
    # clevs = np.arange(2007, 2020.1, 1)
    norm = mpcolors.BoundaryNorm(clevs, cmap.N)
    for huc_12, row in df.iterrows():
        val = df2.at[huc_12, colname]
        c = cmap(norm([val]))[0]
        p = Polygon(row["geom"].exterior.coords, fc=c, ec=c, zorder=2, lw=0.1)
        mp.ax.add_patch(p)
    mp.draw_colorbar(
        clevs,
        cmap,
        norm,
        extend="neither",
        units="hundred ft tonf inches per acre per hour",
    )
    mp.fig.savefig("test.png")


def dump_data():
    """Go main Go."""
    with get_sqlalchemy_conn("idep") as conn:
        df = pd.read_sql(
            """
            SELECT huc_12, max(climate_file) as cli from flowpaths where
            scenario = 0 GROUP by huc_12
        """,
            conn,
            index_col="huc_12",
        )
    data = {
        "huc12": [],
        "rfactor_yr_avg": [],
        "rfactor_yr_max": [],
        "rfactor_yr_min": [],
        "rfactor_min_year": [],
        "rfactor_max_year": [],
    }
    for year in range(2007, 2022):
        data[f"rfactor_{year}"] = []
    for huc_12, row in tqdm(df.iterrows(), total=len(df.index)):
        fn = row["cli"].replace("/i/", "/mnt/idep2/2/")
        cdf = read_cli(fn, compute_rfactor=True)
        data["huc12"].append(huc_12)
        # drop 2020
        yearly = cdf["rfactor"].groupby(cdf.index.year).sum().iloc[:-1]
        data["rfactor_yr_avg"].append(yearly.mean())
        data["rfactor_yr_min"].append(yearly.min())
        data["rfactor_yr_max"].append(yearly.max())
        data["rfactor_min_year"].append(yearly.idxmin())
        data["rfactor_max_year"].append(yearly.idxmax())
        for year in range(2007, 2022):
            data[f"rfactor_{year}"].append(yearly.loc[year])

    df = pd.DataFrame(data)
    df.to_csv("/tmp/data.csv", index=False)


if __name__ == "__main__":
    # dump_data()
    plot()
