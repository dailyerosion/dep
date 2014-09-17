'''Copy the IDEPv1 climate files to IDEPv2

For a first go-around, we are using the IDEPv1 precip data for inputs to IDEPv2

'''
import psycopg2
import os
import shutil
import subprocess
import sys

SCENARIO = sys.argv[1]

idep = psycopg2.connect(database='idep', host='iemdb')
icursor = idep.cursor()

wepp = psycopg2.connect(database='wepp', host='iemdb')
wcursor = wepp.cursor()

def get_latlon(clifile):
    """ Convert a clifile name into lon and latitude """
    fn = clifile.split("/")[-1]
    lat = float(fn[7:13])
    lon = 0 - float(fn[:6])
    return lon, lat

icursor.execute("""
  SELECT distinct climate_file from flowpaths WHERE scenario = %s
  and climate_file is not null
""", (SCENARIO,) )
print 'Found %s distinct IDEPv2 Precip Cells' % (icursor.rowcount,)
for row in icursor:
    clifile = "/i/%s/%s" % (SCENARIO, row[0])
    if os.path.isfile(clifile):
        continue
    lon, lat = get_latlon( clifile )
    wcursor.execute("""
    select hrap_i from hrap_polygons where 
    ST_contains(the_geom, ST_Transform(ST_Geometryfromtext(
    'SRID=4326;POINT(%s %s)'),26915)) and used""" % (lon, lat))
    row2 = wcursor.fetchone()
    if row2 is None:
        # Find the closest hrap_polygon
        wcursor.execute("""select hrap_i, 
        ST_Distance(ST_Geometryfromtext('SRID=4326;POINT(%s %s)'), 
        ST_Transform(the_geom,4326)) from hrap_polygons WHERE used
        ORDER by st_distance ASC LIMIT 1""" % (lon, lat))
        row2 = wcursor.fetchone()
        print '---> No HRAP Polygon for Lon: %.3f Lat: %.3f, assign: %s' % (
                                        lon, lat, row2[0])
        
    hrap = row2[0]
    
    oldfn = "/mnt/idep/data/clifiles/%s.dat"  % (hrap,)
    newdir = os.path.basename(clifile)
    if not os.path.isdir(newdir):
        os.makedirs(newdir)

    print oldfn, clifile
    shutil.copyfile(oldfn, clifile)
    #subprocess.call("ln -s %s %s" % (oldfn, newfn), shell=True)