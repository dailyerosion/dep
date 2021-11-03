"""Process provided GeoJSON files into the database.

Brian Gelder provides me some archive of processed HUC12s, this archive is
dumped to disk and then glob'd by this script.  It then creates a `myhucs.txt`
file, which provides the downstream scripts the data domain to limit processing
to.

    python flowpath_importer.py <scenario> <path to geojsons in ../../data/>

"""
import glob
import os
import sys

from tqdm import tqdm
from shapely.geometry import LineString
import geopandas as gpd
import pandas as pd
from pyiem.util import get_dbconn, logger

LOG = logger()
print(" * BE CAREFUL!  The GeoJSON files may not be 5070, but 26915")
print(" * VERIFY that the GeoJSON is the 5070 grid value")
print(" * This will generate a `myhucs.txt` file with found HUCs")

PREFIX = "fp"
TRUNC_GRIDORDER_AT = 4
GENLU_CODES = {}


def get_flowpath(cursor, scenario, huc12, fpath):
    """Get or create a database flowpath identifier

    Args:
      cursor (psycopg2.cursor): database cursor
      huc12 (str): HUC12 identifier
      fpath (int): the flowpath id value for this HUC12

    Returns:
      int the value of this huc12 flowpath
    """
    cursor.execute(
        "SELECT fid from flowpaths where huc_12 = %s and fpath = %s "
        "and scenario = %s",
        (huc12, fpath, scenario),
    )
    if cursor.rowcount == 0:
        cursor.execute(
            "INSERT into flowpaths(huc_12, fpath, scenario) "
            "values (%s, %s, %s) RETURNING fid",
            (huc12, fpath, scenario),
        )
    return cursor.fetchone()[0]


def get_data(filename):
    """Converts a GeoJSON file into a pandas dataframe

    Args:
      filename (str): The geojson filename to process

    Returns:
      gpd.DataFrame with the geojson data included.
    """
    df = gpd.read_file(filename, index="OBJECTID")
    # Compute full rotation string
    # TODO - wrong label, 2010-2020 period
    s = df["CropRotatn_CY_2019"]
    df["landuse"] = (
        s.str[1] + s.str[0] + s.str[1] + s + s.str[-2]  # 2010  # 2021
    )
    s = df["Management_CY_2020"]
    df["management"] = s.str[1] + s.str[0] + s.str[1] + s + s.str[-2]  # 2010
    return df


def delete_previous(cursor, scenario, huc12):
    """This file is the authority, so we cull previous content."""
    cursor.execute(
        "DELETE from flowpath_points p USING flowpaths f WHERE "
        "p.scenario = %s and p.flowpath = f.fid and f.huc_12 = %s "
        "and f.scenario = %s",
        (scenario, huc12, scenario),
    )
    cursor.execute(
        "DELETE from flowpaths WHERE scenario = %s and huc_12 = %s",
        (scenario, huc12),
    )


def load_genlu_codes(cursor):
    """Populate dict."""
    cursor.execute("SELECT id, label from general_landuse")
    for row in cursor:
        GENLU_CODES[row[1]] = row[0]


def get_genlu_code(cursor, label):
    """Find or create the code for this label."""
    if label not in GENLU_CODES:
        cursor.execute("SELECT max(id) from general_landuse")
        row = cursor.fetchone()
        newval = 0 if row[0] is None else row[0] + 1
        LOG.debug("Inserting new general landuse code: %s [%s]", newval, label)
        cursor.execute(
            "INSERT into general_landuse(id, label) values (%s, %s)",
            (newval, label),
        )
        GENLU_CODES[label] = newval
    return GENLU_CODES[label]


def process_flowpath(cursor, scenario, huc12, db_fid, df):
    """Do one flowpath please."""
    lencolname = f"{PREFIX}Len{huc12}"
    elevcolname = f"ep3m{huc12}"
    gordcolname = f"gord_{huc12}"
    # Sort along the length column, which orders the points from top
    # to bottom
    df = df.sort_values(lencolname, ascending=True)
    # Remove any previous data for this flowpath
    cursor.execute(
        "DELETE from flowpath_points WHERE flowpath = %s", (db_fid,)
    )
    points = []
    sz = len(df.index)
    maxslope = 0
    elev_change = 0
    x_change = 0
    for segid, (_, row) in enumerate(df.iterrows()):
        if (segid + 1) == sz:  # Last row!
            # This effectively repeats the slope of the previous point
            row2 = df.iloc[segid - 1]
        else:
            row2 = df.iloc[segid + 1]
            if pd.isna(row2[lencolname]):
                print("Null fpLen")
                print(row2)
                sys.exit()
        dy = abs(row[elevcolname] - row2[elevcolname])
        elev_change += dy
        dx = abs(row2[lencolname] - row[lencolname])
        if dx == 0:
            raise Exception(f"dx is zero at segid: {segid} {row} {row2}")
        x_change += dx
        gridorder = row[gordcolname]
        if gridorder > TRUNC_GRIDORDER_AT or pd.isnull(gridorder):
            continue
        slope = dy / dx

        if slope > maxslope:
            maxslope = slope
        args = (
            db_fid,
            segid,
            row[elevcolname] / 100.0,
            row[lencolname] / 100.0,
            row["SOL_FY_2020"],
            row["management"],
            slope,
            row["geometry"].x,
            row["geometry"].y,
            row["landuse"],
            scenario,
            gridorder,
            get_genlu_code(cursor, row["GenLU"]),
            row["FBndID"].split("_")[1],
        )
        cursor.execute(
            "INSERT into flowpath_points(flowpath, segid, elevation, length, "
            "surgo, management, slope, geom, landuse, scenario, gridorder, "
            "genlu, fbndid) "
            "values(%s, %s, %s, %s, %s, %s, %s, 'SRID=5070;POINT(%s %s)', "
            "%s, %s, %s, %s, %s)",
            args,
        )

        points.append((row["geometry"].x, row["geometry"].y))

    # Line string must have at least 2 points
    if len(points) > 1:
        ls = LineString(points)
        assert ls.is_valid
        if x_change == 0:
            print("x_change equals 0, abort")
            print(df)
            sys.exit()
        cursor.execute(
            "UPDATE flowpaths SET geom = %s, "
            "max_slope = %s, bulk_slope = %s WHERE fid = %s",
            (f"SRID=5070;{ls.wkt}", maxslope, elev_change / x_change, db_fid),
        )
    else:
        # Cull our work above if this flowpath is too short
        delete_flowpath(cursor, db_fid)


def delete_flowpath(cursor, fid):
    """Delete the flowpath."""
    cursor.execute("DELETE from flowpath_points where flowpath = %s", (fid,))
    cursor.execute("DELETE from flowpaths where fid = %s", (fid,))


def process(cursor, scenario, huc12df):
    """Processing of a HUC12's data into the database

    Args:
      cursor (psycopg2.cursor): database cursor
        scenario (int): the scenario to process
      huc12df (pd.DataFrame): the dataframe containing the data

    Returns:
      None
    """
    # Hack compute the huc12 by finding the fp field name
    huc12 = None
    for col in huc12df.columns:
        if col.startswith(PREFIX):
            huc12 = col[len(PREFIX) :]
            break
    if huc12 is None:
        raise Exception(f"Could not find huc12 from {huc12df.columns}")

    delete_previous(cursor, scenario, huc12)
    # the inbound dataframe has lots of data, one row per flowpath point
    # We group the dataframe by the column which uses a PREFIX and the huc8
    for flowpath_num, df in huc12df.groupby(f"{PREFIX}{huc12}"):
        # These are upstream errors I should ignore
        if flowpath_num == 0 or len(df.index) < 2:
            continue
        # Get or create the flowpathid from the database
        db_fid = get_flowpath(cursor, scenario, huc12, flowpath_num)
        try:
            process_flowpath(cursor, scenario, huc12, db_fid, df)
        except Exception as exp:
            LOG.info("flowpath_num: %s hit exception", flowpath_num)
            LOG.exception(exp)
            delete_flowpath(cursor, db_fid)
            # print(df)
            # sys.exit()
    return huc12


def main(argv):
    """Our main function, the starting point for code execution"""
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()
    load_genlu_codes(cursor)
    scenario = int(argv[1])
    # track our work
    with open("myhucs.txt", "w", encoding="utf8") as fh:
        datadir = os.path.join("..", "..", "data", argv[2])
        # collect up the GeoJSONs in that directory
        fns = glob.glob(f"{datadir}/smpl3m_*.json")
        fns.sort()
        i = 0

        progress = tqdm(fns)
        for fn in progress:
            progress.set_description(os.path.basename(fn))
            # Save our work every 100 HUC12s,
            # so to keep the database transaction
            # at a reasonable size
            if i > 0 and i % 100 == 0:
                pgconn.commit()
                cursor = pgconn.cursor()
            df = get_data(fn)
            huc12 = process(cursor, scenario, df)
            fh.write(f"{huc12}\n")
            i += 1

    # Commit the database changes
    cursor.close()
    pgconn.commit()


if __name__ == "__main__":
    main(sys.argv)
