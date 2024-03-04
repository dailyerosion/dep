"""
Utility to plot some residue values from WEPP crop output
"""

import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

COLS = [
    "canopy_height_m",
    "canopy_cover_%",
    "LAI",
    "cover_rill_%",
    "cover_inter_%",
    "live_biomass_type",
    "live_biomass",
    "standing_residue_mass",
    "flat_residue_mass1_type",
    "flat_residue_mass1",
    "flat_residue_mass2_type",
    "flat_residue_mass2",
    "flat_residue_mass3_type",
    "flat_residue_mass3",
    "barried_residue_mass1",
    "barried_residue_mass2",
    "barried_residue_mass3",
    "deadroot_residue_mass1_type",
    "deadroot_residue_mass1",
    "deadroot_residue_mass2_type",
    "deadroot_residue_mass2",
    "deadroot_residue_mass3_type",
    "deadroot_residue_mass3",
    "average_temp_c",
]


def myread(filename):
    """Read my file,  please"""
    rows = []
    for i, line in enumerate(open(filename)):
        if i < 13:
            continue
        tokens = line.strip().split()
        if len(tokens) < 9:
            continue
        date = datetime.date(int(tokens[2]), 1, 1)
        date = date + datetime.timedelta(days=(int(tokens[1]) - 1))
        mydict = dict(date=date)
        for j in range(3, 3 + len(COLS)):
            mydict[COLS[j - 3]] = float(tokens[i])
        rows.append(mydict)

    return pd.DataFrame(rows)


def main():
    """Go Main Go"""
    df22 = myread("18_102400120405_9.crop")
    # df23 = myread('23_102400120405_9.crop')
    df24 = myread("24_102400120405_9.crop")

    for plotvar in COLS:
        print("Processing %s" % (plotvar,))
        (fig, axes) = plt.subplots(1, 1, figsize=(12, 6))
        axes.plot(df22["date"], df22[plotvar], label="CC No Cover NoTill")
        # axes.plot(df23['date'], df23['inter'], label='CS Cover NoTill')
        axes.plot(df24["date"], df24[plotvar], label="CC Cover NoTill")
        axes.grid(True)
        axes.set_ylabel(plotvar)
        axes.legend(ncol=2)
        axes.set_title(
            (
                "CSCAP Scenario Comparison for HUC12: "
                "102400120405 HS: 9"
                "\n'%s' Plotted"
            )
            % (plotvar,)
        )
        axes.xaxis.set_major_locator(mdates.YearLocator(1))

        fig.savefig("%s.png" % (plotvar,))
        plt.close()


if __name__ == "__main__":
    main()
