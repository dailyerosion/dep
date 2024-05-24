"""Merge in Gelder yearly estimates for further review."""

import glob

import pandas as pd
from pyiem.database import get_dbconnc
from tqdm import tqdm


def main():
    """Go Main Go."""
    conn, cursor = get_dbconnc("idep")
    ppath = "dep_ACPF2022_idepACPF_ResCov_till_combined/*.csv"
    for csvfn in tqdm(glob.glob(ppath)):
        df = pd.read_csv(csvfn).rename(
            columns={
                "Pct_RC_None_CY_2017": "r2017",
                "Pct_RC_None_CY_2018": "r2018",
                "Pct_RC_None_CY_2019": "r2019",
                "Pct_RC_None_CY_2020": "r2020",
                "Pct_RC_None_CY_2021": "r2021",
                "Pct_RC_None_CY_2022": "r2022",
            }
        )
        for yr in range(2017, 2023):
            df[f"r{yr}"] = df[f"r{yr}"].fillna(-1).astype("int8")
        df["huc12"] = df["FBndID"].str.slice(1, 13)
        df["field"] = df["FBndID"].str.slice(14, 18)
        cursor.executemany(
            """
            update fields SET residue2017 = %(r2017)s,
            residue2018 = %(r2018)s, residue2019 = %(r2019)s,
            residue2020 = %(r2020)s, residue2021 = %(r2021)s,
            residue2022 = %(r2022)s WHERE huc12 = %(huc12)s and
            fbndid = %(field)s and scenario = 0
            """,
            df.to_dict("records"),
        )
        cursor.close()
        conn.commit()
        cursor = conn.cursor()
    for yr in range(2017, 2023):
        cursor.execute(
            f"update fields set residue{yr} = null where residue{yr} < 0"
        )
        cursor.close()
        conn.commit()
        cursor = conn.cursor()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
