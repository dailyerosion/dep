"""Dumper for the Dataset 1 request.

MLRA
plant date
sm @ plating
annual detach for year
annual precip for year
Year
Period ID
5 day period middle date
5 day precip total
5 day sm
5 day detach

- This would be one file per planting date (scenarios 59 through 69)
- 2008 thru 2018
"""
import datetime
import glob

from pyiem.util import logger
import pandas as pd
from pydep.io.wepp import read_env
from pydep.io.dep import read_wb

LOG = logger()


def do_scenario(scenario, plantdate, hucdf):
    """Process this scenario."""
    index = pd.MultiIndex.from_product(
        [range(2008, 2019), range(1, 74)], names=["year", "period"]
    )
    df = pd.DataFrame(index=index).reset_index()

    def f(row):
        """Make date."""
        return datetime.date(row["year"], 1, 1) + datetime.timedelta(
            days=int(row["period"] - 1) * 5 + 2
        )

    df["5day_middle_date"] = df.apply(f, axis=1)
    df = df.set_index(["year", "period"])

    smdfs = []
    flowpaths = 0
    for _, row in hucdf.iterrows():
        huc12 = row["HUC12"]
        for fn in glob.glob(
            "/i/%s/wb/%s/%s/*" % (scenario, huc12[:8], huc12[8:])
        ):
            smdfs.append(read_wb(fn))
            flowpaths += 1
    smdf = pd.concat(smdfs)
    del smdfs

    envdfs = []
    for _, row in hucdf.iterrows():
        huc12 = row["HUC12"]
        for fn in glob.glob(
            "/i/%s/env/%s/%s/*" % (scenario, huc12[:8], huc12[8:])
        ):
            envdfs.append(read_env(fn))
    envdf = pd.concat(envdfs)
    envdf["jday"] = pd.to_numeric(
        envdf["date"].dt.strftime("%j"), downcast="integer"
    )
    del envdfs

    # only one ofe 1
    smdf = smdf[smdf["ofe"] == 1]
    smdf["period"] = (smdf["jday"] + 5) // 5
    envdf["period"] = (envdf["jday"] + 5) // 5
    # only consider 2008 thru 2018 data
    smdf = smdf[(smdf["year"] > 2007) & (smdf["year"] < 2019)]
    envdf = envdf[(envdf["year"] > 2007) & (envdf["year"] < 2019)]

    gdf = envdf.groupby(["year", "period"]).mean()
    df["5day_precip_mm"] = gdf["precip"]
    df["5day_detach_kgm2"] = gdf["av_det"]

    gdf = smdf.groupby(["year", "period"]).mean()
    df["5day_soilmoist"] = gdf["sw1"]

    gdf = envdf.groupby("year").sum() / flowpaths
    df = df.join(gdf[["precip", "av_det"]])
    df = df.rename(
        {"precip": "annual_precip_mm", "av_det": "annual_detach_kgm2"}, axis=1
    )

    gdf = (
        smdf[smdf["jday"] == int(plantdate.strftime("%j"))]
        .groupby("year")
        .mean()
    )
    df = df.join(gdf["sw1"])
    df = df.rename({"sw1": "plant_soilmoist"}, axis=1)
    df["plant_date"] = plantdate.strftime("%m %d")
    df["mlra_id"] = hucdf.iloc[0]["MLRA"]
    df = df.fillna(0)
    LOG.info("done with %s %s", plantdate, hucdf.iloc[0]["MLRA"])
    return df


def main():
    """Go Main Go."""
    apr10 = datetime.date(2000, 4, 10)
    mlradf = pd.read_csv(
        "myhucs_mlra.txt",
        sep=r"\s?\|\s?",
        dtype={"HUC12": str},
        skipinitialspace=True,
        engine="python",
    )
    for scenario in range(59, 70):
        plantdate = apr10 + datetime.timedelta(days=(scenario - 59) * 5)
        dfs = []
        for _, hucdf in mlradf.groupby("MLRA"):
            dfs.append(do_scenario(scenario, plantdate, hucdf))
        df = pd.concat(dfs)
        df.to_csv(
            "dataset1_%s.csv" % (plantdate.strftime("%b%d"),),
            float_format="%.4f",
        )


if __name__ == "__main__":
    main()
