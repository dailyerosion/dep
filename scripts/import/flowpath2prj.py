'''Generate the WEPP prj files based on what our database has for us
'''
import psycopg2
import psycopg2.extras
import os
import copy
import sys
import datetime
from math import atan2, degrees, pi

PGCONN = psycopg2.connect(database='idep', host='iemdb')
cursor = PGCONN.cursor(cursor_factory=psycopg2.extras.DictCursor)
cursor2 = PGCONN.cursor(cursor_factory=psycopg2.extras.DictCursor)

surgo2file = {}
cursor.execute("""SELECT surgo, soilfile from xref_surgo""")
for row in cursor:
    surgo2file[ row[0] ] = row[1]

def get_rotation(code, maxmanagement):
    """ Convert complex things into a simple WEPP management for now """
    fn = "IDEP2/%s/%s/%s-%s.rot" % (code[:2], code[2:4], code,
                                    "1" if maxmanagement == 1 else "25")
    return fn

def compute_aspect(x0, y0, x1, y1):
    """ Compute the aspect angle between two points """
    dx = x1 - x0
    dy = y1 - y0
    rads = atan2(-dy,dx)
    rads %= 2*pi
    return degrees(rads)

def non_zero(dy,dx):
    """ Make sure slope is slightly non-zero """
    if dx == 0:
        return 0.00001
    return max(0.00001, dy/dx)

def simplify(rows):
    """ WEPP can only handle 20 slope points it seems, so we must simplify """
    newrows = []
    lrow = rows[0]
    newrows.append( lrow )
    for row in rows:
        # If they are the 'same', continue
        if row['lstring'] == 'UUUUUU':
            continue
        if (row['management'] == lrow['management'] and 
            row['surgo'] == lrow['surgo'] and
            row['lstring'] == lrow['lstring']):
            continue
        # Recompute slope
        dy = lrow['elevation'] - row['elevation']
        dx = row['length'] - lrow['length']
        row['slope'] = non_zero(dy,dx)
        newrows.append( copy.deepcopy(row) )
        lrow = row
        
    if newrows[-1]['segid'] != rows[-1]['segid']:
        # Recompute slope
        dy = newrows[-1]['elevation'] - rows[-1]['elevation']
        dx = rows[-1]['length'] - newrows[-1]['length']
        newrows.append( copy.deepcopy(rows[-1]) )
        newrows[-1]['slope'] = non_zero(dy,dx)
    
    if len(newrows) < 20:
        return newrows
    
    # Brute force!
    threshold = 0.01
    while len(newrows) > 19:
        newrows2 = []
        newrows2.append( copy.deepcopy(newrows[0]) )
        for i in range(1, len(newrows)-1):
            if newrows[i]['slope'] > threshold:
                newrows2.append( copy.deepcopy(newrows[i]) )
        newrows2.append( copy.deepcopy(newrows[-1]) )
        newrows = newrows2
        threshold += 0.01
 
    # TODO: recompute the slopes
 
    if len(newrows) > 19:
        print 'Length of old: %s' % (len(rows),)
        for row in rows:
            print '%(segid)s %(length)s %(elevation)s %(lstring)s %(surgo)s %(management)s %(slope)s' % row
    
        print 'Length of new: %s' % (len(newrows),)
        for row in newrows:
            print '%(segid)s %(length)s %(elevation)s %(lstring)s %(surgo)s %(management)s %(slope)s' % row

        sys.exit()
        
    return newrows

def compute_slope(fid):
    """ Compute the simple slope for the fid """
    cursor2.execute("""SELECT max(elevation), min(elevation), max(length)
    from flowpath_points where flowpath = %s and length < 121""", (fid,))
    row = cursor2.fetchone()
    return (row[0] - row[1]) / row[2]

def do_flowpath(huc_12, fid, fpath):
    """ Process a given flowpathid """
    slope = compute_slope(fid) 
    cursor2.execute("""SELECT segid, elevation, length, f.surgo, 
    slope, management,
    landuse1 || landuse2 || landuse3 || landuse4 || landuse5 || landuse6 as lstring,
    round(ST_X(ST_Transform(geom,4326))::numeric,2) as x, 
    round(ST_Y(ST_Transform(geom,4326))::numeric,2) as y from 
    flowpath_points f JOIN xref_surgo x on (x.surgo = f.surgo) 
    WHERE flowpath = %s and length < 121 and x.soilfile != 'IA9999.SOL'
    ORDER by segid ASC""", (fid,))
    rows = []
    x = None
    y = None
    maxmanagement = 0
    for i, row in enumerate(cursor2):
        if i == 0:
            x = row['x']
            y = row['y']
        if row['management'] > maxmanagement:
            maxmanagement = row['management']
        #if row['slope'] < 0.00001:
        #    row['slope'] = 0.00001
        # hard coded...
        row['slope'] = slope
        rows.append( row )
    
    if len(rows) < 2:
        print ' Not enough data for fid: %s, skipping' % (fid,)
        return None
    if len(rows) > 19:
        rows = simplify(rows)
    
    res = {}
    res['clifile'] = "/i/cli/%03.0fx%03.0f/%06.2fx%06.2f.cli" % (
                                                        0 - x,
                                                        y,
                                                        0 - x,
                                                        y)
    res['huc8'] = huc_12[:8]
    res['huc12'] = huc_12
    res['envfn'] = "/i/env/%s/%s_%s.env" % (res['huc8'], huc_12, fid)
    res['date'] = datetime.datetime.now()
    res['aspect'] = compute_aspect(rows[0]['x'], rows[0]['y'],
                                   rows[-1]['x'], rows[-1]['y'])
    res['prj_fn'] = "/i/prj/%s/%s/%s_%s.prj" % (res['huc8'], huc_12[-4:], 
                                                huc_12, fpath)
    res['length'] = rows[-1]['length']
    res['slope_points'] = len(rows)

    # Iterate over the rows and figure out the slopes and distance fracs
    slpdata = ""
    prevsoil = None
    lsoilstart = 0
    soils = []
    soillengths = []
    
    for row in rows:
        if prevsoil != row['surgo']:
            if prevsoil is not None:
                soils.append(prevsoil)
                soillengths.append( row['length'] - lsoilstart)
            prevsoil = row['surgo']
            lsoilstart = row['length']
        slpdata += " %.3f,%.5f" % (row['length'] / res['length'],
                                   row['slope'])
    soils.append(prevsoil)
    soillengths.append( res['length'] - lsoilstart)

    res['soilbreaks'] = len(soillengths) -1
    res['soils'] = ""
    res['slpdata'] = slpdata

    for d, s in zip(soillengths, soils):
        res['soils'] += """    %s {
        Distance = %.3f
        File = "/i/sol_input/%s"
    }\n""" % (s, d, surgo2file.get(s,s))


    prevman = None
    lmanstart = 0
    mans = []
    manlengths = []
    
    for row in rows:
        if row['lstring'] is None:
            continue
        if prevman != row['lstring']:
            if prevman is not None:
                mans.append( get_rotation(prevman, maxmanagement) )
                manlengths.append( row['length'] - lmanstart)
            prevman = row['lstring']
            lmanstart = row['length']

    mans.append( get_rotation(prevman, maxmanagement) )
    manlengths.append( res['length'] - lmanstart)
    res['manbreaks'] = len(manlengths) -1
    res['managements'] = ""

        
    for d, s in zip(manlengths, mans):
        res['managements'] += """    %s {
        Distance = %.3f
        File = "%s"
    }\n""" % (s, d, s)

    return res

def write_prj(data):
    """ Create the WEPP prj file """
    out = open(data['prj_fn'], 'w')
    
    # Profile format
    # [x] The first number is the hillslope aspect, 
    # [?] the second is the profile width in meters. 
    # [x] The next line contains the number of slope points 
    # [x] and the total distance in meters. 
    # px] The last line contains the fraction of the distance down the slope 
    # [x] and the slope at that point. 

    
    out.write("""#
# WEPP project written: %(date)s 
#
Version = 98.6
Name = default
Comments {
Example hillslope in Iowa.
}
Units = English
Landuse = 1
Length = %(length).4f
Profile {
    Data {
        %(aspect).4f  1.0
        %(slope_points)s  %(length).4f
        %(slpdata)s
    }
}
Climate {
   File = "%(clifile)s"
}
Soil {
   Breaks = %(soilbreaks)s
%(soils)s
}
Management {
   Breaks = %(manbreaks)s
%(managements)s
}
RunOptions {
   Version = 1
   SoilLossOutputType = 1
   EventFile = "%(envfn)s"
   WaterBalanceFile = "test.wb"
   SimulationYears = 7
   SmallEventByPass = 1
}

    
    
    """ %  data )
    out.close()

if __name__ == '__main__':
    # Go main Go
    cursor.execute("""SELECT fpath, fid, huc_12 from flowpaths""")
    for row in cursor:
        data = do_flowpath(row['huc_12'], row['fid'], row['fpath'])
        if data is not None:
            write_prj(data)