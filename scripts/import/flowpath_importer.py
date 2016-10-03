"""
We need to process the DBF files Brian provides, please!

smpl102802010406.dbf

  fp10280201
  X             5070
  Y             5070
  POINT_X       4326
  POINT_Y       4326
  ec3m102802    elevation in cm
  fpLen10280    flow path length in cm
  GenLU10280    land use code
  gSSURGO       soils code
"""

import dbflib
import glob
import os
import pandas as pd
from pandas import Series
import psycopg2
import datetime
import sys

SCENARIO = int(sys.argv[1])

PGCONN = psycopg2.connect(database='idep', host='iemdb')
cursor = PGCONN.cursor()


def get_flowpath(huc12, fpath):
    cursor.execute("""
    SELECT fid from flowpaths where huc_12 = %s and fpath = %s
    and scenario = %s
    """, (huc12, fpath, SCENARIO))
    if cursor.rowcount == 0:
        cursor.execute("""
        INSERT into flowpaths(huc_12, fpath, scenario)
        values (%s, %s, %s) RETURNING fid
        """, (huc12, fpath, SCENARIO))
    return cursor.fetchone()[0]


def get_data(fn):
    ''' Load a DBF file into a pandas DF '''
    rows = []
    dbf = dbflib.open(fn)
    for i in range(dbf.record_count()):
        rows.append(dbf.read_record(i))

    return pd.DataFrame(rows)


def process(fn, df):
    '''Process a given filename into the database '''
    huc12 = fn[4:-4]
    huc8 = huc12[:-4]
    prefix = 'g4'
    flowpaths = Series(df['%s%s' % (prefix, huc8)]).unique()
    flowpaths.sort()
    for flowpath in flowpaths:
        # never do flowpath zero!
        if flowpath == 0:
            continue
        df2 = df[df['%s%s' % (prefix, huc8)] == flowpath]
        df2 = df2.sort_values('%sLen%s' % (prefix, huc8[:5]), ascending=True)
        fid = get_flowpath(huc12, flowpath)
        cursor.execute("""DELETE from flowpath_points WHERE flowpath = %s
            and scenario = %s""",
                       (fid, SCENARIO))
        lstring = []
        sz = len(df2.index)
        for segid, row in enumerate(df2.iterrows()):
            row = df2.iloc[segid]
            if (segid+1) == sz:  # Last row!
                row2 = df2.iloc[segid-1]
            else:
                row2 = df2.iloc[segid+1]
            dy = row['ep3m%s' % (huc8[:6],)] - row2['ep3m%s' % (huc8[:6],)]
            dx = (row2['%sLen%s' % (prefix, huc8[:5])] -
                  row['%sLen%s' % (prefix, huc8[:5])])
            if dx == 0:
                slope = 0
            else:
                slope = dy/dx
            lu = row['CropRotatn'].strip()
            # print "%3s %7.1f %7.1f %7.4f %s" % (segid, dx, dy, slope, lu)
            if lu == "":
                lu = [None, ] * 8
            sql = """INSERT into flowpath_points(flowpath, segid,
                elevation, length,  surgo, management, slope, geom,
                lu2007, lu2008, lu2009, lu2010, lu2011, lu2012, lu2013,
                lu2014, lu2015, lu2016, scenario)
                values(%s, %s , %s,
                %s, %s, %s, %s, 'SRID=5070;POINT(%s %s)',
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """
            # OK, be careful here.  the landuse codes start in 2008 as there
            # is no national coverage in 2007.  So for 2007, we will repeat
            # the value for 2009.
            # no 2016 data, so repeat 2014 value
            args = (fid, segid, row['ep3m%s' % (huc8[:6],)]/100.,
                    row['%sLen%s' % (prefix, huc8[:5])]/100.,
                    row['gSSURGO'], row['Management'], slope, row['X'],
                    row['Y'], lu[1], lu[0], lu[1], lu[2],
                    lu[3], lu[4], lu[5], lu[6], lu[7], lu[6],
                    SCENARIO)
            cursor.execute(sql, args)

            lstring.append("%s %s" % (row['X'], row['Y']))

        if len(lstring) > 1:
            sql = """UPDATE flowpaths SET geom = 'SRID=5070;LINESTRING(%s)'
                WHERE fid = %s and scenario = %s""" % (",".join(lstring), fid,
                                                       SCENARIO)
            cursor.execute(sql)
        else:
            print(('---> ERROR: %s flowpath %s < 2 points, deleting'
                   ) % (fn, flowpath))
            cursor.execute("""DELETE from flowpath_points
                where flowpath = %s and scenario = %s""", (fid, SCENARIO))
            cursor.execute("""DELETE from flowpaths where fid = %s
                and scenario = %s""", (fid, SCENARIO))


def main():
    """ Lets go main go """
    os.chdir("../../data/%s" % (sys.argv[2],))
    fns = glob.glob("*.dbf")
    total = len(fns)
    for i, fn in enumerate(fns):
        sts = datetime.datetime.now()
        if i > 0 and i % 100 == 0:
            PGCONN.commit()
            cursor = PGCONN.cursor()
        df = get_data(fn)
        process(fn, df)
        ets = datetime.datetime.now()
        secs = (ets - sts).microseconds / 100000. + (ets - sts).seconds
        print '%4i/%4i %7.3fs %s' % (i+1, total, secs, fn)

    # cursor.close()
    PGCONN.commit()

if __name__ == '__main__':
    main()
