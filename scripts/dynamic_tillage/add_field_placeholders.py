"""
Add field placeholders since we don't have all the data yet.

see dailyerosion/dep#167
"""

import pandas as pd
from pyiem.util import get_dbconn, get_sqlalchemy_conn, logger
from tqdm import tqdm

LOG = logger()


def do_huc12(cursor, huc12, _area) -> int:
    """Create the faked fields, if necessary."""
    # fields fields
    # scenario check
    # huc12 check
    # fbndid check
    # acres make life choices
    # isag unsure
    # geom ST_Empty
    # landuse OFEs has this
    # management OFEs has this
    cursor.execute(
        """
        WITH data as (
            SELECT o.fbndid, o.management, o.landuse
            from flowpath_ofes o, flowpaths p
            WHERE o.flowpath = p.fid and p.huc_12 = %s and p.scenario = 0
        ), agg as (
            SELECT d.fbndid, d.management, d.landuse, f.field_id
            from data d LEFT JOIN fields f on
            d.fbndid = f.fbndid and f.huc12 = %s and f.scenario = 0
        )
        INSERT into fields(scenario, huc12, fbndid, acres, isag, geom,
        landuse, management) select 0, %s, fbndid, 40, 't', null,
        landuse, management from agg where field_id is null
        """,
        (huc12, huc12, huc12),
    )
    return cursor.rowcount


def main():
    """Go main go."""
    with get_sqlalchemy_conn("idep") as conn:
        df = pd.read_sql(
            """
            SELECT huc_12, st_area(st_transform(simple_geom, 4326)) as area
            from huc12 where scenario = 0
            """,
            conn,
            index_col="huc_12",
        )
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()
    newfields = 0
    for huc12, row in tqdm(df.iterrows(), total=len(df.index)):
        newfields += do_huc12(cursor, huc12, row["area"])
    LOG.info("Created %s new fields", newfields)
    cursor.close()
    pgconn.commit()


if __name__ == "__main__":
    main()
