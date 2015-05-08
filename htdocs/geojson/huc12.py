#!/usr/bin/env python
"""GeoJSON service for HUC12 data"""
import sys
import psycopg2
import json
import memcache
import cgi
import datetime


def do(ts):
    """Do work"""
    pgconn = psycopg2.connect(database='idep', host='iemdb', user='nobody')
    cursor = pgconn.cursor()
    utcnow = datetime.datetime.utcnow()
    cursor.execute("""WITH data as (
        SELECT ST_asGeoJson(ST_Transform(ST_Simplify(geom,500),4326)) as g,
        huc_12
        from ia_huc12), obs as (
        SELECT huc_12,
            coalesce(avg_loss, 0) * 4.463 as avg_loss,
            coalesce(avg_delivery, 0) * 4.464 as avg_delivery,
            coalesce(qc_precip, 0) / 25.4 as qc_precip,
            coalesce(avg_runoff, 0) / 25.4 as avg_runoff
        from results_by_huc12 WHERE
        valid = %s)

        SELECT d.g, d.huc_12, o.avg_loss, o.qc_precip, o.avg_delivery,
        o.avg_runoff from
        data d LEFT JOIN obs o ON (d.huc_12 = o.huc_12)
    """, (ts,))
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
    field = cgi.FieldStorage()
    ts = datetime.datetime.strptime(field.getfirst('date', '2015-05-05'),
                                    '%Y-%m-%d')
    res = do(ts)
    sys.stdout.write(res)

if __name__ == '__main__':
    main(sys.argv)
