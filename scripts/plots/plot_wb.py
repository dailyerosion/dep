"""Diagnose some Water Balance stuff"""
from __future__ import print_function
import sys
import calendar

from pyiem.dep import read_wb
import matplotlib.pyplot as plt


def main(argv):
    """Do things"""
    filename = argv[1]
    wb = read_wb(filename)

    (fig, ax) = plt.subplots(2, 1)
    ax[0].set_title("Water Balance for %s" % (filename.split("/")[-1], ))
    ax[0].plot(wb['date'], wb['sw'])
    ax[0].set_ylabel("Total Soil Water [mm]")
    ax[0].grid(True)

    for year in [2009, 2012, 2015]:
        df2 = wb[wb['year'] == year]
        ax[1].plot(df2['jday'], df2['sw'], label=str(year))
    ax[1].legend(ncol=10)
    ax[1].set_xticks((1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305,
                      335, 365))
    ax[1].set_xticklabels(calendar.month_abbr[1:])
    ax[1].grid(True)
    ax[1].set_ylabel("Total Soil Water [mm]")

    fig.savefig('test.png')


if __name__ == '__main__':
    main(sys.argv)
