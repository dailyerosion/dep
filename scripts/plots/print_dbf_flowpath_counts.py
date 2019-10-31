"""
Print out what the initial flowpath counts where 
"""
import dbflib
import os
import glob
import pandas as pd
from pandas import Series


def get_data(fn):
    """ Load a DBF file into a pandas DF """
    rows = []
    dbf = dbflib.open(fn)
    for i in range(dbf.record_count()):
        rows.append(dbf.read_record(i))

    return pd.DataFrame(rows)


def main():
    """ Lets go main go """
    os.chdir("../../data/dbfsGo4")
    fns = glob.glob("*.dbf")
    for fn in fns:
        huc12 = fn[4:-4]
        huc8 = huc12[:-4]
        df = get_data(fn)
        flowpaths = Series(df["g4%s" % (huc8,)]).unique()


if __name__ == "__main__":
    main()
