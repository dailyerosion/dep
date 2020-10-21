"""Convert a WEPP CLI file to something WEPPCLIFF enjoys.

DT_1,PRECIP,DT_3,MAX_TEMP,MIN_TEMP,SO_RAD,W_VEL,W_DIR,DP_TEMP,STATION,LAT,LON,
ELEV
"""
import sys
from datetime import date, datetime

import pandas as pd


def main(argv):
    """Go Main Go."""
    fn = argv[1]
    outfn = argv[2]

    lines = open(fn).readlines()
    linenum = 15
    daily = []
    bp = []
    while linenum < len(lines):
        (da, mo, year, breakpoints, tmax, tmin, rad, wvl, wdir, tdew) = lines[
            linenum
        ].split()
        daily.append(
            [
                date(int(year), int(mo), int(da)),
                tmax,
                tmin,
                rad,
                wvl,
                wdir,
                tdew,
            ]
        )
        breakpoints = int(breakpoints)
        accum = 0
        for i in range(1, breakpoints + 1):
            (ts, newaccum) = lines[linenum + i].split()
            newaccum = float(newaccum)
            minutes = int(float(ts) * 60.0)
            hours = int(minutes / 60)
            minutes = minutes % 60
            acc = newaccum - accum
            accum = newaccum
            bp.append(
                [datetime(int(year), int(mo), int(da), hours, minutes), acc]
            )
        linenum += breakpoints + 1

    daily = pd.DataFrame(
        daily,
        columns=[
            "DT_3",
            "MAX_TEMP",
            "MIN_TEMP",
            "SO_RAD",
            "W_VEL",
            "W_DIR",
            "DP_TEMP",
        ],
    )
    bp = pd.DataFrame(bp, columns=["DT_1", "PRECIP"])
    df = bp.join(daily, how="outer")
    for col in ["STATION", "LAT", "LON", "ELEV"]:
        df[col] = None
    df.at[0, "STATION"] = "test"
    df.at[0, "LAT"] = 42.4
    df.at[0, "LON"] = -93.9
    df.at[0, "ELEV"] = 341
    df["DT_1"] = df["DT_1"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df["DT_3"] = pd.to_datetime(df["DT_3"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    df = df.fillna("NA")
    df.to_csv(outfn, index=False)


if __name__ == "__main__":
    main(sys.argv)
