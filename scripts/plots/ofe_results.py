"""Some exploritory OFE based results"""
from __future__ import print_function
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def rotclass(val):
    """Convert this rotation string into a classification"""
    # if we have seven years of either corn and soy
    if val.count("B") + val.count("C") > 6:
        return "A"
    return "N"


def main():
    """Go Main Go"""
    dfin = pd.read_csv('results.csv', dtype={'huc12':'str'})
    # Filter data to only include slopes < 0.5 and delivery values < 20 T/a/yr
    df = dfin[(dfin['slope[1]'] < 0.5) &
              (dfin['delivery[t/a/yr]'] < 20)].copy()
    # classify rotation
    df['rotclass'] = df['CropRotationString'].apply(rotclass)
    bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5]
    df['slpclass'] = np.searchsorted(bins, df['slope[1]'].values)
    ax = sns.factorplot(kind='box',        # Boxplot
                         y='delivery[t/a/yr]',
                         x='slpclass',
                         hue='rotclass',
                         data=df,
                         size=8,
                         aspect=1.5,
                         legend_out=False)
    ax.set_xticklabels(["%s-%s" % (bins[i], bins[i+1])
                        for i in range(len(bins)-1)])
    # sns.jointplot(x='slope[1]', y='delivery[t/a/yr]', data=df, kind='reg')
    plt.savefig('test.png')


if __name__ == '__main__':
    main()
