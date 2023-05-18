"""
Fields exist in multiple HUC12s, we want to clip these and cull any field that
is impossibly small.
"""

import pandas as pd
from pyiem.util import get_sqlalchemy_conn
from sqlalchemy import text


def main():
    """Go Main Go."""
    hucs = []
    with open("myhucs.txt", encoding="ascii") as fh:
        for line in fh:
            hucs.append(line.strip())
    with get_sqlalchemy_conn("idep") as conn:
        minval = 1000.0
        for huc12 in hucs:
            df = pd.read_sql(
                text(
                    """
                with data as (
                    select fbndid, f.huc12, st_area(st_intersection(f.geom,
                        st_transform(h.geom, 5070))) / 4046.86  as newacres
                    from fields f, wbd_huc12 h where f.scenario = 0 and
                    f.huc12 = :huc12 and h.huc12 = :huc12),
                xcheck as (
                    select min(d.newacres) from flowpath_ofes o, flowpaths f,
                    data d where o.flowpath = f.fid and f.huc_12 = d.huc12 and
                    f.scenario = 0 and o.fbndid = d.fbndid order by newacres asc
                """
                ),
                conn,
                params={"huc12": huc12},
                index_col="fbndid",
            )
            if df.empty:
                print(huc12)
                continue
            if df.iloc[0]["newacres"] < minval:
                minval = df.iloc[0]["newacres"]
                print(huc12, minval)


if __name__ == "__main__":
    main()
