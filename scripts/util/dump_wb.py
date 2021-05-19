"""Dump Daily Water Balance."""
import os
import glob

from pyiem.util import get_dbconn
from pyiem.dep import read_wb
from pandas.io.sql import read_sql
from tqdm import tqdm
import pandas as pd


def main():
    """Go Main Go."""
    df = read_sql(
        "SELECT distinct huc_12 from flowpaths where scenario = 0",
        get_dbconn("idep"),
        index_col=None,
    )
    with open("sm.csv", "w") as fh:
        fh.write("huc12,date,s10cm\n")
        progress = tqdm(df["huc_12"].values)
        for huc12 in progress:
            progress.set_description(huc12)
            mydir = "/i/0/wb/%s/%s" % (huc12[:8], huc12[8:])
            if not os.path.isdir(mydir):
                continue
            os.chdir(mydir)
            frames = []
            for fn in glob.glob("*.wb"):
                df = read_wb(fn)
                # Only worry about OFE1 for now
                df = df[df["ofe"] == 1]
                frames.append(df)
            if not frames:
                continue
            df = pd.concat(frames)
            gdf = df.groupby("date").mean()
            for year in range(2014, 2019):
                for day in pd.date_range(
                    f"{year}/04/01", f"{year}/07/01", closed="left"
                ):
                    fh.write("%s,%s,%.3f\n" % (huc12, day, gdf.at[day, "sw1"]))


if __name__ == "__main__":
    main()
