"""Dump Daily Water Balance."""
import os
import glob

import pandas as pd
from pydep.io.dep import read_wb


def main():
    """Go Main Go."""
    huc12s = [
        "071000081505",
    ]
    with open("sm.csv", "w", encoding="ascii") as fh:
        fh.write("huc12,date,s10cm\n")
        for huc12 in huc12s:
            mydir = f"/i/0/wb/{huc12[:8]}/{huc12[8:]}"
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
            for day in pd.date_range(
                "2008/01/01", "2022/01/01", inclusive="left"
            ):
                fh.write(f"{huc12},{day:%Y-%m-%d},{gdf.at[day, 'sw1']:.3f}\n")


if __name__ == "__main__":
    main()
