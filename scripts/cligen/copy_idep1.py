'''Copy the IDEPv1 climate files to IDEPv2

For a first go-around, we are using the IDEPv1 precip data for inputs to IDEPv2

'''
import psycopg2
import os
import shutil
import subprocess

idep = psycopg2.connect(database='idep', host='iemdb')
icursor = idep.cursor()

wepp = psycopg2.connect(database='wepp', host='iemdb')
wcursor = wepp.cursor()


IDEPHOME = "/i"

icursor.execute("""
  SELECT distinct
  round(ST_X(ST_PointN(ST_TRANSFORM(geom,4326), 1))::numeric,2),
  round(ST_Y(ST_PointN(ST_TRANSFORM(geom,4326), 1))::numeric,2)
  from flowpaths
""")
print 'Found %s distinct IDEPv2 Precip Cells' % (icursor.rowcount,)
for row in icursor:
    wcursor.execute("""
    select hrap_i from hrap_polygons where 
    ST_contains(the_geom, ST_Transform(ST_Geometryfromtext(
    'SRID=4326;POINT(%s %s)'),26915)) and used""" % (row[0], row[1]))
    row2 = wcursor.fetchone()
    if row2 is None:
        # Find the closest hrap_polygon
        wcursor.execute("""select hrap_i, 
        ST_Distance(ST_Geometryfromtext('SRID=4326;POINT(%s %s)'), 
        ST_Transform(the_geom,4326)) from hrap_polygons 
        ORDER by st_distance ASC LIMIT 1""" % (row[0], row[1]))
        row2 = wcursor.fetchone()
        print '---> No HRAP Polygon for Lon: %.3f Lat: %.3f, assign: %s' % (
                                        row[0], row[1], row2[0])
        
    hrap = row2[0]
    
    oldfn = "/mnt/idep/data/clifiles/%s.dat"  % (hrap,)
    newdir = "/i/cli/%03.0fx%03.0f" % (0 - row[0], row[1])
    newfn = "%s/%06.2fx%06.2f.cli" % (newdir, 0 - row[0], row[1])
    if not os.path.isdir(newdir):
        os.makedirs(newdir)
    if os.path.isfile(newfn):
        continue
        #os.unlink(newfn)
    print oldfn, newfn
    shutil.copyfile(oldfn, newfn)
    #subprocess.call("ln -s %s %s" % (oldfn, newfn), shell=True)