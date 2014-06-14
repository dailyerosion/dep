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
    
    def __init__(self, huc12, fpid, lon, lat):
        ''' We initialize with a huc12 identifier and a flowpath id '''
        self.huc12 = huc12
        self.huc8 = huc12[:8]
        self.subdir = "%s/%s" % (huc12[:8], huc12[8:])
        self.fpid = fpid
        self.lon = lon
        self.lat = lat
        pass
    
    def get_wb_fn(self):
        ''' Return the water balance filename for this run '''
        return '%s/wb/%s/%s_%s.wb' % (IDEPHOME, self.subdir,
                                         self.huc12, self.fpid)

    def get_env_fn(self):
        ''' Return the event filename for this run '''
        return '%s/env/%s/%s_%s.env' % (IDEPHOME, self.subdir,
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
        return '%s/cli/%03ix%03i/%06.2fx%06.2f.cli' % (IDEPHOME, 0 - self.lon, 
                                                  self.lat, 0 - self.lon,
                                                  self.lat)

    def get_runfile_fn(self):
        ''' Return the run filename for this run '''
        return '%s/run/%s/%s_%s.run' % (IDEPHOME, self.subdir,
                                               self.huc12, self.fpid)

    
    def make_runfile(self):
        ''' Create a runfile for our runs '''
        print 'Creating runfile for HUC12: %s HS: %s' % (self.huc12, self.fpid)

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
        o.write("8\n") # years 2007-2014
        o.write("0\n")  # route all events

        o.close()

    def run(self):
        ''' Actually run wepp for this event '''
        runfile = self.get_runfile_fn()
        #if not os.path.isfile(runfile):
        self.make_runfile()
        p = subprocess.Popen("~/bin/wepp < %s" % (runfile,), shell=True,
                             stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        print p.stdout.read()

def realtime_run():
    ''' Do a realtime run, please '''
    idep = psycopg2.connect(database='idep', host='iemdb', user='nobody')
    icursor = idep.cursor()

    icursor.execute("""SELECT huc_12, fid, fpath, 
    ST_x(ST_PointN(ST_Transform(geom,4326),1)), 
    ST_y(ST_PointN(ST_Transform(geom,4326),1)) 
    from flowpaths""")
    for row in icursor:
        r = wepprun(row[0], row[2], row[3], row[4])
        r.run()
    
if __name__ == '__main__':
    ''' Go main Go '''
    realtime_run()