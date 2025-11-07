"""Need something that prints diagnostics of our climate file"""

import datetime
import sys

import netCDF4
import numpy as np
import pandas as pd
import pytz
import requests
from pyiem.iemre import hourly_offset
from pyiem.util import c2f, mm2inch

from pydep.io.wepp import read_cli

LDATE = (datetime.date.today() - datetime.timedelta(days=1)).strftime(
    "%Y-%m-%d"
)


def compute_stage4(lon, lat, year):
    """Build a daily dataframe for the stage4 data"""
    nc = netCDF4.Dataset("/mesonet/data/stage4/%s_stage4_hourly.nc" % (year,))
    lons = nc.variables["lon"][:]
    lats = nc.variables["lat"][:]
    dist = ((lons - lon) ** 2 + (lats - lat) ** 2) ** 0.5
    (yidx, xidx) = np.unravel_index(dist.argmin(), dist.shape)
    print(
        ("Computed stage4 nclon:%.2f nclat:%.2f yidx:%s xidx:%s ")
        % (lons[yidx, xidx], lats[yidx, xidx], yidx, xidx)
    )
    p01i = mm2inch(nc.variables["p01m"][:, yidx, xidx])
    nc.close()
    df = pd.DataFrame(
        {"precip": 0.0},
        index=pd.date_range(f"{year}-01-01", min(LDATE, f"{year}-12-31")),
    )
    for date in df.index.values:
        date2 = datetime.datetime.utcfromtimestamp(date.tolist() / 1e9)
        ts = datetime.datetime(date2.year, date2.month, date2.day, 6)
        ts = ts.replace(tzinfo=pytz.utc)
        ts = ts.astimezone(pytz.timezone("America/Chicago"))
        ts = ts.replace(hour=0)
        ts = ts.astimezone(pytz.utc)
        tidx = hourly_offset(ts)
        # values are in the rears
        val = np.ma.sum(p01i[tidx + 1 : tidx + 25])
        if val > 0:
            df.at[date, "precip"] = val  # close enough
    return df


def fn2lonlat(filename):
    """Convert the filename to lon and lat"""
    tokens = filename.split("/")[-1].rsplit(".", 1)[0].split("x")
    return [0 - float(tokens[0]), float(tokens[1])]


def do_qc(fn, df, year):
    """Run some checks on this dataframe"""
    (lon, lat) = fn2lonlat(fn)
    stage4 = compute_stage4(lon, lat, year)
    # Does the frame appear to have all dates?
    if len(df.index) != len(df.resample("D").mean().index):
        print("ERROR: Appears to be missing dates!")

    with open(fn, encoding="utf-8") as fh:
        if fh.read()[-1] != "\n":
            print("ERROR: File does not end with \\n")

    print("--------- Summary stats from the .cli file")
    print("YEAR |  RAIN | MAXRATE | MAXACC | #DAYS | #>1RT | RAD/D")
    print(" --- | --- | --- | --- | --- | --- | ---")
    for _year, gdf in df.groupby(by=df.index.year):
        print(
            ("%s | %6.2f | %7.2f | %7.2f | %6i | %6i | %6.0f")
            % (
                _year,
                mm2inch(gdf["pcpn"].sum()),
                mm2inch(gdf["maxr"].max()),
                mm2inch(gdf["pcpn"].max()),
                len(gdf[gdf["pcpn"] > 0].index),
                len(gdf[gdf["maxr"] > 25.4].index),
                gdf["rad"].mean(),
            )
        )

    print("---- Months with < 0.05 precipitation ----")
    gdf = df.groupby(by=[df.index.year, df.index.month])["pcpn"].sum()
    print(gdf[gdf < 1.0])

    print("----- Average high temperature -----")
    print("YEAR | Avg High F | Avg Low F | Days > 100F")
    print(" --- | --- | --- | ---")
    for _year, gdf in df.groupby(by=df.index.year):
        print(
            ("%s | %6.2f | %6.2f | %3i")
            % (
                _year,
                c2f(gdf["tmax"].mean()),
                c2f(gdf["tmin"].mean()),
                len(gdf[gdf["tmax"] > 37.7].index),
            )
        )

    monthly = df[df.index.year == year]["pcpn"].resample("ME").sum().copy()
    monthly = pd.DataFrame(
        {"dep": mm2inch(monthly.values)},
        index=range(1, len(monthly.values) + 1),
    )

    # Get prism, for a bulk comparison
    prism = requests.get(
        (
            "http://mesonet.agron.iastate.edu/json/prism.py?"
            "lon=%.2f&lat=%.2f&sdate=%s-01-01&edate=%s"
        )
        % (lon, lat, year, min(LDATE, f"{year}-12-31"))
    ).json()
    rows = []
    for entry in prism["data"]:
        rows.append(
            {
                "date": datetime.datetime.strptime(
                    entry["valid"][:10], "%Y-%m-%d"
                ),
                "precip": entry["precip_in"],
            }
        )
    prismdf = pd.DataFrame(rows)
    prismdf = prismdf.set_index("date")
    monthly["prism"] = prismdf["precip"].resample("ME").sum().copy().values

    # Compare daily values
    iemjson = requests.get(
        (
            "http://mesonet.agron.iastate.edu/iemre/multiday/"
            "%s-01-01/%s/%s/%s/json"
        )
        % (year, min(LDATE, f"{year}-12-31"), lat, lon)
    ).json()
    rows = []
    for entry in iemjson["data"]:
        rows.append(
            {
                "date": datetime.datetime.strptime(entry["date"], "%Y-%m-%d"),
                "precip": entry["daily_precip_in"],
            }
        )
    iemdf = pd.DataFrame(rows)
    iemdf = iemdf.set_index("date")
    print(f"{year} Overall totals")
    print(f"PRISM precip is: {prismdf['precip'].sum():.2f}")
    print(f"IEMRE precip is: {iemdf['precip'].sum():.2f}")
    print(f"StageIV precip is: {stage4['precip'].sum():.2f}")
    ldate = f"{year}-12-31"
    today = (datetime.date.today() - datetime.timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )
    ldate = min(ldate, today)
    thisyear = df.loc[slice(f"{year}-01-01", ldate)]
    print(f"DEP precip is: {thisyear['pcpn_in'].sum():.2f}")
    monthly["stage4"] = stage4["precip"].resample("ME").sum().copy().values
    monthly["iemre"] = iemdf["precip"].resample("ME").sum().copy().values
    monthly["prism-dep"] = monthly["prism"] - monthly["dep"]
    monthly["iemre-dep"] = monthly["iemre"] - monthly["dep"]

    print(" --------- %s Monthly Totals --------" % (year,))
    print(monthly)
    df.at[
        slice(f"{year}-01-01", ldate),
        "stage4_precip",
    ] = stage4["precip"].values
    df["iemre_precip"] = iemdf["precip"]
    df["diff_precip"] = df["pcpn_in"] - df["iemre_precip"]
    df["diff_stage4"] = df["pcpn_in"] - df["stage4_precip"]
    print(" --- Top 5 Largest DEP > IEMRE ----")
    print(
        df[
            [
                "diff_precip",
                "pcpn_in",
                "iemre_precip",
                "stage4_precip",
                "diff_stage4",
            ]
        ]
        .sort_values(by="diff_precip", ascending=False)
        .head()
    )
    print(" --- Top 5 Largest IEMRE > DEP ----")
    print(
        df[
            [
                "diff_precip",
                "pcpn_in",
                "iemre_precip",
                "stage4_precip",
                "diff_stage4",
            ]
        ]
        .sort_values(by="diff_precip", ascending=True)
        .head()
    )

    print(" --- Top 10 Largest Stage4 > DEP ----")
    print(
        df[
            [
                "diff_precip",
                "pcpn_in",
                "iemre_precip",
                "stage4_precip",
                "diff_stage4",
            ]
        ]
        .sort_values(by="diff_stage4", ascending=True)
        .head(10)
    )
    print(" vvv job listing based on the above vvv")
    for dt in df.sort_values(by="diff_stage4", ascending=True).head(10).index:
        print(f"python proctor_tile_edit.py -s 0 --date={dt:%Y-%m-%d}")
    df2 = df.loc[slice(datetime.date(year, 1, 1), datetime.date(year, 1, 31))][
        ["diff_precip", "pcpn_in", "iemre_precip", "stage4_precip"]
    ].sort_values(by="diff_precip")
    print(" --- Daily values for month ")
    print(df2)


def main(argv):
    """Do Stuff"""
    fn = argv[1]
    year = int(argv[2])
    df = read_cli(fn).loc[:LDATE]
    df["pcpn_in"] = mm2inch(df["pcpn"].values)
    do_qc(fn, df, year)


if __name__ == "__main__":
    main(sys.argv)
