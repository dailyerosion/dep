"""Dump Daily Water Balance."""

import glob
import os

from tqdm import tqdm

from pydep.io.dep import read_wb


def main():
    """Go Main Go."""
    huc12s = [
        "071000081505",
    ]
    with open("sm.csv", "w", encoding="ascii") as fh:
        fh.write("huc12,fpath,ofe,date,vsm0_10cm,precip_mm,runoff_mm\n")
        for huc12 in huc12s:
            mydir = f"/i/0/wb/{huc12[:8]}/{huc12[8:]}"
            if not os.path.isdir(mydir):
                continue
            os.chdir(mydir)
            progress = tqdm(glob.glob("*.wb"))
            for fn in progress:
                progress.set_description(fn)
                df = read_wb(fn)
                fpath = fn[:-3].split("_")[-1]
                df["sday"] = df["date"].dt.strftime("%m%d")
                for _, row in df.iterrows():
                    if row["sday"] < "0411" or row["sday"] > "0615":
                        continue
                    fh.write(
                        f"{huc12},{fpath},{row['ofe']},"
                        f"{row['date']:%Y-%m-%d},{row['sw1']:.2f},"
                        f"{row['precip']:.2f},{row['runoff']:.2f}\n"
                    )


if __name__ == "__main__":
    main()
