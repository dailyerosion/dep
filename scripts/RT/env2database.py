'''
Process the ENV output to the database, for a given date
'''
import sys
import datetime
import glob
import os
import psycopg2
idep = psycopg2.connect(database='idep', host='iemdb')
icursor = idep.cursor()

IDEPHOME = "/i"

def do():
    ''' Process for this date! '''
    os.chdir("/i/env") 
    for huc8 in glob.glob("*"):
        os.chdir(huc8)
        for huc4 in glob.glob("*"):
            os.chdir(huc4)
            huc12 = huc8+huc4
            runs = 0
            data = {}
            for fn in glob.glob("*.env"):
                runs += 1
                for line in open(fn):
                    tokens = line.strip().split()
                    if len(tokens) < 5 or tokens[0] in ['day', '---'] or line.find('******') > -1:
                        continue
                    ts = datetime.datetime( 2006 + int(tokens[2]), int(tokens[1]),
                                            int(tokens[0]) )
                    if not data.has_key(ts):
                        data[ts] = {'runoff': [],
                                    'loss': [],
                                    'precip': []}
                    data[ts]['runoff'].append( float(tokens[4]) )
                    data[ts]['loss'].append( float(tokens[6]) )
                    data[ts]['precip'].append( float(tokens[3]) )
            if runs > 0:
                for ts in data.keys():
                    avgloss = sum(data[ts]['loss']) / float(runs)
                    avgprecip = sum(data[ts]['precip']) / float(runs)
                    avgrunoff = sum(data[ts]['runoff']) / float(runs)
                    icursor.execute("""
                    INSERT into results_by_huc12(huc_12, valid, 
                    min_precip, avg_precip, max_precip,
                    min_loss, avg_loss, max_loss,
                    min_runoff, avg_runoff, max_runoff) VALUES
                    (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (huc12, ts, 
                          min(data[ts]['precip']), avgprecip, max(data[ts]['precip']),
                          min(data[ts]['loss']), avgloss, max(data[ts]['loss']),
                          min(data[ts]['runoff']), avgrunoff, max(data[ts]['runoff'])))
            os.chdir("..")
        os.chdir("..")
 
if __name__ == '__main__':
    #ts = datetime.datetime( int(sys.argv[1]), 
    #                        int(sys.argv[2]), 
    #                        int(sys.argv[3]))
    do()
    icursor.close()
    idep.commit()
    idep.close()