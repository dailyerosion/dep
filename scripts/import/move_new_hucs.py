"""One off to look for new hucs."""

import glob
import os
import pandas as pd
from pyiem.util import get_sqlalchemy_conn


def main():
    """Go Main Go."""
    with get_sqlalchemy_conn("idep") as conn:
        df = pd.read_sql(
            "SELECT huc_12 from huc12 where scenario = 0",
            conn,
        )

    for fn in glob.glob("../../data/220713/*.json"):
        huc = fn[31:43]
        if huc not in df["huc_12"].values:
            print(fn)
            os.system(f"cp {fn} ../../data/220713.new/")


if __name__ == "__main__":
    main()
