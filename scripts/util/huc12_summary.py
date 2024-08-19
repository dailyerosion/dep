"""Generate DEP summary."""

from calendar import month_abbr

import pandas as pd
from pandas.io.sql import read_sql
from pyiem.util import get_dbconn
from tqdm import tqdm

from pydep.io.wepp import read_env


def main():
    """Go Main Go."""
    dbconn = get_dbconn("idep")
    gpd = read_sql(
        "SELECT huc_12 from huc12 where states ~* 'MN' and scenario = 0",
        dbconn,
        index_col=None,
    )
    result = []
    for _, row in tqdm(gpd.iterrows(), total=len(gpd.index)):
        # Find flowpaths intersecting the shape bounds
        df = read_sql(
            "SELECT fpath, ST_Length(geom) as len from flowpaths "
            "where scenario = 0 and huc_12 = %s",
            dbconn,
            params=(row["huc_12"],),
            index_col=None,
        )
        if df.empty:
            continue
        res = {"fpcount": len(df.index), "HUC_12": row["huc_12"]}
        # Read all the envs, include row count
        envs = []
        for _, fp in df.iterrows():
            envfn = (
                f"/i/0/env/{row['huc_12'][:8]}/{row['huc_12'][8:]}/"
                f"{row['huc_12']}_{fp['fpath']:.0f}.env"
            )
            envdf = read_env(envfn)
            envdf["key"] = f"{row['huc_12']}_{fp['fpath']}"
            envdf["delivery"] = envdf["sed_del"] / fp["len"]
            envs.append(envdf)
        envdf = pd.concat(envs)
        envdf["month"] = envdf["date"].dt.month
        # HUC 12 Annual Soils Loss, Precipitation and RunOff for 2008-2019
        genvdf = envdf.groupby(by=["key", "year"]).sum().groupby("year").mean()
        for year in range(2008, 2020):
            ydf = genvdf.loc[year]
            for col in ["delivery", "precip", "runoff"]:
                res[f"{col}_{year}"] = float(ydf[col])
        # HUC 12 and headwater lake catchments monthly Soils Loss,
        # Precipitation and RunOff for 2019
        env2019 = envdf[envdf["year"] == 2019]
        genv2019 = (
            env2019.groupby(by=["key", "month"]).sum().groupby("month").mean()
        )
        for month in range(1, 13):
            if month not in genv2019.index.values:
                continue
            mdf = genv2019.loc[month]
            label = month_abbr[month].lower()
            for col in ["delivery", "precip", "runoff"]:
                res[f"{col}_{year}_{label}"] = float(mdf[col])
        result.append(res)

    # Dump out
    df = pd.DataFrame(result)
    df = df.fillna(0)
    df.to_csv("dep_huc12_data.csv", index=False, float_format="%.4f")


if __name__ == "__main__":
    main()
