"""Dump OFE metadata."""

import pandas as pd
from pyiem.database import get_sqlalchemy_conn, sql_helper
from pyiem.util import logger

LOG = logger()
# 2007 is skipped
YEARS = 6.0


def main():
    """Do the computations for the flowpath."""
    with get_sqlalchemy_conn("idep") as conn:
        meta = pd.read_sql(
            sql_helper("""
                select huc_12, fpath as flowpath, ofe,
                st_x(st_pointn(st_transform(o.geom, 4326), 1)) as lon,
                st_y(st_pointn(st_transform(o.geom, 4326), 1)) as lat,
                o.bulk_slope,
                o.max_slope,
                landuse, management,
                mukey as surgo24,
                kwfact, hydrogroup, fbndid,
                o.real_length as length, groupid
                from flowpath_ofes o JOIN flowpaths f on
                (o.flowpath = f.fid)
                JOIN gssurgo g on (o.gssurgo_id = g.id)
                WHERe f.scenario = 0
            """),
            conn,
        )
    meta.to_csv(
        "flowpath_ofe_meta.csv",
        index=False,
    )


if __name__ == "__main__":
    main()
