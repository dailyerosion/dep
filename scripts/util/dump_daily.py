import psycopg2

pgconn = psycopg2.connect(database='idep', host='iemdb', user='nobody')
cursor = pgconn.cursor()

pgconn2 = psycopg2.connect(database='postgis', host='iemdb', user='nobody')
cursor2 = pgconn2.cursor()

counties = ['Adair', 'Audubon',
            'Boone', 'Buena Vista', 'Calhoun', 'Carroll', 'Clay', 'Dallas',
            'Greene', 'Guthrie', 'Madison', 'Palo Alto', 'Pocahontas',
            'Polk', 'Sac', 'Warren', 'Webster']

huc12s = []
for county in counties:
    cursor2.execute("""SELECT ST_astext(geom) from ugcs where end_ts is null
    and name = %s and state = 'IA' and substr(ugc, 3, 1) = 'C'""", (county,))
    # Find HUC12s
    geom = cursor2.fetchone()[0]

    cursor.execute("""SELECT huc_12 from huc12 where scenario = 0 and
    ST_Overlaps(ST_Transform(geom, 4326), ST_SetSRID(ST_GeomFromEWKT(%s),4326))""", (geom,))
    for row in cursor:
        if row[0] not in huc12s:
            huc12s.append(row[0])

print 'HUC12,DATE,DETACH,RUNOFF,LOSS,PRECIP'
for huc12 in huc12s:
    cursor.execute("""SELECT valid, coalesce(avg_loss,0),
    coalesce(avg_runoff,0), coalesce(avg_delivery,0),
    coalesce(qc_precip, avg_precip) from results_by_huc12 where valid < '2015-05-27' and scenario = 0
    and huc_12 = %s ORDER by valid ASC""", (huc12, ))
    for row in cursor:
        print "%s,%s,%s,%s,%s,%s" % (huc12, row[0], row[1], row[2], row[3],
                                       row[4])
