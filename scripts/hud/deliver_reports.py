"""Generate and upload DEP reports."""

from pandas.io.sql import read_sql
import geopandas as gpd
import requests
from pyiem.util import get_dbconn
from pyiem.box_utils import sendfiles2box

LOOKUP = {
    "10240003": "East Nishnabotna River",
    "07080205": "Middle Cedar River",
    "07100006": "North Raccoon River",
    "07060002": "Upper Iowa River",
    "07080102": "Upper Wapsipinicon River",
    "10240002": "West Nishnabotna River",
}


def build_xref():
    """Figure out which HUC12s we need and where to file them."""
    xref = {}
    # exporthucs can use the LOOKUP
    df = gpd.read_file('exporthucs.shp')
    for _i, row in df.iterrows():
        huc8 = row['HUC_12'][:8]
        # A misfire of some HUCs in South Dakota
        if huc8 not in LOOKUP:
            continue
        refs = xref.setdefault(LOOKUP[huc8], [])
        refs.append(row['HUC_12'])

    # English River
    df = gpd.read_file('english.shp')
    for _i, row in df.iterrows():
        refs = xref.setdefault('English River', [])
        refs.append(row['HUC_12'])

    # Clear Creek
    xref['Clear Creek'] = ['070802090101', '070802090102', '070802090103']
    # TODO Dubuque and Bee Branch Creek
    return xref


def workflow(name, hucs):
    """Do our processing please."""
    # Construct the lookup table
    pgconn = get_dbconn('idep')
    df = read_sql("""
    select huc_12, hu_12_name from huc12 where scenario = 0
    and huc_12 in %s
    """, pgconn, params=(tuple(hucs), ), index_col='huc_12')
    filenames = []
    for huc in hucs:
        if huc not in df.index.values:
            print("Huc: %s is unknown to DEP" % (huc, ))
            continue
        uri = "http://dailyerosion.local/auto/huc12report.py?huc=%s" % (huc,)
        req = requests.get(uri)
        if req.status_code != 200:
            print("Uri: %s failed with: %s" % (uri, req.status_code))
            continue
        fn = "%s-%s.pdf" % (huc, df.at[huc, 'hu_12_name'].replace(" ", "_"))
        fp = open(fn, 'wb')
        fp.write(req.content)
        fp.close()
        filenames.append(fn)

    res = sendfiles2box(
        "Iowa Watershed Approach - Daily Erosion Project/%s" % (name, ),
        filenames, overwrite=True
    )
    for retval, fn in zip(res, filenames):
        if retval is None:
            print("%s failed to upload." % (fn, ))


def main():
    """Go Main Go."""
    xref = build_xref()
    for name, hucs in xref.items():
        workflow(name, hucs)


if __name__ == '__main__':
    main()
