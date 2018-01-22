#!/usr/bin/env python
import cgi
import sys
import json

from pyiem.util import get_dbconn


def search(q):
    """Search for q"""
    pgconn = get_dbconn('idep')
    cursor = pgconn.cursor()
    d = dict(results=[])
    cursor.execute("""SELECT huc_12, hu_12_name from huc12
    WHERE hu_12_name ~* %s and scenario = 0 LIMIT 10""", (q,))
    for row in cursor:
        d['results'].append(dict(huc_12=row[0], name=row[1]))

    return d


def main():
    """DO Something"""
    form = cgi.FieldStorage()
    q = form.getfirst('q', '')
    sys.stdout.write("Content-type: application/json\n\n")

    sys.stdout.write(json.dumps(search(q)))


if __name__ == '__main__':
    main()
