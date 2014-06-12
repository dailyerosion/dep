'''Generate the WEPP prj files based on what our database has for us
'''
import psycopg2
import psycopg2.extras
import os
import datetime
from math import atan2, degrees, pi

PGCONN = psycopg2.connect(database='idep', host='iemdb')
cursor = PGCONN.cursor(cursor_factory=psycopg2.extras.DictCursor)

def compute_aspect(x0, y0, x1, y1):
    """ Compute the aspect angle between two points """
    dx = x1 - x0
    dy = y1 - y0
    rads = atan2(-dy,dx)
    rads %= 2*pi
    return degrees(rads)

def do_flowpath(huc_12, fid):
    """ Process a given flowpathid """
    cursor.execute("""SELECT segid, elevation, length, landuse, surgo, 
    slope, management,
    landuse1 || landuse2 || landuse3 || landuse4 || landuse5 || landuse6 as lstring,
    ST_X(ST_Transform(geom,4326)) as x, 
    ST_Y(ST_Transform(geom,4326)) as y from flowpath_points WHERE flowpath = %s
    ORDER by segid ASC""", (fid,))
    rows = []
    for row in cursor:
        rows.append( row )
        
    res = {}
    res['clifile'] = "/i/cli/%03ix%03i/%07.2fx%07.2f.cli" % (0 - rows[0]['x'],
                                                           rows[0]['y'],
                                                           0 - rows[0]['x'],
                                                           rows[0]['y'])
    res['huc8'] = huc_12[:8]
    res['huc12'] = huc_12
    res['date'] = datetime.datetime.now()
    res['aspect'] = compute_aspect(rows[0]['x'], rows[0]['y'],
                                   rows[-1]['x'], rows[-1]['y'])
    res['prj_fn'] = "/i/prj/%s/%s/%s_%s.prj" % (res['huc8'], huc_12, 
                                                huc_12, fid)
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

    mandata = ""
    prevman = None
    lmanstart = 0
    mans = []
    manlengths = []
    
    for row in rows:
        if row['lstring'] is None:
            continue
        if prevman != row['lstring']:
            if prevman is not None:
                mans.append(prevman)
                manlengths.append( row['length'] - lmanstart)
            prevman = row['lstring']
            lmanstart = row['length']

    mans.append(prevman)
    manlengths.append( res['length'] - lmanstart)
    res['manbreaks'] = len(manlengths) -1
    res['managements'] = ""

        
    for d, s in zip(manlengths, mans):
        res['managements'] += """    %s {
        Distance = %.3f
        File = "/i/man/%s.man"
    }\n""" % (s, d, s)

    return res

def write_prj(data):
    """ Create the WEPP prj file """
    dirname = "/i/prj/%s/%s" % (data['huc8'], data['huc12'])
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
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
   SoilLossOutputFile = AutoName
   PlotFile = AutoName
   GraphFile = AutoName
   SimulationYears = 8
   SmallEventByPass = 1
}

    
    
    """ %  data )
    out.close()

if __name__ == '__main__':
    # Go main Go
    cursor.execute("""SELECT fid, huc_12 from flowpaths LIMIT 1""")
    for row in cursor:
        data = do_flowpath(row['huc_12'], row['fid'])
        write_prj(data)