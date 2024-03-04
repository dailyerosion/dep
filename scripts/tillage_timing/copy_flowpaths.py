"""Too complicated to do this right."""

import sys

from pandas.io.sql import read_sql
from pyiem.util import get_dbconn, logger

LOG = logger()


def main(argv):
    """Run for a scenario."""
    scenario = int(argv[1])
    myhucs = [s.strip() for s in open("myhucs.txt")]
    # Get df of flowpaths
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()
    df = read_sql(
        """
        SELECT fid, huc_12, fpath from flowpaths
        where scenario = 0 and huc_12 in %s
    """,
        pgconn,
        params=(tuple(myhucs),),
        index_col="fid",
    )
    LOG.info(
        "found %s flowpaths for copying to scenario %s",
        len(df.index),
        scenario,
    )
    # copy back into flowpath database and then copy points over
    newrows = 0
    for fid, _row in df.iterrows():
        cursor.execute(
            """
            INSERT into flowpaths(huc_12, fpath, geom, scenario, climate_file)
            select huc_12, fpath, geom, %s, climate_file from flowpaths
            where scenario = 0 and fid = %s RETURNING fid
        """,
            (scenario, fid),
        )
        newfid = cursor.fetchone()[0]
        # copy flowpath_points over and replace flowpath + scenario column
        cursor.execute(
            """
            INSERT into flowpath_points
            SELECT %s, segid, elevation, length, surgo, management, slope,
            lu2007, lu2008, lu2009, lu2010, lu2011, lu2012, geom, %s,
            gridorder, landuse, management
            from flowpath_points where scenario = 0 and flowpath = %s
        """,
            (newfid, scenario, fid),
        )
        newrows += cursor.rowcount

    LOG.info("Added %s rows to flowpath_points", newrows)
    cursor.close()
    pgconn.commit()


if __name__ == "__main__":
    main(sys.argv)
