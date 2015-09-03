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

TODAY = datetime.date.today()


def load_precip(date):
    """Load up our QC'd daily precip dataset """
    fn = date.strftime("/mnt/idep2/data/dailyprecip/%Y/%Y%m%d.npy")
    if not os.path.isfile(fn):
        print("load_precip(%s) failed, no such file" % (date,))
        return
    return np.load(fn)


def do(date, process_all):
    """ Process for this date, if process_all is true, then do it all!"""
    precip = load_precip(date)

    if process_all:
        print("Deleting all {results_by_huc12,results} for scenario: %s" % (
                                                                SCENARIO,))
        icursor.execute("""DELETE from results_by_huc12 WHERE
                            scenario = %s""", (SCENARIO,))
        icursor.execute("""DELETE from results WHERE
                            scenario = %s""", (SCENARIO,))
    else:
        for tbl in ['results', 'results_by_huc12']:
            icursor.execute("""DELETE from """+tbl+""" WHERE
                            valid = %s and scenario = %s""", (date, SCENARIO))
            if icursor.rowcount != 0:
                print '... env2database.py removed %s %s rows for date: %s' % (
                                                tbl, icursor.rowcount, date)
    # Compute dictionary of slope lengths
    lengths = {}
    icursor.execute("""
    SELECT huc_12, fpath, ST_Length(geom) from flowpaths where
    scenario = %s
    """, (SCENARIO,))
    for row in icursor:
        lengths["%s_%s" % (row[0], row[1])] = row[2]

    huc12_centroids = {}
    if precip is not None:
        icursor.execute("""
        WITH centers as (
         SELECT huc_12, ST_Transform(ST_Centroid(geom),4326) as g from ia_huc12
        )

        SELECT huc_12, ST_x(g), ST_y(g) from centers
        """)
        SOUTH = 36.9
        WEST = -99.2
        for row in icursor:
            y = int((row[2] - SOUTH) * 100.)
            x = int((row[1] - WEST) * 100.)
            huc12_centroids[row[0]] = precip[y, x]

    os.chdir("/i/%s/env" % (SCENARIO,))
    hits = 0
    count = 0
    justrain = 0
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
                hsid = fn.split("_")[1][:-4]
                for line in open(fn):
                    tokens = line.strip().split()
                    if (len(tokens) < 5 or tokens[0] in ['day', '---'] or
                            line.find('******') > -1 or line.find('NaN') > -1):
                        continue
                    ts = datetime.date(2006 + int(tokens[2]),
                                       int(tokens[1]), int(tokens[0]))
                    if not process_all and date != ts:
                        continue
                    if ts not in data:
                        data[ts] = {'runoff': [],
                                    'loss': [],
                                    'precip': [],
                                    'delivery': []}
                    data[ts]['runoff'].append(float(tokens[4]))
                    data[ts]['loss'].append(float(tokens[6]))
                    data[ts]['precip'].append(float(tokens[3]))
                    data[ts]['delivery'].append(float(tokens[12]) /
                                                lengths[fn[:-4]])
                    icursor.execute("""
                        INSERT into results(huc_12, hs_id,
                        valid, runoff, loss, precip, scenario, delivery)
                        VALUES(%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (huc12, hsid, ts, float(tokens[4]),
                              float(tokens[6]), float(tokens[3]), SCENARIO,
                              float(tokens[12]) / lengths[fn[:-4]]))
            qcprecip = huc12_centroids.get(huc12, 0)
            if runs > 0:
                keys = data.keys()
                for ts in keys:
                    # Don't ingest data from the future!
                    if ts >= TODAY:
                        continue
                    avgloss = sum(data[ts]['loss']) / float(runs)
                    avgprecip = np.average(data[ts]['precip'])
                    avgrunoff = sum(data[ts]['runoff']) / float(runs)
                    avgdelivery = sum(data[ts]['delivery']) / float(runs)
                    icursor.execute("""
                        INSERT into results_by_huc12(huc_12, valid,
                        min_precip, avg_precip, max_precip, qc_precip,
                        min_loss, avg_loss, max_loss,
                        min_delivery, avg_delivery, max_delivery,
                        min_runoff, avg_runoff, max_runoff, scenario) VALUES
                        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (huc12, ts, min(data[ts]['precip']),
                          avgprecip, max(data[ts]['precip']), qcprecip,
                          min(data[ts]['loss']), avgloss,
                          max(data[ts]['loss']),
                          min(data[ts]['delivery']), avgdelivery,
                          max(data[ts]['delivery']),
                          min(data[ts]['runoff']), avgrunoff,
                          max(data[ts]['runoff']), SCENARIO))
                    hits += 1
                if len(keys) == 0 and qcprecip >= 0.01:
                    icursor.execute("""INSERT into results_by_huc12
                        (huc_12, valid, qc_precip, scenario)
                        VALUES (%s,%s,%s,%s)""", (huc12, date, qcprecip,
                                                  SCENARIO))
                    justrain += 1
            os.chdir("..")
        os.chdir("..")

    print '... env2database.py %s -> %s/%s/%s (Erosion/Prec/Tot) huc12s' % (
                                            date, hits, justrain, count)


def update_properties(date):
    """ Update database properties to let us know we ran this date! """
    key = "last_date_%s" % (SCENARIO, )
    icursor.execute("""UPDATE properties SET value = %s
    WHERE key = %s""", (date, key))
    if icursor.rowcount == 0:
        icursor.execute("""INSERT into properties(key, value) VALUES
        (%s, %s)""", (key, date))


def main():
    """ go main go """
    if len(sys.argv) == 5:
        ts = datetime.date(int(sys.argv[2]), int(sys.argv[3]),
                           int(sys.argv[4]))
    else:
        ts = datetime.date.today() - datetime.timedelta(days=1)

    do(ts, (len(sys.argv) == 3 and sys.argv[2] == 'all'))
    # Only update the last processing date when this script is run without
    # arguments, which is a realtime run
    if SCENARIO == 0 and len(sys.argv) == 2:
        update_properties(ts)


if __name__ == '__main__':
    # Do something
    main()
    icursor.close()
    idep.commit()
    idep.close()
