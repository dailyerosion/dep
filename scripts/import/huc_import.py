import psycopg2
import glob
import subprocess
import os

idep = psycopg2.connect(database='idep', host='iemdb')
icursor = idep.cursor()

os.chdir("a")
for fn in glob.glob("*.dbf"):

    p = subprocess.Popen("dbfdump %s" % (fn,), stdout=subprocess.PIPE, 
                         shell=True)
    data = p.stdout.read()
    for line in data.split("\n"):
        if line.strip() == '':
            continue
        (huc12, hs_id, lon, lat) = line.strip().split()
        if huc12 == 'Id':
            continue
        huc12 = fn.split("_")[1].split(".")[0]
        icursor.execute("""INSERT into hillslopes(huc_12, hs_id, geom) values
        ('%s', %s, 'SRID=4326;POINT(%s %s)')""" % (huc12, hs_id, lon, lat))
    
icursor.close()
idep.commit()
idep.close()
    