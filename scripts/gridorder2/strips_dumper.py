"""Generate the requested output."""

from pyiem.util import get_dbconn
from tqdm import tqdm
import pandas as pd
from pandas.io.sql import read_sql
from pydep.io.wepp import read_env

HUCS = (
    "070801050307 070801050702 071000070104 102300030203 102400030406 "
    "102400030602 102802010203"
).split()


def get_flowpath_lengths(pgconn):
    """Load some metadata."""
    df = read_sql(
        "SELECT scenario, huc_12, fpath, bulk_slope,"
        "ST_LENGTH(geom) as len from flowpaths "
        "WHERE scenario = 95 and huc_12 in %s"
        "ORDER by scenario ASC, huc_12 ASC",
        pgconn,
        params=(tuple(HUCS),),
        index_col=None,
    )
    df["useme"] = True
    return df


def compute_daily(df):
    """Compute daily 2008-2020 totals."""
    envs = []
    for _, row in tqdm(df.iterrows(), total=len(df.index)):
        envfn = (
            f"/i/{row['scenario']}/env/{row['huc_12'][:8]}/"
            f"{row['huc_12'][8:]}/{row['huc_12']}_{row['fpath']}.env"
        )
        envdf = read_env(envfn)
        envdf["scenario"] = row["scenario"]
        envdf["huc_12"] = row["huc_12"]
        envdf["flowpath"] = row["fpath"]
        envdf["delivery"] = envdf["sed_del"] / row["len"]
        envs.append(envdf)
    # We now have dataframe with yearly flowpath totals
    envdf = pd.concat(envs)
    return envdf


def main():
    """Do great things."""
    pgconn = get_dbconn("idep")
    df = get_flowpath_lengths(pgconn)
    result_full = compute_daily(df)

    with pd.ExcelWriter("daily.xlsx") as writer:
        result_full.to_excel(writer, "Single Flowpath-daily", index=False)


if __name__ == "__main__":
    main()
