"""Diagnose some Water Balance stuff"""

import sys

import pandas as pd
import seaborn as sns
from pyiem.util import get_dbconnstr

from pydep.io.dep import read_wb


def main(argv):
    """Do things"""
    obs = pd.read_sql(
        "SELECT day, snowd from alldata_mn where station = 'MN2142' "
        "and year >= 2007 and year < 2022 ORDER by day ASC",
        get_dbconnstr("coop"),
        index_col="day",
    )
    df = read_wb(argv[1])
    # just care about OFE 1 for now
    df = df[df["ofe"] == 1].set_index("date")

    df["obs"] = obs["snowd"] * 25.4
    df["delta"] = df["snodpy"] - df["obs"]

    g = sns.lmplot(x="snodpy", y="obs", data=df)
    g.ax.set_title("Detroit Lakes 2007-2021 vs 090201030701 FP:32")
    g.ax.set_ylabel("Snow Depth Obs (mm)")
    g.ax.set_xlabel("Snow Depth WEPP (mm)")
    df = df[pd.notnull(df["obs"])]
    b = df["snodpy"].mean() - df["obs"].mean()
    g.ax.text(0.05, 0.8, f"bias:{b:.3f}mm", transform=g.ax.transAxes)
    g.fig.subplots_adjust(top=0.95)
    g.fig.savefig("test.png")


if __name__ == "__main__":
    main(sys.argv)
