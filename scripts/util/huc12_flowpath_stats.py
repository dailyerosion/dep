"""Summarize Flowpath stats."""

import pandas as pd
from pyiem.util import get_dbconn


def main():
    """Go Main Go."""
    df = pd.read_csv("isbi.csv")
    dbconn = get_dbconn("idep")
    cursor = dbconn.cursor()
    for idx, row in df.iterrows():
        huc12 = f"{row['huc12Code']:012.0f}"
        cursor.execute(
            "SELECT count(*), max(bulk_slope), max(max_slope), "
            "avg(bulk_slope), avg(max_slope), stddev(bulk_slope), "
            "stddev(max_slope) from flowpaths where "
            "scenario = 0 and huc_12 = %s",
            (huc12,),
        )
        data = cursor.fetchone()
        for i, col in enumerate(
            [
                "flowpath_count",
                "max_bulk_slope",
                "max_max_slope",
                "avg_bulk_slope",
                "avg_max_slope",
                "std_bulk_slope",
                "std_max_slope",
            ]
        ):
            df.at[idx, col] = data[i]

    df.to_csv("isbi.csv", index=False)


if __name__ == "__main__":
    main()
