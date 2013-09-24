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

def do(ts):
    ''' Process for this date! '''
    icursor.execute("""DELETE from results_by_huc12 where valid = %s""", 
                    (ts,))
    os.chdir("%s/env" % (IDEPHOME,)) 
    for huc12 in glob.glob("*"):
        os.chdir("%s/env/%s" % (IDEPHOME, huc12))
        runs = 0
        runoff = []
        loss = []
        precip = []
        for fn in glob.glob("*.env"):
            runs += 1
            found = False
            for line in open(fn):
                tokens = line.strip().split()
                if len(tokens) < 5 or tokens[0] in ['day', '---'] or line.find('******') > -1:
                    continue
                if (int(tokens[0]) == ts.day and 
                    int(tokens[1]) == ts.month and
                    int(tokens[2])+ 2006 == ts.year):
                    #if huc12 == '071000081505':
                    #    print fn, line[:-1]
                    found = True
                    runoff.append( float(tokens[4]) )
                    loss.append( float(tokens[6]) )
                    precip.append( float(tokens[3]) )
                    break
            if not found:
                precip.append( 0 ) # BUG
                loss.append( 0 )
                runoff.append( 0 )
        if runs > 0:
            avgloss = sum(loss) / float(runs)
            avgprecip = sum(precip) / float(runs)
            avgrunoff = sum(runoff) / float(runs)
            icursor.execute("""
            INSERT into results_by_huc12(huc_12, valid, 
            min_precip, avg_precip, max_precip,
            min_loss, avg_loss, max_loss,
            min_runoff, avg_runoff, max_runoff) VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (huc12, ts, 
                  min(precip), avgprecip, max(precip),
                  min(loss), avgloss, max(loss),
                  min(runoff), avgrunoff, max(runoff)))
 
if __name__ == '__main__':
    ts = datetime.datetime( int(sys.argv[1]), 
                            int(sys.argv[2]), 
                            int(sys.argv[3]))
    do(ts)
    icursor.close()
    idep.commit()
    idep.close()