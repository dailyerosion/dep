"""Dump out hourly wind for a year for Dr Wilson."""

import requests
import pandas as pd
from tqdm import tqdm

IEMRE = "http://mesonet.agron.iastate.edu/iemre/hourly"


def main():
    """Go Main Go."""
    lat = 48.75
    lon = -97.5
    progress = tqdm(pd.date_range("2021-01-01", "2021-12-31"))
    with open("/tmp/wind.txt", "w", encoding="utf-8") as ffh:
        for dt in progress:
            progress.set_description(dt.strftime("%Y-%m-%d"))
            uri = f"{IEMRE}/{dt:%Y-%m-%d}/{lat:.2f}/{lon:.2f}/json"
            res = requests.get(uri).json()
            with open(f"wind/{dt:%Y%m%d}.txt", "w", encoding="utf-8") as fh:
                for i, et in enumerate(res["data"]):
                    vel = (et["uwnd_mps"] ** 2 + et["vwnd_mps"] ** 2) ** 0.5
                    fh.write(f"{vel:.2f} ")
                    if i > 0 and (i + 1) % 6 == 0:
                        fh.write("\n")
                    ffh.write(f"{et['valid_local']},{vel:.2f}\n")


if __name__ == "__main__":
    main()
