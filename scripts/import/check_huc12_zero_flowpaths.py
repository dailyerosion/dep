"""Report which HUC12s have 0 flowpaths."""

import sys

from pandas import read_sql
from pyiem.util import get_dbconnstr


def main(argv):
    """Go Main Go."""
    scenario = int(argv[1])
    huc12s = [s.strip() for s in open("myhucs.txt", encoding="utf8")]
    df = read_sql(
        "SELECT huc_12, count(*) from flowpaths where scenario = %s "
        "GROUP by huc_12",
        get_dbconnstr("idep"),
        params=(scenario,),
        index_col="huc_12",
    )
    df = df.reindex(huc12s).fillna(0)
    print(df[df["count"] == 0].index.values)


if __name__ == "__main__":
    main(sys.argv)
