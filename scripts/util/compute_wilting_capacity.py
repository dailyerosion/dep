"""
Compute a given soil's wilting and capacity values based on what WEPP produces
for a soil moisture time series.  This is kind of backwards logic, but a
thought experiment for now.
"""

import sys

import pandas as pd
from pyiem.database import get_dbconn, get_sqlalchemy_conn
from pyiem.util import logger

from pydep.io.dep import read_wb

LOG = logger()


def run_mukey(mukey) -> pd.DataFrame:
    """Do the mukey work!"""
    with get_sqlalchemy_conn("idep") as conn:
        # We limit to 50 OFEs as we likely(?) need not sample more than that
        df = pd.read_sql(
            """
            select huc_12, fpath, ofe, plastic_limit, o.bulk_slope,
            wepp_min_sw, wepp_max_sw, wepp_min_sw1, wepp_max_sw1,
            management, landuse from gssurgo g, flowpath_ofes o, flowpaths f
            where o.gssurgo_id = g.id and g.mukey = %s and f.scenario = 0
            and f.fid = o.flowpath
            LIMIT 50
            """,
            conn,
            params=(mukey,),
        )
    for idx, row in df.iterrows():
        wbfn = (
            f"/i/0/wb/{row['huc_12'][:8]}/{row['huc_12'][8:12]}/"
            f"{row['huc_12']}_{row['fpath']}.wb"
        )
        wbdf = read_wb(wbfn)
        ofedf = wbdf[wbdf["ofe"] == row["ofe"]]
        df.at[idx, "wepp_min_sw1"] = ofedf["sw1"].min()
        df.at[idx, "wepp_max_sw1"] = ofedf["sw1"].max()
        df.at[idx, "wepp_min_sw"] = ofedf["sw"].min()
        df.at[idx, "wepp_max_sw"] = ofedf["sw"].max()
    # We should have more than 1 OFE at the given max and min values
    maxval = df["wepp_max_sw1"].max()
    if len(df[(df["wepp_max_sw1"] - maxval).abs() < 0.01].index) < 2:
        LOG.warning("Failure quorum at maxval: %s", maxval)
        print(df.sort_values("bulk_slope"))
        sys.exit()

    return df


def main():
    """Go Main Go."""
    with get_sqlalchemy_conn("idep") as conn:
        df = pd.read_sql(
            """
            SELECT g.id, mukey, count(*)
            from gssurgo g, flowpath_ofes o, flowpaths f
            WHERE f.scenario = 0 and f.fid = o.flowpath and o.gssurgo_id = g.id
            and wepp_min_sw is null
            GROUP by g.id, mukey ORDER by count DESC
            """,
            conn,
            index_col="id",
        )
    LOG.info("Found %s soils over %s OFEs", len(df.index), df["count"].sum())
    conn = get_dbconn("idep")
    cursor = conn.cursor()

    cnt = 0
    for gid, row in df.iterrows():
        cnt += 1
        obsdf = run_mukey(row["mukey"])
        LOG.info(
            "mukey: %s [%.3f-%.3f]",
            row["mukey"],
            obsdf["wepp_min_sw1"].min(),
            obsdf["wepp_max_sw1"].max(),
        )
        cursor.execute(
            "UPDATE gssurgo SET wepp_min_sw1 = %s, wepp_max_sw1 = %s, "
            "wepp_min_sw = %s, wepp_max_sw = %s "
            "WHERE id = %s",
            (
                obsdf["wepp_min_sw1"].min(),
                obsdf["wepp_max_sw1"].max(),
                obsdf["wepp_min_sw"].min(),
                obsdf["wepp_max_sw"].max(),
                gid,
            ),
        )
        if cnt % 100 == 0:
            cursor.close()
            conn.commit()
            cursor = conn.cursor()
    cursor.close()
    conn.commit()


if __name__ == "__main__":
    main()
