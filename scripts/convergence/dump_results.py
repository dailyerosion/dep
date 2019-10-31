"""blah."""
from pyiem.util import get_dbconn

pgconn = get_dbconn("idep")
cursor = pgconn.cursor()

cursor.execute(
    """
  SELECT r.hs_id, r.huc_12, p.fpath, extract(year from valid) as yr,
  sum(runoff) as sum_runoff,
  sum(loss) as sum_loss, sum(delivery) as sum_delivery from
  results r JOIN flowpaths p on (r.hs_id = p.fid)
  WHERE r.scenario = 5
  GROUP by r.hs_id, r.huc_12, fpath, yr
"""
)

print("CATCHMENT,HUC12,FPATH,YEAR,RUNOFF,LOSS,DELIVERY")
for row in cursor:
    fpath = row[0]
    if fpath < 100:
        catchment = 0
    else:
        catchment = int(str(fpath)[:-2])
    print(str(catchment) + ",%s,%s,%s,%.4f,%.4f,%.4f" % row[1:])
