"""Make sure our database has things right with climate_file."""

import sys

from pydep.util import get_cli_fname
from pyiem.util import get_dbconn, logger

LOG = logger()


def main(argv):
    """Go Main Go."""
    scenario = int(argv[1])
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()
    cursor2 = pgconn.cursor()
    # Get the climate_scenario
    cursor.execute(
        "SELECT climate_scenario from scenarios where id = %s", (scenario,)
    )
    clscenario = cursor.fetchone()[0]
    cursor.execute(
        """
        SELECT st_x(st_pointn(st_transform(geom, 4326), 1)),
        st_y(st_pointn(st_transform(geom, 4326), 1)), fid, climate_file
        from flowpaths WHERE scenario = %s
    """,
        (scenario,),
    )
    ok = wrong = updated = 0
    for row in cursor:
        fn = get_cli_fname(row[0], row[1], clscenario)
        if row[3] == fn:
            ok += 1
            continue
        if row[3] is not None and row[3] != fn:
            wrong += 1
        cursor2.execute(
            "UPDATE flowpaths SET climate_file = %s where fid = %s",
            (fn, row[2]),
        )
        updated += 1
    LOG.info(
        "%s rows updated: %s ok: %s wrong: %s",
        cursor.rowcount,
        updated,
        ok,
        wrong,
    )
    cursor2.close()
    pgconn.commit()


if __name__ == "__main__":
    main(sys.argv)
