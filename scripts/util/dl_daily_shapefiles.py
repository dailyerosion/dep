#!/usr/bin/env python
"""Example script to download daily shapefiles from the dailyerosion site"""
import datetime
import urllib2


start_time = datetime.date(2007, 1, 1)
end_time = datetime.date(2015, 9, 8)
interval = datetime.timedelta(days=1)

now = start_time
while now < end_time:
    print("Downloading shapefile for %s" % (now.strftime("%d %b %Y"),))
    uri = ("https://dailyerosion.org/dl/shapefile.py?dt=%s"
           ) % (now.strftime("%Y-%m-%d"), )
    fn = "dep%s.zip" % (now.strftime("%Y%m%d"), )
    o = open(fn, 'wb')
    o.write(urllib2.urlopen(uri).read())
    o.close()
    now += interval
