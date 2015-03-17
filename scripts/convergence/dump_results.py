import psycopg2
pgconn = psycopg2.connect(database='idep')
cursor = pgconn.cursor()

cursor.execute("""
  SELECT hs_id, huc_12, extract(year from valid) as yr,
  sum(runoff) as sum_runoff,
  sum(loss) as sum_loss, sum(delivery) as sum_delivery from results
  WHERE scenario = 5
  GROUP by hs_id, huc_12, yr
""")

for row in cursor:
    print "%s,%s,%s,%.4f,%.4f,%.4f" % row
