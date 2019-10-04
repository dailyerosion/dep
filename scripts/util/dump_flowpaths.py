"""Dump flowpaths to a shapefile."""

from geopandas import read_postgis
from pyiem.util import get_dbconn


def main():
    """Go Main Go."""
    pgconn = get_dbconn('idep')
    df = read_postgis("""
        SELECT f.fpath, f.huc_12, ST_Transform(f.geom, 4326) as geo from
        flowpaths f, huc12 h WHERE h.scenario = 0 and f.scenario = 0
        and h.huc_12 = f.huc_12 and h.states ~* 'IA'
    """, pgconn, index_col=None, geom_col='geo')
    df.to_file("ia_flowpaths.shp")


if __name__ == '__main__':
    main()
