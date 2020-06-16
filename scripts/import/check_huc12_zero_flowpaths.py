"""Report which HUC12s have 0 flowpaths."""
import sys

from pyiem.util import get_dbconn
from pandas.io.sql import read_sql


def main(argv):
    """Go Main Go."""
    scenario = int(argv[1])
    huc12s = [s.strip() for s in open("myhucs.txt").readlines()]
    pgconn = get_dbconn("idep")
    df = read_sql(
        "SELECT huc_12, count(*) from flowpaths where scenario = %s "
        "GROUP by huc_12",
        pgconn,
        params=(scenario,),
        index_col="huc_12",
    )
    df = df.reindex(huc12s).fillna(0)
    print(df[df["count"] == 0].index.values)


if __name__ == "__main__":
    main(sys.argv)
