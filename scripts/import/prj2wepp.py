""" Generate WEPP project files, which we then hand off to prj2wepp for run"""

import subprocess
import os
import sys
import glob
import shutil

SCENARIO = sys.argv[1]
EXE = "/home/akrherz/projects/idep/prj2wepp/prj2wepp"
WEPP = "/home/akrherz/projects/idep/prj2wepp/wepp"

if __name__ == '__main__':
    # Go Main Go
    os.chdir("/i/%s/prj" % (SCENARIO,))
    huc8s = glob.glob("*")
    sz = len(huc8s)
    for i, huc8 in enumerate(huc8s):
        print "%04i/%04i %s" % (i+1, sz, huc8)
        os.chdir(huc8)
        for huc4 in glob.glob("*"):
            huc12 = "%s%s" % (huc8, huc4)
            os.chdir(huc4)
            for pfile in glob.glob("*.prj"):
                fullfn = "/i/%s/prj/%s/%s/%s" % (SCENARIO, huc8, huc4, pfile)
                proc = subprocess.Popen("%s %s test %s no" % (
                                                        EXE, fullfn, WEPP),
                            shell=True, stderr=subprocess.PIPE,
                            stdout=subprocess.PIPE)
                # Need to block the above
                stdout = proc.stdout.read()
                if not os.path.isfile('test.man'):
                    print '---> ERROR generating output for %s%s\n%s' % (huc12,
                                                    proc.stderr.read(),
                                                    stdout)
                    #sys.exit()
                    continue
                # This generates .cli, .man, .run, .slp, .sol
                # We need the .man , .slp , .sol from this process
                for suffix in ['man', 'slp', 'sol']:
                    shutil.copyfile('test.%s' % (suffix,), 
                                    "/i/%s/%s/%s/%s/%s.%s" % (SCENARIO,
                                            suffix, huc8, huc4, 
                                            pfile[:-4], suffix))
                
                for suffix in ['cli', 'man', 'run', 'slp', 'sol']:
                    if os.path.isfile("test.%s" % (suffix,)):
                        os.unlink("test.%s" % (suffix,))
                    
            os.chdir("..")
        os.chdir("..")
