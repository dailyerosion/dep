""" Construct management files out of building blocks

                     No-till (1)   (2-5)
  B - Soy               B1          B25    IniCropDef.Default
  F - forest            F1          F25    IniCropDef.Tre_2239
G/P - Pasture           P1          P25    IniCropDef.gra_3425
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

SCENARIO = sys.argv[1]

PGCONN = psycopg2.connect(database='idep', host='iemdb')
cursor = PGCONN.cursor()

INITIAL_COND = {'B': 'IniCropDef.Default',
                'F': 'IniCropDef.Tre_2239',
                'P': 'IniCropDef.gra_3425',
                'G': 'IniCropDef.gra_3425',
                'C': 'IniCropDef.Default',
                'T': 'IniCropDef.Default',
                'U': 'IniCropDef.Default',
                'X': 'IniCropDef.Default',
                'R': 'IniCropDef.Aft_12889',
                }


def read_file(code, cfactor, year):
    """ Read a file and do replacement for year """
    data = open('blocks/%s%s.txt' % (code, cfactor), 'r').read()
    return data.replace("{yr}", str(year))


def do_rotation(code, cfactor):
    """ Process a given 6char rotation code and cfactor """
    dirname = "../../prj2wepp/wepp/data/managements/IDEP2/%s/%s" % (code[:2],
                                                                    code[2:4])
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
    fn = "%s/%s-%s.rot" % (dirname, code, cfactor)
    if os.path.isfile(fn):
        return

    data = {}
    data['date'] = datetime.datetime.now()
    data['code'] = code
    data['name'] = "%s-%s" % (code, cfactor)
    data['initcond'] = INITIAL_COND[code[0]]
    data['year1'] = read_file(code[0], cfactor, 1)  # 2007
    data['year2'] = read_file(code[1], cfactor, 2)  # 2008
    data['year3'] = read_file(code[2], cfactor, 3)  # 2009
    data['year4'] = read_file(code[3], cfactor, 4)  # 2010
    data['year5'] = read_file(code[4], cfactor, 5)  # 2011
    data['year6'] = read_file(code[5], cfactor, 6)  # 2012
    data['year7'] = read_file(code[6], cfactor, 7)  # 2013
    data['year8'] = read_file(code[7], cfactor, 8)  # 2014
    data['year9'] = read_file(code[0], cfactor, 9)  # 2015 <<-- repeated
    data['year10'] = read_file(code[1], cfactor, 9)  # 2016 <<-- repeated

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

if __name__ == '__main__':
    # Go Main Go
    cursor.execute("""SELECT distinct
        lu2007 || lu2008 || lu2009 || lu2010 || lu2011 || lu2012 || lu2013
        || lu2014 || lu2015 || lu2016
        from flowpath_points WHERE scenario = %s""", (SCENARIO,))
    for row in cursor:
        if row[0] is None:
            continue
        for i in (1, 25):
            do_rotation(row[0], i)
