"""Generate DEP for a custom datum."""
from calendar import month_abbr

from pyiem.dep import read_env
from pyiem.util import get_dbconn
from geopandas import read_file
import pandas as pd
from pandas.io.sql import read_sql
from tqdm import tqdm


def main():
    """Go Main Go."""
    dbconn = get_dbconn("idep")
    # Load custom shapefile
    gpd = read_file("/tmp/Catchment_headwaters_w_LK.shp")
    result = []
    for _, row in tqdm(gpd.iterrows(), total=len(gpd.index)):
        # Find flowpaths intersecting the shape bounds
        df = read_sql(
            "SELECT huc_12, fpath, ST_Length(geom) as len from flowpaths "
            "where scenario = 0 and ST_Intersects(geom, "
            "ST_Transform(ST_SetSRID(ST_GeomFromEWKT(%s), 26915), 5070))",
            dbconn,
            params=(row["geometry"].wkt,),
            index_col=None,
        )
        if df.empty:
            continue
        res = {"fpcount": len(df.index), "CATCH_ID": row["CATCH_ID"]}
        # Read all the envs, include row count
        envs = []
        for _, fp in df.iterrows():
            envfn = (
                f"/i/0/env/{fp['huc_12'][:8]}/{fp['huc_12'][8:]}/"
                f"{fp['huc_12']}_{fp['fpath']}.env"
            )
            envdf = read_env(envfn)
            envdf["key"] = f"{fp['huc_12']}_{fp['fpath']}"
            envdf["delivery"] = envdf["sed_del"] / fp["len"]
            envs.append(envdf)
        envdf = pd.concat(envs)
        envdf["month"] = envdf["date"].dt.month
        # HUC 12 Annual Soils Loss, Precipitation and RunOff for 2008-2019
        genvdf = envdf.groupby(by=["key", "year"]).sum().groupby("year").mean()
        for year in range(2017, 2021):
            ydf = genvdf.loc[year]
            for col in ["delivery", "precip", "runoff"]:
                res[f"{col}_{year}"] = float(ydf[col])
            envy = envdf[envdf["year"] == year]
            genv = (
                envy.groupby(by=["key", "month"]).sum().groupby("month").mean()
            )
            # 1, 2, 3 inch events
            counts = [[0] * 13, [0] * 13, [0] * 13]
            for i, level in enumerate([25, 50, 75]):
                for dt in envy.loc[envy["precip"] >= level]["date"].unique():
                    counts[i][pd.to_datetime(dt).month] += 1
            for month in range(1, 13):
                label = month_abbr[month].lower()
                for i, level in enumerate([25, 50, 75]):
                    res[f"{level}mmdays_{year}_{label}"] = counts[i][month]
                if month not in genv.index.values:
                    continue
                mdf = genv.loc[month]
                for col in ["delivery", "precip", "runoff"]:
                    res[f"{col}_{year}_{label}"] = float(mdf[col])
        result.append(res)

    # Dump out
    df = pd.DataFrame(result)
    df = df.fillna(0)
    df.to_csv("dep_data.csv", index=False, float_format="%.4f")


if __name__ == "__main__":
    main()
