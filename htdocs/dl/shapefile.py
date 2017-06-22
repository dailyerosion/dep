#!/usr/bin/env python
"""
Called from DEP map application
"""
import cgi
import datetime
import sys
import os
import shutil
import zipfile

import psycopg2
from geopandas import GeoDataFrame


def workflow(dt, dt2):
    """Generate for a given date """
    dbconn = psycopg2.connect(database='idep', host='iemdb', user='nobody')
    dextra = "valid = %s"
    args = (dt,)
    if dt2 is not None:
        dextra = "valid >= %s and valid <= %s"
        args = (dt, dt2)
    df = GeoDataFrame.from_postgis("""
        WITH data as (
            SELECT simple_geom, huc_12
            from huc12 WHERE scenario = 0),
        obs as (
            SELECT huc_12,
            sum(coalesce(avg_loss, 0)) as avg_loss,
            sum(coalesce(avg_delivery, 0)) as avg_delivery,
            sum(coalesce(qc_precip, 0)) as qc_precip,
            sum(coalesce(avg_runoff, 0)) as avg_runoff
            from results_by_huc12 WHERE
            """+dextra+""" and scenario = 0 GROUP by huc_12)

        SELECT d.simple_geom, d.huc_12,
        coalesce(o.qc_precip, 0) as prec_mm,
        coalesce(o.avg_loss, 0) as los_kgm2,
        coalesce(o.avg_runoff, 0) as runof_mm,
        coalesce(o.avg_delivery, 0) as deli_kgm
        from data d LEFT JOIN obs o ON (d.huc_12 = o.huc_12)
    """, dbconn, params=args, geom_col='simple_geom')

    os.chdir("/tmp")
    fn = "idepv2_%s" % (dt.strftime("%Y%m%d"),)
    if dt2:
        fn += dt2.strftime("_%Y%m%d")
    df.columns = [s.upper() if s != 'simple_geom' else s
                  for s in df.columns.values]
    df.to_file(fn + ".shp")
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
    workflow(dt, dt2)


if __name__ == '__main__':
    main()
