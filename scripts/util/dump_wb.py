"""Dump Daily Water Balance."""

import glob
import os
import sys

from tqdm import tqdm

from dailyerosion.io.dep import read_wb


def run(huc12):
    """Go Main Go."""
    fn = f"/i/0/meta/{huc12[:8]}/{huc12[8:]}/sm{huc12}.csv"
    if os.path.isfile(fn):
        print(f"Skipping {huc12} as {fn} exists")
        return
    with open(fn, "w", encoding="ascii") as fh:
        fh.write("huc12,fpath,ofe,date,vsm0_10cm,precip_mm,runoff_mm\n")
        mydir = f"/i/0/wb/{huc12[:8]}/{huc12[8:]}"
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


def main():
    """Go Main Go."""
    for root, _dirs, _files in os.walk("/i/0/wb"):
        tokens = root.split("/")
        if len(tokens) == 6:
            _h = tokens[4] + tokens[5]
            if _h.endswith(sys.argv[1]):
                run(_h)


if __name__ == "__main__":
    main()
