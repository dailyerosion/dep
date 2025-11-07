"""Generate the requested output."""

import pandas as pd
from pyiem.util import get_dbconn
from tqdm import tqdm

from pydep.io.wepp import read_env

HUCS = (
    "102400090102 102300020307 102400020604 102801020801 071000040902 "
    "070600040608 070802040604 070802090402"
).split()
XREF = {
    91: 1,
    92: 2,
    93: 3,
    94: 4,
    95: 5,
    96: 6,
    97: 7,
    98: 9,
    99: 8,
    100: 11,
    101: 10,
}


def get_flowpath_lengths(pgconn):
    """Load some metadata."""
    df = pd.read_sql(
        "SELECT scenario, huc_12, fpath, bulk_slope,"
        "ST_LENGTH(geom) as len from flowpaths "
        "WHERE scenario >= 91 and scenario <= 101 and huc_12 in %s"
        "ORDER by scenario ASC, huc_12 ASC",
        pgconn,
        params=(tuple(HUCS),),
        index_col=None,
    )
    df["useme"] = False
    # We only want flowpaths that existed in all scenarios, unsure of the
    # most efficient way to do this, so here we are.
    gdf = df.groupby(["huc_12", "fpath"]).count()
    good = gdf[gdf["bulk_slope"] == 11].index.values.tolist()
    for idx, row in df.iterrows():
        df.at[idx, "useme"] = (row["huc_12"], row["fpath"]) in good
    return df[df["useme"]]


def compute_yearly(df, bymax=False, individual=False):
    """Compute yearly 2011-2020 totals."""
    envs = []
    for _, row in tqdm(df.iterrows(), total=len(df.index)):
        envfn = (
            f"/i/{row['scenario']}/env/{row['huc_12'][:8]}/"
            f"{row['huc_12'][8:]}/{row['huc_12']}_{row['fpath']}.env"
        )
        if bymax:
            envdf = (
                read_env(envfn)
                .sort_values("precip", ascending=False)
                .groupby("year")
                .nth(0)
                .reset_index()
            )
        else:
            envdf = read_env(envfn).groupby("year").sum().copy().reset_index()
        envdf["scenario"] = row["scenario"]
        envdf["huc_12"] = row["huc_12"]
        envdf["flowpath"] = row["fpath"]
        envdf["delivery"] = envdf["sed_del"] / row["len"]
        envs.append(envdf)
    # We now have dataframe with yearly flowpath totals
    envdf = pd.concat(envs)
    key = ["scenario", "huc_12", "year"]
    if individual:
        key = ["scenario", "huc_12", "flowpath", "year"]
    if individual:
        genvdf = envdf.set_index(key)
    else:
        genvdf = envdf.groupby(by=key).mean().copy()
    if bymax:
        # add back in a good date, maybe
        genvdf["date"] = envdf.groupby(by=key).nth(0)["date"]
    return genvdf


def main():
    """Do great things."""
    pgconn = get_dbconn("idep")
    df = get_flowpath_lengths(pgconn)
    df221 = df[df["len"] > 22.1]
    avg_len_full = df.groupby(["scenario", "huc_12"]).mean()
    avg_len_221 = df221.groupby(["scenario", "huc_12"]).mean()
    flowpath_counts_full = df.groupby(["scenario", "huc_12"]).count()
    flowpath_counts_221 = df221.groupby(["scenario", "huc_12"]).count()
    # For all hillslopes
    opts = dict(bymax=True, individual=False)
    result_full = compute_yearly(df, **opts)
    # Only those over > 22.1m
    result_221 = compute_yearly(df[df["len"] > 22.1], **opts)

    # Result time
    rows = []
    for huc_12 in tqdm(HUCS):
        for scenario in XREF:
            fdf = df[(df["huc_12"] == huc_12) & (df["scenario"] == scenario)]
            # keep the below from overlooping
            fpaths = [
                0,
            ]
            if opts["individual"]:
                fpaths = fdf["fpath"].values
            for _ in fpaths:
                for year in range(2011, 2021):
                    key = (scenario, huc_12, year)
                    if key not in result_full.index:
                        print(key)
                        continue
                    rows.append(
                        {
                            # "Flowpath ID": flowpath,
                            "HUC12": huc_12,
                            "Situation": XREF[scenario],
                            "Date for daily max rainfall": result_full.at[
                                key, "date"
                            ],
                            "Number of flowpath": flowpath_counts_full.at[
                                (scenario, huc_12), "len"
                            ],
                            "Avg Flowpath Length(m)": avg_len_full.at[
                                (scenario, huc_12), "len"
                            ],
                            "Yearly Rainfall (mm)": result_full.at[
                                key, "precip"
                            ],
                            "Yearly Runoff (mm)": result_full.at[
                                key, "runoff"
                            ],
                            "Yearly Delivery (kg/m2)": result_full.at[
                                key, "delivery"
                            ],
                            "Yearly Detachment (kg/m2)": result_full.at[
                                key, "av_det"
                            ],
                            "Number of flowpath >22.1": flowpath_counts_221.at[
                                (scenario, huc_12), "len"
                            ],
                            "Avg Flowpath Length(m) >22.1": avg_len_221.at[
                                (scenario, huc_12), "len"
                            ],
                            "Yearly Runoff (mm) >22.1": result_221.at[
                                key, "runoff"
                            ],
                            "Yearly Delivery (kg/m2) >22.1": result_221.at[
                                key, "delivery"
                            ],
                            "Yearly Detachment (kg/m2) >22.1": result_221.at[
                                key, "av_det"
                            ],
                        }
                    )
    resdf = pd.DataFrame(rows)
    with pd.ExcelWriter("daily.xlsx") as writer:
        resdf.to_excel(writer, "Single Flowpath-yearly", index=False)


if __name__ == "__main__":
    main()
