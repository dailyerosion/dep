"""
 I do the realtime run!
"""
import psycopg2
import sys
import os
import subprocess
import datetime
from multiprocessing import Pool

SCENARIO = sys.argv[1]
# don't need trailing /
IDEPHOME = "/i/%s" % (SCENARIO, )


class wepprun(object):
    """ Represents a single run of WEPP

    Filenames have a 51 character restriction
    """

    def __init__(self, huc12, fpid, clifile):
        """ We initialize with a huc12 identifier and a flowpath id """
        self.huc12 = huc12
        self.huc8 = huc12[:8]
        self.subdir = "%s/%s" % (huc12[:8], huc12[8:])
        self.fpid = fpid
        self.clifile = clifile

    def get_wb_fn(self):
        ''' Return the water balance filename for this run '''
        return '%s/wb/%s/%s_%s.wb' % (IDEPHOME, self.subdir,
                                      self.huc12, self.fpid)

    def get_env_fn(self):
        ''' Return the event filename for this run '''
        return '%s/env/%s/%s_%s.env' % (IDEPHOME, self.subdir,
                                        self.huc12, self.fpid)

    def get_ofe_fn(self):
        """ Return the filename used for OFE output """
        return '%s/ofe/%s/%s_%s.ofe' % (IDEPHOME, self.subdir, self.huc12,
                                        self.fpid)

    def get_error_fn(self):
        ''' Return the event filename for this run '''
        return '%s/error/%s/%s_%s.error' % (IDEPHOME, self.subdir,
                                            self.huc12, self.fpid)

    def get_man_fn(self):
        ''' Return the management filename for this run '''
        return '%s/man/%s/%s_%s.man' % (IDEPHOME, self.subdir,
                                        self.huc12, self.fpid)

    def get_slope_fn(self):
        ''' Return the slope filename for this run '''
        return '%s/slp/%s/%s_%s.slp' % (IDEPHOME, self.subdir,
                                        self.huc12, self.fpid)

    def get_soil_fn(self):
        ''' Return the soil filename for this run '''
        return '%s/sol/%s/%s_%s.sol' % (IDEPHOME, self.subdir,
                                        self.huc12, self.fpid)

    def get_clifile_fn(self):
        ''' Return the climate filename for this run '''
        return '%s/%s' % (IDEPHOME, self.clifile)

    def get_runfile_fn(self):
        ''' Return the run filename for this run '''
        return '%s/run/%s/%s_%s.run' % (IDEPHOME, self.subdir,
                                        self.huc12, self.fpid)

    def make_runfile(self):
        ''' Create a runfile for our runs '''
        o = open(self.get_runfile_fn(), 'w')
        o.write("E\n")      # English units
        o.write("Yes\n")    # Run Hillslope
        o.write("1\n")      # Continuous simulation
        o.write("1\n")      # hillslope version
        o.write("No\n")     # pass file output?
        o.write("1\n")      # abbreviated annual output
        o.write("No\n")     # initial conditions output
        o.write("/dev/null\n")   # soil loss output file
        o.write("Yes\n")        # Do water balance output
        o.write("%s\n" % (self.get_wb_fn(),))   # water balance output file
        o.write("No\n")     # crop output
        o.write("No\n")     # soil output
        o.write("No\n")     # distance and sed output
        o.write("No\n")     # large graphics output
        o.write("Yes\n")    # event by event output
        o.write("%s\n" % (self.get_env_fn(),))  # event file output
        o.write("No\n")     # element output
        # o.write("%s\n" % (self.get_ofe_fn(),))
        o.write("No\n")     # final summary output
        o.write("No\n")     # daily winter output
        o.write("No\n")     # plant yield output
        o.write("%s\n" % (self.get_man_fn(),))  # management file
        o.write("%s\n" % (self.get_slope_fn(),))  # slope file
        o.write("%s\n" % (self.get_clifile_fn(),))  # climate file
        o.write("%s\n" % (self.get_soil_fn(),))  # soil file
        o.write("0\n")  # Irrigation
        o.write("8\n")  # years 2007-2014
        o.write("0\n")  # route all events

        o.close()

    def run(self):
        ''' Actually run wepp for this event '''
        runfile = self.get_runfile_fn()
        if not os.path.isfile(runfile):
            self.make_runfile()
        p = subprocess.Popen(["~/bin/wepp", ],
                             stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        p.stdin.write(open(runfile).read())
        res = p.stdout.read()
        if res[-13:-1] != 'SUCCESSFULLY':
            print 'Run HUC12: %s FPATH: %4s errored!' % (self.huc12, self.fpid)
            e = open(self.get_error_fn(), 'w')
            e.write(res)
            e.close()

QUEUE = []


def realtime_run():
    ''' Do a realtime run, please '''
    idep = psycopg2.connect(database='idep', host='iemdb', user='nobody')
    icursor = idep.cursor()

    icursor.execute("""SELECT huc_12, fid, fpath, climate_file
    from flowpaths where scenario = %s""" % (SCENARIO,))
    for row in icursor:
        QUEUE.append(row)


def run(row):
    """ Run ! """
    r = wepprun(row[0], row[2], row[3])
    r.run()

if __name__ == '__main__':
    # Go main Go
    realtime_run()
    pool = Pool()  # defaults to cpu-count
    sts = datetime.datetime.now()
    sz = len(QUEUE)
    for i, _ in enumerate(pool.imap_unordered(run, QUEUE), 1):
        if i > 0 and i % 5000 == 0:
            delta = datetime.datetime.now() - sts
            secs = delta.microseconds / 1000000. + delta.seconds
            speed = i / secs
            remaining = ((sz - i) / speed) / 3600.
            print ('%5.2fh Processed %6s/%6s [%.2f runs per sec] '
                   'remaining: %5.2fh') % (secs / 3600., i, sz, speed,
                                           remaining)
