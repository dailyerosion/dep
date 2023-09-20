"""Update the database storage to add another value."""
import sys

from pyiem.util import get_dbconn, logger

LOG = logger()


def main(argv):
    """Go Main Go."""
    newyear = int(argv[1])
    length_to_fix = int(newyear - 2007)
    LOG.info("For %s fixing length of %s", newyear, length_to_fix)
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()
    cursor.execute(
        """
        UPDATE flowpath_ofes SET
        landuse = landuse || substr(landuse, %s, 1),
        management = management || substr(management, %s, 1)
        where length(landuse) = %s
        """,
        (length_to_fix - 1, length_to_fix - 1, length_to_fix),
    )
    LOG.info("%s updated %s rows", newyear, cursor.rowcount)
    cursor.close()
    pgconn.commit()


if __name__ == "__main__":
    main(sys.argv)
