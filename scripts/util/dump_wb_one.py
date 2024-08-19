"""Dump Water Balance for Dr Wang
070802070603 2016-2018 March-June
"""

import glob
import os

import pandas as pd

from pydep.io.dep import read_wb


def main():
    """Go Main Go."""
    os.chdir("/i/0/wb/07080207/0603")
    frames = []
    for fn in glob.glob("*.wb"):
        df = read_wb(fn)
        # Only worry about OFE1 for now
        df = df[df["ofe"] == 1]
        frames.append(df)
    df = pd.concat(frames)
    rows = []
    for year in range(2016, 2021):
        for day in pd.date_range(
            f"{year}/03/01", f"{year}/12/01", closed="left"
        ):
            row = df[df["date"] == day].mean()
            row["date"] = day
            rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv("/tmp/test.csv")


if __name__ == "__main__":
    main()
