import psycopg2

postgis = psycopg2.connect(dbname='postgis', host='iemdb', user='nobody')
pcursor = postgis.cursor()

dep = psycopg2.connect(dbname='idep', host='localhost', port=5555,
                       user='mesonet')
cursor = dep.cursor()
cursor2 = dep.cursor()

cursor.execute("""with data as (
    SELECT ST_Transform(ST_Centroid(geom), 4326) as geo, gid
    from huc12 where ugc is null)

    SELECT ST_x(geo), ST_y(geo), gid from data
""")
for row in cursor:
    pcursor.execute("""
    select ugc from ugcs where end_ts is null and
    ST_Contains(geom, ST_SetSrid(ST_GeomFromText('POINT(%s %s)'), 4326))
    and substr(ugc, 3, 1) = 'C'
    """ % (row[0], row[1]))
    ugc = pcursor.fetchone()[0]
    cursor2.execute("""UPDATE huc12 SET ugc = %s where gid = %s
    """, (ugc, row[2]))

cursor2.close()
dep.commit()
