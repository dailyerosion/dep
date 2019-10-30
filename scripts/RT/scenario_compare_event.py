"""Compare scenarios."""
import os
import glob
import datetime

import pandas as pd
from pyiem.plot.use_agg import plt
from pyiem.dep import read_env


def main():
    """Go Main Go."""
    os.chdir("/i/0/env/10230003/1504")
    baseline = {}
    for fn in glob.glob("*.env"):
        fpath = fn.split(".")[0].split("_")[1]
        df = read_env(fn)
        row = df[df["date"] == pd.Timestamp(year=2014, month=6, day=15)]
        baseline[fpath] = row.iloc[0]["sed_del"]

    os.chdir("/i/1000/env/10230003/1504")
    scenario = {}
    for fn in glob.glob("*.env"):
        fpath = fn.split(".")[0].split("_")[1]
        df = read_env(fn)
        row = df[df["date"] == pd.Timestamp(year=2014, month=6, day=15)]
        scenario[fpath] = row.iloc[0]["sed_del"]

    df = pd.DataFrame(
        {"baseline": pd.Series(baseline), "scenario": pd.Series(scenario)}
    )
    df["diff"] = df["scenario"] - df["baseline"]
    print(df.sort_values("diff", ascending=False).head(1))
    df2 = df[pd.isnull(df["diff"])]
    print(df2)

    (fig, ax) = plt.subplots(1, 1)
    ax.plot([0, 10000], [0, 10000], lw=2, color="r")
    ax.set_xlabel("Baseline avg: %.2f" % (df["baseline"].mean(),))
    ax.set_ylabel("Previous avg: %.2f" % (df["scenario"].mean(),))
    # keep this from impacting above
    df = df.fillna(0)
    ax.scatter(df["baseline"].values, df["scenario"].values)
    ax.set_title("15 Jun 2014 :: HUC12: 102300031504, raw sed_del")
    fig.savefig("/tmp/test.png")


if __name__ == "__main__":
    main()
