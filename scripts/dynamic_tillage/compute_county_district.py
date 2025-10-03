"""Build county cross reference."""

import json

import pandas as pd
from pyiem.database import get_sqlalchemy_conn, sql_helper

DISTRICTS = {
    "1": "NW",
    "2": "NC",
    "3": "NE",
    "4": "WC",
    "5": "C",
    "6": "EC",
    "7": "SW",
    "8": "SC",
    "9": "SE",
}


def main():
    """Go main Go."""
    with get_sqlalchemy_conn("postgis") as conn:
        counties = pd.read_sql(
            sql_helper(
                """
    select ugc, st_x(st_centroid(geom)) as lon,
    st_y(st_centroid(geom)) as lat from ugcs where substr(ugc, 3, 1) = 'C'
    and end_ts is null and substr(ugc, 1, 2) in ('IA', 'MN', 'KS', 'NE')
    order by ugc asc
"""
            ),
            conn,
        )

    xref = {}
    with get_sqlalchemy_conn("coop") as conn:
        for _, row in counties.iterrows():
            res = conn.execute(
                sql_helper("""
    select id from climodat_regions c JOIN stations t on (c.iemid = t.iemid)
    where st_contains(c.geom, st_point(:lon, :lat, 4326)) and
    substr(id, 1, 3) in ('IAC', 'MNC', 'KSC', 'NEC')
               """),
                {"lon": row["lon"], "lat": row["lat"]},
            )
            cid = res.fetchone()[0]
            datum = f"{row['ugc'][:2]}_{DISTRICTS[cid[-1]]}"
            xref.setdefault(datum, []).append(row["ugc"])
    with open("datum2county.json", "w") as fh:
        json.dump(xref, fh, indent=2)


if __name__ == "__main__":
    main()
