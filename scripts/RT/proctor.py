'''
 I do the realtime run!
'''
import psycopg2
import os
import subprocess

IDEPHOME = "/i" # don't need trailing /

class wepprun:
    ''' Represents a single run of WEPP 
    
    Filenames have a 51 character restriction
    '''
    
    def __init__(self, huc12, hsid, lon, lat):
        ''' We initialize with a huc12 identifier and a hillslope id '''
        self.huc12 = huc12
        self.hsid = hsid
        self.lon = lon
        self.lat = lat
        pass
    
    def get_wb_fn(self):
        ''' Return the water balance filename for this run '''
        return '%s/wb/%s/hs_%s_%s.wb' % (IDEPHOME, self.huc12, self.huc12,
                                         self.hsid)

    def get_env_fn(self):
        ''' Return the event filename for this run '''
        return '%s/env/%s/hs_%s_%s.env' % (IDEPHOME, self.huc12, self.huc12,
                                          self.hsid)

    def get_man_fn(self):
        ''' Return the management filename for this run '''
        return '%s/man/%s/hs_%s_%s.man' % (IDEPHOME, self.huc12, 
                                                  self.huc12, self.hsid)
    
    def get_slope_fn(self):
        ''' Return the slope filename for this run '''
        return '%s/slp/%s/hs_%s_%s.slp' % (IDEPHOME, self.huc12, 
                                             self.huc12, self.hsid)

    def get_soil_fn(self):
        ''' Return the soil filename for this run '''
        return '%s/sol/%s/hs_%s_%s.sol' % (IDEPHOME, self.huc12, 
                                            self.huc12, self.hsid)
    
    def get_clifile_fn(self):
        ''' Return the climate filename for this run '''
        return '%s/cli/%07.3f_%07.3f.cli' % (IDEPHOME, 0 - self.lon, 
                                                  self.lat)

    def get_runfile_fn(self):
        ''' Return the run filename for this run '''
        return '%s/run/%s/hs_%s_%s.run' % (IDEPHOME, self.huc12, 
                                               self.huc12, self.hsid)

    
    def make_runfile(self):
        ''' Create a runfile for our runs '''
        print 'Creating runfile for HUC12: %s HS: %s' % (self.huc12, self.hsid)

        o = open(self.get_runfile_fn(), 'w')
        o.write("E\n")      # English units
        o.write("Yes\n")    # Run Hillslope
        o.write("1\n")      # Continuous simulation
        o.write("1\n")      # hillslope version
        o.write("No\n")     # pass file output?
        o.write("1\n")      # abbreviated annual output
        o.write("No\n")     # initial conditions output
        o.write("wepp.out\n")   # soil loss output file
        o.write("Yes\n")        # Do water balance output
        o.write("%s\n" % (self.get_wb_fn(),))   # water balance output file
        o.write("No\n")     # crop output
        o.write("No\n")     # soil output
        o.write("No\n")     # distance and sed output
        o.write("No\n")     # large graphics output
        o.write("Yes\n")    # event by event output
        o.write("%s\n" % (self.get_env_fn(),))  # event file output
        o.write("No\n")     # element output
        o.write("No\n")     # final summary output
        o.write("No\n")     # daily winter output
        o.write("No\n")     # plant yield output
        o.write("%s\n" % (self.get_man_fn(),))  # management file
        o.write("%s\n" % (self.get_slope_fn(),))  # slope file
        o.write("%s\n" % (self.get_clifile_fn(),))  # climate file
        o.write("%s\n" % (self.get_soil_fn(),))  # soil file
        o.write("0\n")  # Irrigation
        o.write("7\n") # years
        o.write("0\n")  # route all events

        o.close()

    def run(self):
        ''' Actually run wepp for this event '''
        runfile = self.get_runfile_fn()
        if not os.path.isfile(runfile):
            self.make_runfile()
        p = subprocess.Popen("~/bin/wepp < %s" % (runfile,), shell=True,
                             stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        print p.stdout.read()

def realtime_run():
    ''' Do a realtime run, please '''
    idep = psycopg2.connect(database='idep', host='iemdb', user='nobody')
    icursor = idep.cursor()

    icursor.execute("""SELECT huc_12, hs_id, ST_x(geom), ST_y(geom) 
    from hillslopes""")
    for row in icursor:
        r = wepprun(row[0], row[1], row[2], row[3])
        r.run()
    
if __name__ == '__main__':
    ''' Go main Go '''
    realtime_run()