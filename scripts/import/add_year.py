"""Update the database storage to add another value."""

from pyiem.util import get_dbconn, logger

LOG = logger()


def main():
    """Go Main Go."""
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()
    cursor.execute(
        "UPDATE flowpath_points SET "
        "landuse = landuse || substr(landuse, 13, 1), "
        "management = management || substr(management, 13, 1) "
        "where length(landuse) = 14"
    )
    LOG.info("updated %s rows", cursor.rowcount)
    cursor.close()
    pgconn.commit()


if __name__ == "__main__":
    main()
