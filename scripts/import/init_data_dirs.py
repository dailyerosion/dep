'''
Initialize needed directories
'''
import psycopg2
import os

idep = psycopg2.connect(database='idep', host='iemdb')
icursor = idep.cursor()

IDEPHOME = "/mnt/idep/2"

icursor.execute("""
  SELECT huc_12 from ia_huc12
""")
for row in icursor:
    huc12 = row[0]
    for typ in ['managements', 'runfiles', 'slopes', 'soils', 'wb', 'env']:
        dirname = "%s/%s/%s" % (IDEPHOME, typ, huc12)
        if os.path.isdir(dirname):
            continue
        print 'MKDIR: %s' % (dirname,)
        os.makedirs(dirname)