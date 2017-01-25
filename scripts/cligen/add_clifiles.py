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
    if not os.path.isdir(os.path.dirname(fn)):
        os.makedirs(os.path.dirname(fn))
    # So there should be a file at an interval of 0.25
    lon2 = lon - (lon * 100 % 25) / 100.
    lat2 = lat - (lat * 100 % 25) / 100.
    testfn = ("/i/%s/cli/%03.0fx%03.0f/%06.2fx%06.2f.cli"
              ) % (scenario, lon2, lat2, lon2, lat2)
    if not os.path.isfile(testfn):
        print("Whoa, why doesn't %s exist?" % (testfn,))
        sys.exit()
    print("%s->%s" % (testfn, fn))
    shutil.copyfile(testfn, fn)


def main(argv):
    """Go Main Go!"""
    scenario = argv[1]
    pgconn = psycopg2.connect(database='idep', host='iemdb', user='nobody')
    cursor = pgconn.cursor()
    cursor.execute("""
        SELECT distinct climate_file from flowpaths where scenario = %s
        and climate_file is not null
    """, (scenario, ))
    for row in cursor:
        fn = "/i/%s/%s" % (scenario, row[0])
        if os.path.isfile(fn):
            continue
        missing_logic(scenario, fn)

if __name__ == '__main__':
    main(sys.argv)
