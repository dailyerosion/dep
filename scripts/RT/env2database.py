"""
Process the ENV output to the database, for a given date
"""
import sys
import datetime
import glob
import os
import psycopg2
import numpy as np
idep = psycopg2.connect(database='idep', host='iemdb')
icursor = idep.cursor()

IDEPHOME = "/i"
SCENARIO = int(sys.argv[1])

def do(date, process_all):
    """ Process for this date, if process_all is true, then do it all!"""
    if process_all:
        print("Deleting all results_by_huc12 for scenario: %s" % (SCENARIO,))
        icursor.execute("""DELETE from results_by_huc12 WHERE 
                            scenario = %s""", (SCENARIO,))
    else:
        icursor.execute("""DELETE from results_by_huc12 WHERE 
                            valid = %s and scenario = %s""", (date, SCENARIO))
        if icursor.rowcount != 0:
            print '... env2database.py removed %s rows for date: %s' % (
                                                    icursor.rowcount, date)
    # Compute dictionary of slope lengths
    lengths = {}
    icursor.execute("""
    SELECT huc_12, fpath, ST_Length(geom) from flowpaths where
    scenario = %s
    """, (SCENARIO,))
    for row in icursor:
        lengths["%s_%s" % (row[0], row[1])] = row[2]
    
    
    os.chdir("/i/%s/env" % (SCENARIO,))
    hits = 0
    count = 0
    for huc8 in glob.glob("*"):
        os.chdir(huc8)
        for huc4 in glob.glob("*"):
            count += 1
            os.chdir(huc4)
            huc12 = huc8+huc4
            runs = 0
            data = {}
            for fn in glob.glob("*.env"):
                runs += 1
                for line in open(fn):
                    tokens = line.strip().split()
                    if (len(tokens) < 5 or tokens[0] in ['day', '---'] 
                        or line.find('******') > -1):
                        continue
                    ts = datetime.date(2006 + int(tokens[2]), 
                                            int(tokens[1]), int(tokens[0]))
                    if not process_all and date != ts:
                        continue
                    if not data.has_key(ts):
                        data[ts] = {'runoff': [],
                                    'loss': [],
                                    'precip': [],
                                    'delivery': []}
                    data[ts]['runoff'].append( float(tokens[4]) )
                    data[ts]['loss'].append( float(tokens[6]) )
                    data[ts]['precip'].append( float(tokens[3]) )
                    data[ts]['delivery'].append( float(tokens[12]) /
                                                 lengths[fn[:-4]])
            if runs > 0:
                for ts in data.keys():
                    avgloss = sum(data[ts]['loss']) / float(runs)
                    avgprecip = np.average(data[ts]['precip'])
                    avgrunoff = sum(data[ts]['runoff']) / float(runs)
                    avgdelivery = sum(data[ts]['delivery']) / float(runs)
                    icursor.execute("""
                    INSERT into results_by_huc12(huc_12, valid, 
                    min_precip, avg_precip, max_precip,
                    min_loss, avg_loss, max_loss,
                    min_delivery, avg_delivery, max_delivery,
                    min_runoff, avg_runoff, max_runoff, scenario) VALUES
                    (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (huc12, ts, min(data[ts]['precip']), 
                          avgprecip, max(data[ts]['precip']),
                    min(data[ts]['loss']), avgloss, max(data[ts]['loss']), 
                    min(data[ts]['delivery']), avgdelivery, max(data[ts]['delivery']), 
                          min(data[ts]['runoff']), 
                          avgrunoff, max(data[ts]['runoff']), SCENARIO))
                    hits += 1
            os.chdir("..")
        os.chdir("..")
    
    print '... env2database.py %s produced %s/%s huc12s with erosion' % (
                                            date, hits, count)
 
def update_properties(date):
    """ Update database properties to let us know we ran this date! """
    icursor.execute("""UPDATE properties SET value = %s 
    WHERE key = 'last_date'""", (date,))
    if icursor.rowcount == 0:
        icursor.execute("""INSERT into properties(key, value) VALUES
        (%s, %s)""", ('last_date', date))
 
def main():
    """ go main go """
    if len(sys.argv) == 5:
        ts = datetime.date( int(sys.argv[2]), int(sys.argv[3]), 
                             int(sys.argv[4]))
    else:
        ts = datetime.date.today() - datetime.timedelta(days=1)

    do(ts, (len(sys.argv) == 3 and sys.argv[2] == 'all'))
    if SCENARIO == 0:
        update_properties(ts)
        
 
if __name__ == '__main__':
    # Do something
    main()
    icursor.close()
    idep.commit()
    idep.close()