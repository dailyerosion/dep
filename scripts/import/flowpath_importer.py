'''
We need to process the DBF files Brian provides, please!

smpl102802010406.dbf

  fp10280201                   
  X             26915      
  Y             26915
  ec3m102802    elevation in cm 
  fpLen10280    flow path length in cm
  GenLU10280    land use code
  gSSURGO       soils code

'''

import dbflib
import glob
import os
import pandas as pd
from pandas import Series
import psycopg2
import datetime

PGCONN = psycopg2.connect(database='idep', host='iemdb')
cursor = PGCONN.cursor()

def get_flowpath(huc12, fpath):
    cursor.execute("""
    SELECT fid from flowpaths where huc_12 = %s and fpath = %s
    """, (huc12, fpath))
    if cursor.rowcount == 0:
        cursor.execute("""
        INSERT into flowpaths(huc_12, fpath) values (%s, %s) RETURNING fid
        """, (huc12, fpath))
    return cursor.fetchone()[0]    

def get_data(fn):
    ''' Load a DBF file into a pandas DF '''
    rows = []
    dbf = dbflib.open(fn)
    for i in range(dbf.record_count()):
        rows.append( dbf.read_record(i) )
    
    return pd.DataFrame(rows)

def process(fn, df):
    '''Process a given filename into the database '''
    huc12 = fn[4:-4]
    huc8 = huc12[:-4]
    flowpaths = Series(df['fp%s' % (huc8,)]).unique()
    flowpaths.sort()
    for flowpath in flowpaths:
        df2 = df[df['fp%s' % (huc8,)]==flowpath]
        df2 = df2.sort('fpLen%s' % (huc8[:5],), ascending=True)
        fid = get_flowpath(huc12, flowpath)
        cursor.execute("""DELETE from flowpath_points WHERE flowpath = %s""",
                       (fid,))
        lstring = []
        sz = len(df2.index)
        for segid, row in enumerate(df2.iterrows()):
            row = df2.irow(segid)
            if (segid+1) == sz: # Last row!
                row2 = df2.irow(segid-1)
            else:
                row2 = df2.irow(segid+1)
            dy = row['ec3m%s' % (huc8[:6],)] - row2['ec3m%s' % (huc8[:6],)]
            dx =  row2['fpLen%s' % (huc8[:5],)] - row['fpLen%s' % (huc8[:5],)]
            if dx == 0:
                slope = 0
            else:
                slope = dy/dx
            lu = row['CropRotatn']
            if lu.strip() == "":
                lu = [None, None, None, None, None, None]
            sql = """INSERT into flowpath_points(flowpath, segid, 
                elevation, length,  surgo, management, slope, geom,
                landuse1, landuse2, landuse3, landuse4, landuse5, landuse6) 
                values(%s, %s , %s,
                %s, %s, %s, %s, 'SRID=26915;POINT(%s %s)',
                %s, %s, %s, %s, %s, %s);
                """ 
            args = (fid, segid,  
                       row['ec3m%s' % (huc8[:6],)]/100.,
               row['fpLen%s' % (huc8[:5],)]/100., 
                row['gSSURGO'], 
               row['Management'], slope, row['X'], 
               row['Y'], lu[0], lu[1], lu[2], 
               lu[3], lu[4], lu[5])
            cursor.execute(sql, args)
            
            lstring.append("%s %s" % (row['X'], row['Y']))
        
        if len(lstring) > 1:
            #print '%s %s Save flowpath %s GEOM, length %s' % (huc12, flowpath, fid, 
            #                                               len(lstring))
            sql = """UPDATE flowpaths SET geom = 'SRID=26915;LINESTRING(%s)' 
                WHERE fid = %s""" % (",".join(lstring), fid)
            cursor.execute(sql)
        else:
            print '---> ERROR: %s flowpath %s < 2 points, deleting' % (
                                                            fn, flowpath,)
            cursor.execute("""DELETE from flowpath_points 
                where flowpath = %s""", (fid,))
            cursor.execute("""DELETE from flowpaths where fid = %s""", (fid,))

if __name__ == '__main__':
    os.chdir("../../data/flowpaths")
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
        print '%4i/%4i %7.3fs %s' % (i+1, total, 
            (ets - sts).microseconds / 100000. + (ets - sts).seconds, fn)
    
    cursor.close()
    PGCONN.commit()
