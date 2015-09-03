#!/usr/bin/env python
"""GeoJSON service for HUC12 data"""
import sys
import psycopg2
import json
import memcache
import cgi
import datetime


def do(huc12, mode):
    """Do work"""
    pgconn = psycopg2.connect(database='idep', host='iemdb', user='nobody')
    cursor = pgconn.cursor()
    utcnow = datetime.datetime.utcnow()
    if mode == 'daily':
        cursor.execute("""
            SELECT valid, avg_loss * 4.463, avg_delivery * 4.463,
            qc_precip / 25.4, avg_runoff / 25.4
            from results_by_huc12 where huc_12 = %s and scenario = 0 ORDER
            by valid ASC
        """, (huc12, ))
    else:
        cursor.execute("""
            SELECT extract(year from valid) as yr,
            sum(avg_loss) * 4.463, sum(avg_delivery) * 4.463,
            sum(qc_precip) / 25.4, sum(avg_runoff) / 25.4
            from results_by_huc12 where huc_12 = %s and scenario = 0
            GROUP by yr ORDER by yr ASC
        """, (huc12, ))
    res = {'results': [],
           'huc12': huc12,
           'generation_time': utcnow.strftime("%Y-%m-%dT%H:%M:%SZ")}
    for row in cursor:
        dt = row[0]
        if isinstance(row[0], float):
            dt = datetime.date(int(row[0]), 1, 1)
        res['results'].append(dict(date=dt.strftime("%m/%d/%Y"),
                                   avg_loss=row[1],
                                   avg_delivery=row[2],
                                   qc_precip=row[3],
                                   avg_runoff=row[4]))
    return json.dumps(res)


def main(argv):
    """Do Fun things"""
    sys.stdout.write("Content-Type: application/vnd.geo+json\n\n")
    form = cgi.FieldStorage()
    cb = form.getfirst('callback', None)
    huc12 = form.getfirst('huc12', '000000000000')[:12]
    mode = form.getfirst('mode', 'daily')

    mckey = ("/geojson/huc12_events/%s/%s"
             ) % (huc12, mode)
    mc = memcache.Client(['iem-memcached:11211'], debug=0)
    res = mc.get(mckey)
    if not res:
        res = do(huc12, mode)
        mc.set(mckey, res, 15)

    if cb is None:
        sys.stdout.write(res)
    else:
        sys.stdout.write("%s(%s)" % (cb, res))


if __name__ == '__main__':
    main(sys.argv)
