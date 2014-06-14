""" Generate WEPP project files, which we then hand off to prj2wepp for run"""

import subprocess
import os
import glob
import shutil

EXE = "/home/akrherz/projects/idep/prj2wepp/prj2wepp.exe"
WEPP = "/home/akrherz/projects/idep/prj2wepp/wepp"

def check_dirs(huc8, huc12):
    """ Make sure directories exist, please """
    for d in ['man', 'slp', 'sol']:
        d = "/i/%s/%s/%s" % (d, huc8, huc12)
        if not os.path.isdir(d):
            os.makedirs(d)

if __name__ == '__main__':
    # Go Main Go
    os.chdir("/i/prj")
    huc8s = glob.glob("*")
    sz = len(huc8s)
    for i, huc8 in enumerate(huc8s):
        print "%04i/%04i %s" % (i+1, sz, huc8)
        os.chdir(huc8)
        for huc12 in glob.glob("*"):
            os.chdir(huc12)
            check_dirs(huc8, huc12)
            for pfile in glob.glob("*.prj"):
                fullfn = "/i/%s/%s/%s" % (huc8, huc12, pfile)
                subprocess.call("%s %s test %s no" % (EXE, fullfn, WEPP),
                            shell=True, stderr=subprocess.PIPE,
                            stdout=subprocess.PIPE)
                if not os.path.isfile('test.man'):
                    print '---> ERROR generating output for %s' % (huc12,)
                    continue
                # This generates .cli, .man, .run, .slp, .sol
                # We need the .man , .slp , .sol from this process
                for suffix in ['man', 'slp', 'sol']:
                    shutil.copyfile('test.%s' % (suffix,), 
                                    "/i/%s/%s/%s/%s.%s" % (
                                            suffix, huc8, huc12, 
                                            pfile[:-4], suffix))
                
                for suffix in ['cli', 'man', 'run', 'slp', 'sol']:
                    if os.path.isfile("test.%s" % (suffix,)):
                        os.unlink("test.%s" % (suffix,))
                    
            os.chdir("..")
        os.chdir("..")
