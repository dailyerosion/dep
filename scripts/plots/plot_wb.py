"""Diagnose some Water Balance stuff"""
from __future__ import print_function
import sys
import glob
import datetime

from tqdm import tqdm
import pandas as pd
import seaborn as sns
from pyiem.plot.use_agg import plt
from pyiem.dep import read_wb


def main(argv):
    """Do things"""
    dfs = []
    for fn in glob.glob("/i/0/wb/07100004/0704/*"):
        df = read_wb(fn)
        df["fpath"] = int(fn.split("_")[1][:-3])
        dfs.append(df)
    df = pd.concat(dfs)
    ranges = df.groupby(["fpath", "ofe"]).describe()
    year = 2018
    for doy in tqdm(range(1, 365)):
        date = datetime.date(year, 1, 1) + datetime.timedelta(days=(doy - 1))
        wb = df[(df["year"] == year) & (df["jday"] == doy)].copy()
        wb = wb.set_index(["fpath", "ofe"])
        for f2 in ["sw1", "sw2", "sw"]:
            for f1 in ["min", "max"]:
                wb["%s_%s" % (f2, f1)] = ranges[f2, f1]
            wb["%s_range" % (f2,)] = (
                wb["%s_max" % (f2,)] - wb["%s_min" % (f2,)]
            )
            wb["%s_percent" % (f2,)] = (
                (wb[f2] - wb["%s_min" % (f2,)])
                / wb["%s_range" % (f2,)]
                * 100.0
            )

        sns.set(style="white", palette="muted", color_codes=True)
        (fig, ax) = plt.subplots(3, 2, figsize=(7, 7))
        sns.despine(left=True)
        fig.text(
            0.5,
            0.98,
            "%s :: Water Balance for 071000040704"
            % (date.strftime("%d %B %Y"),),
            ha="center",
        )

        # ---------------------------------------------------
        myax = ax[0, 0]
        sns.distplot(wb["sw1"], hist=False, color="g", ax=myax, rug=True)
        myax.set_xlabel("0-10cm Soil Water [mm]")
        myax.axvline(wb["sw1"].mean(), color="r")
        myax.set_xlim(0, 60)

        myax = ax[0, 1]
        sns.distplot(
            wb["sw1_percent"], hist=False, color="g", ax=myax, rug=True
        )
        myax.set_xlabel("0-10cm Soil Water of Capacity [%]")
        myax.axvline(wb["sw1_percent"].mean(), color="r")
        myax.set_xlim(0, 100)

        # ---------------------------------------------------------
        myax = ax[1, 0]
        sns.distplot(wb["sw2"], hist=False, color="g", ax=myax, rug=True)
        myax.set_xlabel("10-20cm Soil Water [mm]")
        myax.axvline(wb["sw2"].mean(), color="r")
        myax.set_xlim(0, 60)

        myax = ax[1, 1]
        sns.distplot(
            wb["sw2_percent"], hist=False, color="g", ax=myax, rug=True
        )
        myax.set_xlabel("10-20cm Soil Water of Capacity [%]")
        myax.axvline(wb["sw2_percent"].mean(), color="r")
        myax.set_xlim(0, 100)

        # -------------------------------------------------------
        myax = ax[2, 0]
        sns.distplot(wb["sw"], hist=False, color="g", ax=myax, rug=True)
        myax.set_xlabel("Total Soil Water [mm]")
        myax.axvline(wb["sw"].mean(), color="r")
        myax.set_xlim(150, 650)

        myax = ax[2, 1]
        sns.distplot(
            wb["sw_percent"], hist=False, color="g", ax=myax, rug=True
        )
        myax.set_xlabel("Total Soil Water of Capacity [%]")
        myax.axvline(wb["sw_percent"].mean(), color="r")
        myax.set_xlim(0, 100)

        plt.setp(ax, yticks=[])
        plt.tight_layout()
        fig.savefig("frames/%05i.png" % (doy - 1,))
        plt.close()


if __name__ == "__main__":
    main(sys.argv)
