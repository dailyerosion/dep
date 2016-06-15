""" Construct management files out of building blocks

                     No-till (1)   (2-5)
  B - Soy               B1          B25    IniCropDef.Default
  F - forest            F1          F25    IniCropDef.Tre_2239
  G - Sorghum
  P - Pasture           P1          P25    IniCropDef.gra_3425
  C - Corn              C1          C25    IniCropDef.Default
  R - Other crops       R1          R25    IniCropDef.Aft_12889
  T - ?
  U - ?
  X - ?
"""

import psycopg2
import os
import datetime
import sys
from tqdm import tqdm

SCENARIO = sys.argv[1]
OVERWRITE = True
if len(sys.argv) == 2:
    print("WARNING: This does not overwrite old files!")
    OVERWRITE = False

PGCONN = psycopg2.connect(database='idep', host='iemdb')
cursor = PGCONN.cursor()

INITIAL_COND = {'B': 'IniCropDef.Default',
                'F': 'IniCropDef.Tre_2239',
                'P': 'IniCropDef.gra_3425',
                'G': None,
                'C': 'IniCropDef.Default',
                'T': 'IniCropDef.Default',
                'U': 'IniCropDef.Default',
                'X': 'IniCropDef.Default',
                'R': 'IniCropDef.Aft_12889',
                }
SOYBEAN_PLANT = {
    'KS_SOUTH': datetime.date(2000, 5, 25),
    'KS_CENTRAL': datetime.date(2000, 5, 25),
    'KS_NORTH': datetime.date(2000, 5, 25),
    'IA_SOUTH': datetime.date(2000, 5, 12),
    'IA_CENTRAL': datetime.date(2000, 5, 17),
    'IA_NORTH': datetime.date(2000, 5, 23)
    }
CORN_PLANT = {
    'KS_SOUTH': datetime.date(2000, 4, 20),
    'KS_CENTRAL': datetime.date(2000, 4, 25),
    'KS_NORTH': datetime.date(2000, 4, 30),
    'IA_SOUTH': datetime.date(2000, 4, 30),
    'IA_CENTRAL': datetime.date(2000, 5, 5),
    'IA_NORTH': datetime.date(2000, 5, 10)
    }
CORN = {
    'KS_SOUTH': 'CropDef.Cor_0964',
    'KS_CENTRAL': 'CropDef.Cor_0964',
    'KS_NORTH': 'CropDef.Cor_0964',
    'IA_SOUTH': 'CropDef.Cor_0965',
    'IA_CENTRAL': 'CropDef.Cor_0966',
    'IA_NORTH': 'CropDef.Cor_0967'
        }
SOYBEAN = {
    'KS_SOUTH': 'CropDef.Soy_2191',
    'KS_CENTRAL': 'CropDef.Soy_2191',
    'KS_NORTH': 'CropDef.Soy_2191',
    'IA_SOUTH': 'CropDef.Soy_2192',
    'IA_CENTRAL': 'CropDef.Soy_2193',
    'IA_NORTH': 'CropDef.Soy_2194'
        }


def read_file(zone, code, cfactor, year):
    """ Read a file and do replacement for year """
    data = open('blocks/%s%s.txt' % (code, cfactor), 'r').read()
    pdate = ''
    pdatem5 = ''
    pdatem10 = ''
    plant = ''
    if code == 'C':
        d = CORN_PLANT[zone]
        pdate = d.strftime("%m    %d")
        pdatem5 = (d - datetime.timedelta(days=5)).strftime("%m    %d")
        pdatem10 = (d - datetime.timedelta(days=10)).strftime("%m    %d")
        plant = CORN[zone]
    elif code == 'B':
        d = SOYBEAN_PLANT[zone]
        pdate = d.strftime("%m    %d")
        pdatem5 = (d - datetime.timedelta(days=5)).strftime("%m    %d")
        pdatem10 = (d - datetime.timedelta(days=10)).strftime("%m    %d")
        plant = SOYBEAN[zone]
    return data % {'yr': year, 'pdate': pdate, 'pdatem5': pdatem5,
                   'pdatem10': pdatem10, 'plant': plant}


def do_rotation(zone, code, cfactor):
    """ Process a given rotation code and cfactor """
    dirname = ("../../prj2wepp/wepp/data/managements/IDEP2/%s/%s/%s"
               ) % (zone, code[:2], code[2:4])
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
    fn = "%s/%s-%s.rot" % (dirname, code, cfactor)
    if not OVERWRITE and os.path.isfile(fn):
        return

    data = {}
    data['date'] = datetime.datetime.now()
    data['code'] = code
    data['name'] = "%s-%s" % (code, cfactor)
    data['initcond'] = INITIAL_COND[code[0]]
    data['year1'] = read_file(zone, code[0], cfactor, 1)  # 2007
    data['year2'] = read_file(zone, code[1], cfactor, 2)  # 2008
    data['year3'] = read_file(zone, code[2], cfactor, 3)  # 2009
    data['year4'] = read_file(zone, code[3], cfactor, 4)  # 2010
    data['year5'] = read_file(zone, code[4], cfactor, 5)  # 2011
    data['year6'] = read_file(zone, code[5], cfactor, 6)  # 2012
    data['year7'] = read_file(zone, code[6], cfactor, 7)  # 2013
    data['year8'] = read_file(zone, code[7], cfactor, 8)  # 2014
    data['year9'] = read_file(zone, code[8], cfactor, 9)  # 2015
    data['year10'] = read_file(zone, code[9], cfactor, 10)  # 2016

    o = open(fn, 'w')
    o.write("""#
# WEPP rotation saved on: %(date)s
#
# Created with scripts/mangen/build_management.py
#
Version = 98.7
Name = %(name)s
Description {
}
Color = 0 255 0
LandUse = 1
InitialConditions = %(initcond)s

Operations {
%(year1)s
%(year2)s
%(year3)s
%(year4)s
%(year5)s
%(year6)s
%(year7)s
%(year8)s
%(year9)s
%(year10)s
}
""" % data)
    o.close()


def main():
    """Do Something"""
    cursor.execute("""
    WITH np as (
        SELECT ST_ymax(ST_Transform(geom, 4326)) as lat, fid
        from flowpaths WHERE scenario = %s)

    SELECT np.lat,
        lu2007 || lu2008 || lu2009 || lu2010 || lu2011 || lu2012 || lu2013
        || lu2014 || lu2015 || lu2016
        from flowpath_points p, np WHERE p.flowpath = np.fid and
        scenario = %s""", (SCENARIO, SCENARIO))
    for row in tqdm(cursor, total=cursor.rowcount):
        zone = "KS_NORTH"
        if row[0] >= 42.5:
            zone = "IA_NORTH"
        elif row[0] >= 41.5:
            zone = "IA_CENTRAL"
        elif row[0] >= 40.5:
            zone = "IA_SOUTH"
        if row[1] is None:
            continue
        for i in (1, 25):  # loop over c-factors
            do_rotation(zone, row[1], i)

if __name__ == '__main__':
    main()
