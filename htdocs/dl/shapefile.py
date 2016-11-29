#!/usr/bin/env python
"""
Called from DEP map application
"""
import cgi
import datetime
import sys
import os
import shapelib
import dbflib
import shutil
import zipfile
from pyiem import wellknowntext
import psycopg2.extras


def do(dt, dt2):
    """Generate for a given date """
    dbconn = psycopg2.connect(database='idep', host='iemdb', user='nobody')
    cursor = dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    dextra = "valid = %s"
    args = (dt,)
    if dt2 is not None:
        dextra = "valid >= %s and valid <= %s"
        args = (dt, dt2)
    cursor.execute("""WITH data as (
        SELECT ST_AsText(geom) as g,
        huc_12
        from huc12 WHERE scenario = 0), obs as (
        SELECT huc_12,
            sum(coalesce(avg_loss, 0)) as avg_loss,
            sum(coalesce(avg_delivery, 0)) as avg_delivery,
            sum(coalesce(qc_precip, 0)) as qc_precip,
            sum(coalesce(avg_runoff, 0)) as avg_runoff
        from results_by_huc12 WHERE
        """+dextra+""" and scenario = 0 GROUP by huc_12)

        SELECT d.g, d.huc_12,
        coalesce(o.avg_loss, 0),
        coalesce(o.qc_precip, 0),
        coalesce(o.avg_delivery, 0),
        coalesce(o.avg_runoff, 0)
        from data d LEFT JOIN obs o ON (d.huc_12 = o.huc_12)
    """, args)

    os.chdir("/tmp")
    fn = "idepv2_%s" % (dt.strftime("%Y%m%d"),)
    if dt2:
        fn += dt2.strftime("_%Y%m%d")
    shp = shapelib.create(fn, shapelib.SHPT_POLYGON)

    dbf = dbflib.create(fn)
    dbf.add_field("HUC_12", dbflib.FTString, 12, 0)
    dbf.add_field("PREC_MM", dbflib.FTDouble, 8, 2)
    dbf.add_field("LOS_KGM2", dbflib.FTDouble, 8, 2)
    dbf.add_field("RUNOF_MM", dbflib.FTDouble, 8, 2)
    dbf.add_field("DELI_KGM", dbflib.FTDouble, 8, 2)

    for i, row in enumerate(cursor):
        g = wellknowntext.convert_well_known_text(row[0])
        obj = shapelib.SHPObject(shapelib.SHPT_POLYGON, 1, g)
        shp.write_object(-1, obj)
        del(obj)

        dbf.write_record(i, dict(HUC_12=row[1],
                                 PREC_MM=row[3],
                                 LOS_KGM2=row[2],
                                 RUNOF_MM=row[5],
                                 DELI_KGM=row[4]))

    # hack way to close the files
    del(shp)
    del(dbf)

    shutil.copyfile("/opt/iem/data/gis/meta/5070.prj",
                    fn+".prj")
    z = zipfile.ZipFile(fn+".zip", 'w', zipfile.ZIP_DEFLATED)
    suffixes = ['shp', 'shx', 'dbf', 'prj']
    for s in suffixes:
        z.write(fn+"."+s)
    z.close()

    sys.stdout.write("Content-type: application/octet-stream\n")
    sys.stdout.write(("Content-Disposition: attachment; filename=%s.zip\n\n"
                      "") % (fn,))

    sys.stdout.write(file(fn+".zip", 'r').read())

    suffixes.append('zip')
    for s in suffixes:
        os.remove(fn+"."+s)


def main():
    """Generate something nice for the users"""
    form = cgi.FieldStorage()
    dt = datetime.datetime.strptime(form.getfirst('dt'), '%Y-%m-%d')
    dt2 = form.getfirst('dt2')
    if dt2 is not None:
        dt2 = datetime.datetime.strptime(form.getfirst('dt2'), '%Y-%m-%d')
    do(dt, dt2)

if __name__ == '__main__':
    main()
