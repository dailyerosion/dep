"""Some exploritory OFE based results"""

# third party
import pandas as pd
import numpy as np
import seaborn as sns
from pyiem.plot.use_agg import plt


def rotclass(val):
    """Convert this rotation string into a classification"""
    # if we have seven years of either corn and soy
    if val.count("B") + val.count("C") > 6:
        return "Ag"
    return "Non Ag"


def main():
    """Go Main Go"""
    dfin = pd.read_csv("results.csv", dtype={"huc12": "str"})
    # Filter data to only include slopes < 0.5 and delivery values < 20 T/a/yr
    df = dfin[
        (dfin["slope[1]"] < 0.5) & (dfin["delivery[t/a/yr]"] < 20)
    ].copy()
    # classify rotation
    df["rotclass"] = df["CropRotationString"].apply(rotclass)
    bins = [0, 0.01, 0.02, 0.05, 0.09, 0.14, 0.5]
    df["slpclass"] = np.searchsorted(bins, df["slope[1]"].values)
    ax = sns.violinplot(
        y="delivery[t/a/yr]",
        x="slpclass",
        hue="rotclass",
        data=df,
        legend=False,
    )
    plt.legend(loc=2)
    ax.set_ylim(bottom=0)
    ax.set_xticklabels(
        ["%s-%s" % (bins[i], bins[i + 1]) for i in range(len(bins) - 1)]
    )
    ax.grid(True)
    ax.set_title("2008-2020 DEP OFE Soil Delivery by Crop Rotation Class")
    # sns.jointplot(
    # hue='rotclass',
    #    x='slope[1]', y='delivery[t/a/yr]', data=df, kind='reg')
    plt.savefig("test.png")


if __name__ == "__main__":
    main()
