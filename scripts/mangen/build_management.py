"""Construct building block management files

In the database, we construct a list of unique rotation strings and then
generate WEPP .rot files for each unique string.  These .rot files are later
used by prj2wepp to generate the .man files.

  python build_management.py <scenario> <optional_to_overwrite>

Here's a listing of project landuse codes used

                     No-till (1)   (2-5)
  B - Soy               B1          B25    IniCropDef.Default
  F - forest            F1          F25    IniCropDef.Tre_2239
  G - Sorghum
  P - Pasture           P1          P25    IniCropDef.gra_3425
  C - Corn              C1          C25    IniCropDef.Default
  R - Other crops       R1          R25    IniCropDef.Aft_12889
  T - Water
  U - Developed
  X - Unclassified
  I - Idle
  L - Double Crop  (started previous year)
  W - Wheat
  N - ???  *see 27 Sep 2016 email from dave, it is unused, so treat as I*
"""
from __future__ import print_function
import os
import datetime
import sys

import psycopg2
from tqdm import tqdm

SCENARIO = sys.argv[1]
OVERWRITE = True
if len(sys.argv) == 2:
    print("WARNING: This does not overwrite old files!")
    OVERWRITE = False

PGCONN = psycopg2.connect(database='idep', host='iemdb')

# Note that the default used below is
INITIAL_COND_DEFAULT = 'IniCropDef.Default'
INITIAL_COND = {'F': 'IniCropDef.Tre_2239',
                'P': 'IniCropDef.gra_3425',
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
    """Read a block file and do replacements

    Args:
      zone (str): The DEP cropping zone
      code (str): the crop code
      cfactor (int): the c-factor for tillage
      year (int): the year of this crop

    Returns:
      str with the raw data used for the .rot file
    """
    data = open('blocks/%s%s.txt' % (code, cfactor), 'r').read()
    pdate = ''
    pdatem5 = ''
    pdatem10 = ''
    plant = ''
    # We currently only have zone specific files for Corn and Soybean
    if code == 'C':
        date = CORN_PLANT[zone]
        pdate = date.strftime("%m    %d")
        pdatem5 = (date - datetime.timedelta(days=5)).strftime("%m    %d")
        pdatem10 = (date - datetime.timedelta(days=10)).strftime("%m    %d")
        plant = CORN[zone]
    elif code == 'B':
        date = SOYBEAN_PLANT[zone]
        pdate = date.strftime("%m    %d")
        pdatem5 = (date - datetime.timedelta(days=5)).strftime("%m    %d")
        pdatem10 = (date - datetime.timedelta(days=10)).strftime("%m    %d")
        plant = SOYBEAN[zone]
    return data % {'yr': year, 'pdate': pdate, 'pdatem5': pdatem5,
                   'pdatem10': pdatem10, 'plant': plant}


def do_rotation(zone, code, cfactor):
    """Create the rotation file

    Args:
      zone (str): The DEP cropping zone
      code (str): the management code string used to identify crops
      cfactor (int): the c-factor at play here

    Returns:
      None
    """
    # We create a tree of codes to keep directory sizes in check
    dirname = ("../../prj2wepp/wepp/data/managements/IDEP2/%s/%s/%s"
               ) % (zone, code[:2], code[2:4])
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
    fn = "%s/%s-%s.rot" % (dirname, code, cfactor)
    # Don't re-create this file if it already exists and we don't have
    # OVERWRITE set
    if not OVERWRITE and os.path.isfile(fn):
        return
    # Dictionary of values used to fill out the file template below
    data = {}
    data['date'] = datetime.datetime.now()
    data['code'] = code
    data['name'] = "%s-%s" % (code, cfactor)
    data['initcond'] = INITIAL_COND.get(code[0], INITIAL_COND_DEFAULT)
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
    data['year11'] = read_file(zone, code[10], cfactor, 11)  # 2017

    fp = open(fn, 'w')
    fp.write("""#
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
%(year11)s
}
""" % data)
    fp.close()


def get_zone(latitude):
    """Determine the DEP zone based on the provided latitude"""
    if latitude is None:
        return None
    zone = "KS_NORTH"
    if latitude >= 42.5:
        zone = "IA_NORTH"
    elif latitude >= 41.5:
        zone = "IA_CENTRAL"
    elif latitude >= 40.5:
        zone = "IA_SOUTH"
    return zone


def main():
    """Our main code entry point"""
    cursor = PGCONN.cursor()
    cursor.execute("""
    WITH np as (
        SELECT ST_ymax(ST_Transform(geom, 4326)) as lat, fid
        from flowpaths WHERE scenario = %s)

    SELECT np.lat,
        lu2007 || lu2008 || lu2009 || lu2010 || lu2011 || lu2012 || lu2013
        || lu2014 || lu2015 || lu2016 || lu2017
        from flowpath_points p, np WHERE p.flowpath = np.fid and
        scenario = %s
    """, (SCENARIO, SCENARIO))
    for row in tqdm(cursor, total=cursor.rowcount):
        zone = get_zone(row[1])
        if zone is None:
            continue
        for i in (1, 25):  # loop over c-factors
            do_rotation(zone, row[1], i)


if __name__ == '__main__':
    main()
