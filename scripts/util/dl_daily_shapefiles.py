"""Example script to download daily shapefiles from the dailyerosion site"""

import datetime

import requests


def main():
    """Go Main Go."""
    start_time = datetime.date(2007, 1, 1)
    end_time = datetime.date(2015, 9, 8)
    interval = datetime.timedelta(days=1)

    now = start_time
    while now < end_time:
        print("Downloading shapefile for %s" % (now.strftime("%d %b %Y"),))
        uri = ("https://dailyerosion.org/dl/shapefile.py?dt=%s") % (
            now.strftime("%Y-%m-%d"),
        )
        fn = "dep%s.zip" % (now.strftime("%Y%m%d"),)
        req = requests.get(uri)
        with open(fn, "wb") as fp:
            fp.write(req.content)
        now += interval


if __name__ == "__main__":
    main()
