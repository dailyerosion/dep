'''
 Copy over climatatic files from IDEPv1
'''
import psycopg2
import os
import subprocess

idep = psycopg2.connect(database='idep', host='iemdb')
icursor = idep.cursor()

wepp = psycopg2.connect(database='wepp', host='iemdb')
wcursor = wepp.cursor()


IDEPHOME = "/i"

icursor.execute("""
  SELECT huc_12, hs_id, ST_x(geom), ST_y(geom) from hillslopes
""")
for row in icursor:
    wcursor.execute("""
    select hrap_i from hrap_polygons where 
    ST_contains(the_geom, ST_Transform(ST_Geometryfromtext(
    'SRID=4326;POINT(%s %s)'),26915))""" % (row[2], row[3]))
    row2 = wcursor.fetchone()
    if row2 is None:
        continue
    hrap = row2[0]
    
    oldfn = "/mnt/idep/RT/clifiles/%s.dat"  % (hrap,)
    newfn = "%s/cli/%06.2f0_%06.2f0.cli" % (IDEPHOME, 0 - row[2], row[3])
    
    if not os.path.isfile(newfn):
        print oldfn, newfn
        subprocess.call("scp mesonet@mesonet:%s %s" % (oldfn, oldfn), shell=True)
        subprocess.call("cp %s %s" % (oldfn, newfn), shell=True)
