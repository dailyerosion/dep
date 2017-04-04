"""Delete all traces of a HUC12"""

import psycopg2
import sys
import os
import glob


def do_delete(huc12, scenario):
    pgconn = psycopg2.connect(database='idep', host='iemdb')
    cursor = pgconn.cursor()

    # Remove any flowpath points
    cursor.execute("""
    delete from flowpath_points pts using flowpaths f where
    pts.flowpath = f.fid and f.huc_12 = %s and f.scenario = %s
    """, (huc12, scenario))
    print("removed %s flowpath_points" % (cursor.rowcount, ))

    # Remove any flowpaths
    cursor.execute("""
    DELETE from flowpaths where huc_12 = %s and scenario = %s
    """, (huc12, scenario))
    print("removed %s flowpaths" % (cursor.rowcount, ))

    # remove any results
    cursor.execute("""
    DELETE from results_by_huc12 where huc_12 = %s and scenario = %s
    """, (huc12, scenario))
    print("removed %s results_by_huc12" % (cursor.rowcount, ))

    # Remove some files
    for prefix in ['env', 'error', 'man', 'prj', 'run', 'slp', 'sol', 'wb']:
        dirname = "/i/%s/%s/%s/%s" % (scenario, prefix, huc12[:8],
                                      huc12[8:])
        os.chdir(dirname)
        files = glob.glob("*.*")
        for fn in files:
            os.unlink(fn)
        os.rmdir(dirname)
        print("Removed %s files from %s" % (len(files), dirname))

    cursor.close()
    pgconn.commit()


def main():
    """Go Main Go"""
    huc12 = sys.argv[1]
    scenario = int(sys.argv[2])
    do_delete(huc12, scenario)


if __name__ == '__main__':
    main()
