"""Utility script that copies neighboring clifiles when it is discovered
that we need new ones!"""
import psycopg2
import os
import sys
import shutil


def missing_logic(scenario, fn):
    """Figure out what to do when this filename is missing"""
    print("Searching for replacement for '%s'" % (fn,))
    lon = float(fn[17:23])
    lat = float(fn[24:30])
    for xoff in [0, -1, 1, -2, 2, -3, 3]:
        for yoff in [0, -1, 1, -2, 2, -3, 3]:
            lon2 = lon + xoff / 100.0
            lat2 = lat + yoff / 100.0
            testfn = ("/i/%s/cli/%03.0fx%03.0f/%06.2fx%06.2f.cli"
                      ) % (scenario, lon2, lat2, lon2, lat2)
            if not os.path.isfile(testfn):
                continue
            print("%s->%s" % (testfn, fn))
            shutil.copyfile(testfn, fn)
            return
    print("--> failure for %s" % (fn,))


def main(argv):
    """Go Main Go!"""
    scenario = argv[1]
    pgconn = psycopg2.connect(database='idep', host='iemdb', user='nobody')
    cursor = pgconn.cursor()
    cursor.execute("""
        SELECT climate_file from flowpaths where scenario = %s
    """, (scenario, ))
    for row in cursor:
        fn = "/i/%s/%s" % (scenario, row[0])
        if os.path.isfile(fn):
            continue
        missing_logic(scenario, fn)

if __name__ == '__main__':
    main(sys.argv)
