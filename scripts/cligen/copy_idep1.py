'''Copy the IDEPv1 climate files to IDEPv2

For a first go-around, we are using the IDEPv1 precip data for inputs to IDEPv2

'''
import psycopg2
import os
import shutil

idep = psycopg2.connect(database='idep', host='iemdb')
icursor = idep.cursor()

wepp = psycopg2.connect(database='wepp', host='iemdb')
wcursor = wepp.cursor()


IDEPHOME = "/i"

icursor.execute("""
  SELECT distinct
  round(ST_X(ST_CENTROID(ST_TRANSFORM(geom,4326)))::numeric,2),
  round(ST_Y(ST_CENTROID(ST_TRANSFORM(geom,4326)))::numeric,2)
  from flowpaths
""")
print 'Found %s distinct IDEPv2 Precip Cells' % (icursor.rowcount,)
for row in icursor:
    wcursor.execute("""
    select hrap_i from hrap_polygons where 
    ST_contains(the_geom, ST_Transform(ST_Geometryfromtext(
    'SRID=4326;POINT(%s %s)'),26915))""" % (row[0], row[1]))
    row2 = wcursor.fetchone()
    if row2 is None:
        print 'No results?'
        continue
    hrap = row2[0]
    
    oldfn = "/mnt/idep/RT/clifiles/%s.dat"  % (hrap,)
    newdir = "/i/cli/%03ix%03i" % (0 - row[0], row[1])
    newfn = "%s/%06.2fx%06.2f.cli" % (newdir, 0 - row[0], row[1])
    if not os.path.isdir(newdir):
        os.makedirs(newdir)
    #print oldfn, newfn
    shutil.copyfile(oldfn, newfn)
