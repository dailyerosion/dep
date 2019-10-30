"""Assign a MLRA_ID to the huc12 table"""
from __future__ import print_function
from pyiem.util import get_dbconn


def main():
    """Go Main Go"""
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()
    cursor.execute(
        """
    update huc12  SET mlra_id = m.mlra_id FROM mlra m
    WHERE ST_Contains(m.geom, st_transform(ST_CEntroid(huc12.geom), 4326))
    and huc12.mlra_id is null
    """
    )
    print("Updated %s rows" % (cursor.rowcount,))
    cursor.close()
    pgconn.commit()
    pgconn.close()


if __name__ == "__main__":
    main()
