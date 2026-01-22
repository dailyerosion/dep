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

import geopandas as gpd
import numpy as np
import pandas as pd
from pyiem.database import get_dbconn
from pyiem.util import logger

LOG = logger()
print(" * BE CAREFUL!  The GeoJSON files may not be 5070, but 26915")
print(" * VERIFY that the GeoJSON is the 5070 grid value")
print(" * This will generate a `myhucs.txt` file with found HUCs")

SCENARIO = int(sys.argv[1])
PREFIX = "fp"

PGCONN = get_dbconn("idep")
INSERT_SQL = """
    INSERT into flowpath_points(flowpath, segid,
    elevation, length,  surgo, management, slope, geom,
    landuse, scenario, gridorder)
    values(%s, %s, %s, %s, %s, %s, %s, 'SRID=5070;POINT(%s %s)',
    %s, %s, %s)
"""


def get_flowpath(cursor, huc12, fpath):
    """Get or create a database flowpath identifier

    Args:
      cursor (psycopg.cursor): database cursor
      huc12 (str): HUC12 identifier
      fpath (int): the flowpath id value for this HUC12

    Returns:
      int the value of this huc12 flowpath
    """
    cursor.execute(
        """
        SELECT fid from flowpaths where huc_12 = %s and fpath = %s
        and scenario = %s
    """,
        (huc12, fpath, SCENARIO),
    )
    if cursor.rowcount == 0:
        cursor.execute(
            """
            INSERT into flowpaths(huc_12, fpath, scenario)
            values (%s, %s, %s) RETURNING fid
        """,
            (huc12, fpath, SCENARIO),
        )
    return cursor.fetchone()[0]


def run_checks(df):
    """Do some sanity checks."""
    # Find flowpath column
    fpcol = [x for x in df.columns if x.startswith("fp")][0]
    gordcol = [x for x in df.columns if x.startswith("gord")][0]
    fplencol = [x for x in df.columns if x.startswith("fpLen")][0]
    gdf = df.groupby(fpcol).agg([np.min, np.max])
    # collapse multiindex
    gdf.columns = list(map("".join, gdf.columns.values))
    # Check that grid order starts at 1 and goes to at least 5
    df2 = gdf[(gdf[f"{gordcol}amin"] > 1) | (gdf[f"{gordcol}amax"] < 5)]
    cull = []
    if not df2.empty:
        for fpath, row in df2.iterrows():
            print(
                "GORDER_CHECK FAIL %s %s min:%s max:%s, culling"
                % (
                    gordcol,
                    fpath,
                    row[f"{gordcol}amin"],
                    row[f"{gordcol}amax"],
                )
            )
            cull.append(fpath)
    # Check that fpLen is monotonic
    for fpath, gdf in df.groupby(fpcol):
        res = gdf[fplencol].values[1:] - gdf[fplencol].values[:-1]
        if not all(res > 0):
            print(
                "FPLEN %s for %s not monotonic, culling %s"
                % (fplencol, fpath, min(res))
            )
            cull.append(fpath)

    if cull:
        print("culling %s" % (cull,))
        df = df[~df[fpcol].isin(cull)]
    return df


def get_data(filename):
    """Converts a GeoJSON file into a pandas dataframe

    Args:
      filename (str): The geojson filename to process

    Returns:
      gpd.DataFrame with the geojson data included.
    """
    df = gpd.read_file(filename, index="OBJECTID")
    # Sort along the length column, which orders the points from top
    # to bottom
    fplencol = [x for x in df.columns if x.startswith("fpLen")][0]
    df = df.sort_values(fplencol, ascending=True)
    df = run_checks(df)
    snapdf = gpd.read_file(
        filename.replace("smpldef3m", "snaps3m"), index="OBJECTID"
    )
    # Compute full rotation string
    # OK, be careful here. Presently, the 8 char field covers
    # 2010 thru 2017, so we rotate to cover the first and last years
    # 2007 2011[1]
    # 2008 2010[0]
    # 2009 2011[1]
    # 2018 2016[6]
    # 2019 2017[7]
    # 2020 2018[6]
    s = df["CropRotatn_CY_2017"]
    df["landuse"] = (
        s.str[1]
        + s.str[0]
        + s.str[1]
        + s
        + s.str[6]
        + s.str[7]
        + s.str[6]
        + s.str[7]
    )
    s = df["Management_CY_2017"]
    df["management"] = (
        s.str[1]
        + s.str[0]
        + s.str[1]
        + s
        + s.str[6]
        + s.str[7]
        + s.str[6]
        + s.str[7]
    )
    return df, snapdf


def delete_previous(cursor, huc12):
    """This file is the authority for the HUC12."""
    cursor.execute(
        """
        DELETE from flowpath_points p USING flowpaths f WHERE
        p.scenario = %s and p.flowpath = f.fid and f.huc_12 = %s
        and f.scenario = %s
    """,
        (SCENARIO, huc12, SCENARIO),
    )
    cursor.execute(
        """
        DELETE from flowpaths WHERE
        scenario = %s and huc_12 = %s
    """,
        (SCENARIO, huc12),
    )


def truncation_logic(df, snappt, lencolname, gordcolname, elevcolname):
    """Figure out where to stop this flowpath."""
    df["distance"] = df["geometry"].distance(snappt["geometry"])
    # 91 gully head
    # 98 Gulley Head -10m
    # 99 Gulley Head +10m
    # 100 Gulley Head -20m
    # 101 Gulley Head +20m
    offsets = {91: 0, 98: -10, 99: 10, 100: -20, 101: 20}
    # 93 Gorder 2
    # 94 Gorder 3
    # 95 Gorder 4
    # 96 Gorder 5
    # 97 Gorder 6
    gords = {93: 2, 94: 3, 95: 4, 96: 5, 97: 6}
    if SCENARIO in offsets:
        # Find Gulley head row, the value 9 is arb to account for a quirk
        # with one of the HUC12s
        df2 = df[df["distance"] < 9]
        if df2.empty:
            print(f"Min distance is {df['distance'].min()}")
            raise Exception("failed to find closest point to flowpath")
        df2 = df2.sort_values("distance", ascending=True)
        gulleyhead = df2.iloc[0]
        # What is the distance along the flowpath this is
        # What's the threshold this scenario mandates (in cm)
        fplen = gulleyhead[lencolname] + offsets[SCENARIO] * 100.0
        df = df[df[lencolname] <= fplen]
    elif SCENARIO in gords:
        if df[gordcolname].min() != 1:
            LOG.info(
                "%s flowpath %s gridorder min is not 1, but %s, aborting",
                elevcolname.replace("ep3m", ""),
                df[elevcolname.replace("ep3m", "fp")].values[0],
                df[gordcolname].min(),
            )
            sys.exit()
        df = df[df[gordcolname] < gords[SCENARIO]]
    # 92 Dynamic 3-4
    elif SCENARIO == 92:
        # Check the slope at the GORDER 3 to 4 transition, if > 10% stop
        # else go to GORDER 4
        df2 = df[df[gordcolname] < 3]
        # A quick jumper to 3
        if len(df2.index) == 1:
            df2 = df.iloc[:2]
        dx = df2[lencolname].values[-1] - df2[lencolname].values[-2]
        dy = df2[elevcolname].values[-2] - df2[elevcolname].values[-1]
        slope = dy / dx
        if slope < 0.1:
            df = df[df[gordcolname] < 4]
        else:
            df = df2

    if df.empty:
        raise Exception("truncation resulted in empty flowpath.")
    return df


def process_flowpath(cursor, huc12, db_fid, df, snappt):
    """Do one flowpath please."""
    lencolname = "%sLen%s" % (PREFIX, huc12)
    elevcolname = "ep3m%s" % (huc12,)
    gordcolname = "gord_%s" % (huc12,)
    # Remove any previous data for this flowpath
    cursor.execute(
        "DELETE from flowpath_points WHERE flowpath = %s", (db_fid,)
    )
    linestring = []
    sz = len(df.index)
    maxslope = 0
    elev_change = 0
    x_change = 0
    truncated_df = truncation_logic(
        df, snappt, lencolname, gordcolname, elevcolname
    )
    for segid, (_idx, row) in enumerate(truncated_df.iterrows()):
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
            print(huc12)
            print(
                df[["OBJECTID", elevcolname, lencolname, gordcolname]].head(10)
            )
            sys.exit()
        x_change += dx
        gridorder = row[gordcolname]
        slope = dy / dx

        if slope > maxslope:
            maxslope = slope
        args = (
            db_fid,
            segid,
            row[elevcolname] / 100.0,
            row[lencolname] / 100.0,
            row["SOL_FY_2018"],
            row["management"],
            slope,
            row["geometry"].x,
            row["geometry"].y,
            row["landuse"],
            SCENARIO,
            gridorder,
        )
        cursor.execute(INSERT_SQL, args)

        linestring.append("%s %s" % (row["geometry"].x, row["geometry"].y))

    # Line string must have at least 2 points
    if len(linestring) > 1:
        if x_change == 0:
            print()
            print(df)
            sys.exit()
        sql = """
            UPDATE flowpaths SET geom = 'SRID=5070;LINESTRING(%s)',
            max_slope = %s, bulk_slope = %s
            WHERE fid = %s
        """ % (
            ",".join(linestring),
            maxslope,
            elev_change / x_change,
            db_fid,
        )
        cursor.execute(sql)
    else:
        # Cull our work above if this flowpath is too short
        delete_flowpath(cursor, db_fid)


def delete_flowpath(cursor, fid):
    """Delete the flowpath."""
    cursor.execute("DELETE from flowpath_points where flowpath = %s", (fid,))
    cursor.execute("DELETE from flowpaths where fid = %s", (fid,))


def process(cursor, filename, huc12df, snapdf):
    """Processing of a HUC12's data into the database

    Args:
      cursor (psycopg.cursor): database cursor
      filename (str): the geojson filename
      huc12df (pd.DataFrame): the dataframe containing the data

    Returns:
      None
    """
    # We get the huc12 code based on the filename
    huc12 = filename.split(".")[0].split("_")[-1][-12:]

    delete_previous(cursor, huc12)
    # the inbound dataframe has lots of data, one row per flowpath point
    # We group the dataframe by the column which uses a PREFIX and the huc8
    for flowpath_num, df in huc12df.groupby(f"fp{huc12}"):
        snappt = snapdf[snapdf["grid_code"] == flowpath_num].iloc[0]
        # These are upstream errors I should ignore
        if flowpath_num == 0 or len(df.index) < 2:
            continue
        # Get or create the flowpathid from the database
        db_fid = get_flowpath(cursor, huc12, flowpath_num)
        try:
            process_flowpath(cursor, huc12, db_fid, df, snappt)
        except Exception as exp:
            LOG.info(
                "huc12: %s flowpath_num: %s hit exception", huc12, flowpath_num
            )
            LOG.exception(exp)
            delete_flowpath(cursor, db_fid)
            print(df)
            print(df[[f"gord_{huc12}", f"fpLen{huc12}"]])
    return huc12


def main():
    """Our main function, the starting point for code execution"""
    cursor = PGCONN.cursor()
    # track our work
    with open("myhucs.txt", "w") as fh:
        # Change the working directory to where we have data files
        os.chdir("../../data/%s" % (sys.argv[2],))
        # collect up the GeoJSONs in that directory
        fns = glob.glob("smpldef3m_*.json")
        fns.sort()
        i = 0

        for fn in fns:
            # Save our work every 100 HUC12s,
            # so to keep the database transaction
            # at a reasonable size
            if i > 0 and i % 100 == 0:
                PGCONN.commit()
                cursor = PGCONN.cursor()
            df, snapdf = get_data(fn)
            huc12 = process(cursor, fn, df, snapdf)
            fh.write("%s\n" % (huc12,))
            i += 1

    # Commit the database changes
    cursor.close()
    PGCONN.commit()
    LOG.info("Complete.")


if __name__ == "__main__":
    main()
