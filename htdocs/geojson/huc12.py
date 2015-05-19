#!/usr/bin/env python
"""GeoJSON service for HUC12 data"""
import sys
import psycopg2
import json
import memcache
import cgi
import datetime


def do(ts, ts2):
    """Do work"""
    pgconn = psycopg2.connect(database='idep', host='iemdb', user='nobody')
    cursor = pgconn.cursor()
    utcnow = datetime.datetime.utcnow()
    dextra = "valid = %s"
    args = (ts,)
    if ts2 is not None:
        dextra = "valid >= %s and valid < %s"
        args = (ts, ts2)
    cursor.execute("""WITH data as (
        SELECT ST_asGeoJson(ST_Transform(simple_geom, 4326), 4) as g,
        huc_12
        from ia_huc12), obs as (
        SELECT huc_12,
            sum(coalesce(avg_loss, 0)) * 4.463 as avg_loss,
            sum(coalesce(avg_delivery, 0)) * 4.463 as avg_delivery,
            sum(coalesce(qc_precip, 0)) / 25.4 as qc_precip,
            sum(coalesce(avg_runoff, 0)) / 25.4 as avg_runoff
        from results_by_huc12 WHERE
        """+dextra+""" and scenario = 0 GROUP by huc_12)

        SELECT d.g, d.huc_12, o.avg_loss, o.qc_precip, o.avg_delivery,
        o.avg_runoff from
        data d LEFT JOIN obs o ON (d.huc_12 = o.huc_12)
    """, args)
    res = {'type': 'FeatureCollection',
           'crs': {'type': 'EPSG',
                   'properties': {'code': 4326, 'coordinate_order': [1, 0]}},
           'features': [],
           'generation_time': utcnow.strftime("%Y-%m-%dT%H:%M:%SZ"),
           'count': cursor.rowcount}
    for row in cursor:
        res['features'].append(dict(type="Feature",
                                    id=row[1],
                                    properties=dict(
                                        avg_loss=row[2] or 0,
                                        qc_precip=row[3] or 0,
                                        avg_delivery=row[4] or 0,
                                        avg_runoff=row[5] or 0),
                                    geometry=json.loads(row[0])
                                    ))

    return json.dumps(res)


def main(argv):
    """Do Fun things"""
    sys.stdout.write("Content-Type: application/vnd.geo+json\n\n")
    form = cgi.FieldStorage()
    cb = form.getfirst('callback', None)
    ts = datetime.datetime.strptime(form.getfirst('date', '2015-05-05'),
                                    '%Y-%m-%d')
    ts2 = None
    if form.getfirst('date2', None) is not None:
        ts2 = datetime.datetime.strptime(form.getfirst('date2'), '%Y-%m-%d')

    mckey = ("/geojson/huc12/%s/%s"
             ) % (ts.strftime("%Y%m%d"),
                  '' if ts2 is None else ts2.strftime("%Y%m%d"))
    mc = memcache.Client(['iem-memcached:11211'], debug=0)
    res = mc.get(mckey)
    if not res:
        res = do(ts, ts2)
        mc.set(mckey, res, 15)

    if cb is None:
        sys.stdout.write(res)
    else:
        sys.stdout.write("%s(%s)" % (cb, res))


if __name__ == '__main__':
    main(sys.argv)
