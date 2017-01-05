"""Report a listing of potentially bad climate files"""
import os
import psycopg2

bad = []
pgconn = psycopg2.connect(database='idep', host='iemdb', user='nobody')
cursor = pgconn.cursor()

for root, dirs, files in os.walk("/i/0/error"):
    for fn in files:
        (huc12, fpath) = fn[:-6].split("_")
        cursor.execute("""SELECT climate_file from flowpaths
        where scenario = 0 and huc_12 = %s and fpath = %s
        """, (huc12, fpath))
        clifile = cursor.fetchone()[0]
        if clifile not in bad:
            bad.append(clifile)

bad.sort()
for fn in bad:
    print fn
