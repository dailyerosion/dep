"""Utility script to delete a flowpath from the database and on-disk"""
import sys
import os

from pyiem.util import get_dbconn


def do_delete(huc12, fpath, scenario):
    """Delete a flowpath from the database and on disk

    Args:
      huc12 (str): The HUC12 that contains the flowpath
      fpath (str): The flowpath within that HUC12 that needs removal
      scenario (str): The IDEP scenario to remove this flowpath from
    """
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()

    # Find the FID
    cursor.execute(
        """SELECT fid from flowpaths WHERE huc_12 = %s and
    fpath = %s and scenario = %s""",
        (huc12, fpath, scenario),
    )
    if cursor.rowcount == 0:
        print(
            "ERROR: Can't find FID for HUC12: %s FPATH: %s SCENARIO: %s"
            % (huc12, fpath, scenario)
        )
        return
    fid = cursor.fetchone()[0]
    # Delete flowpath points
    cursor.execute(
        """DELETE from flowpath_points where flowpath = %s
    and scenario = %s""",
        (fid, scenario),
    )
    # Delete flowpath
    cursor.execute(
        """DELETE from flowpaths where fid = %s
    and scenario = %s""",
        (fid, scenario),
    )

    # Remove some files
    for prefix in ["env", "error", "man", "prj", "run", "slp", "sol", "wb"]:
        fn = "/i/%s/%s/%s/%s/%s_%s.%s" % (
            scenario,
            prefix,
            huc12[:8],
            huc12[8:],
            huc12,
            fpath,
            prefix,
        )
        if os.path.isfile(fn):
            print("REMOVE  %s" % (fn,))
            os.unlink(fn)
        else:
            print("MISSING %s" % (fn,))

    cursor.close()
    pgconn.commit()


def main():
    """Go Main Go"""
    huc12 = sys.argv[1]
    fpath = sys.argv[2]
    scenario = sys.argv[3]
    do_delete(huc12, fpath, scenario)


if __name__ == "__main__":
    main()
