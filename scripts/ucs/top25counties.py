"""Go."""

import sys

from pandas.io.sql import read_sql
from pyiem.util import get_dbconn

pgconn = get_dbconn("idep")

df = read_sql(
    """
    with yearly as (
        SELECT huc_12, extract(year from valid) as yr,
        sum(avg_loss) from results_by_huc12 where scenario = 0
        GROUP by huc_12, yr),
    agg as (
        SELECT huc_12, avg(sum) from yearly GROUP by huc_12)

    SELECT st_x(st_centroid(st_transform(geom, 4326))),
    st_y(st_centroid(st_transform(geom, 4326))), a.huc_12, avg
    from huc12 h JOIN agg a on (h.huc_12 = a.huc_12) WHERE
    h.states ~* 'IA' ORDER by avg DESC
    """,
    pgconn,
    index_col="huc_12",
)

pgconn = get_dbconn("postgis")
cursor = pgconn.cursor()

DONE = []
for i, row in df.iterrows():
    cursor.execute(
        """SELECT name from ugcs where end_ts is null and
    state = 'IA' and substr(ugc, 3, 1) = 'C' and
    ST_Contains(geom, St_SetSRID(ST_Point(%s, %s), 4326))
    """,
        (row["st_x"], row["st_y"]),
    )
    name = cursor.fetchone()[0]
    if name not in DONE:
        print(name)
        DONE.append(name)
    if len(DONE) == 25:
        sys.exit()
