""" Generate WEPP project files, which we then hand off to prj2wepp for run"""

import subprocess
import os
import glob
import shutil

def check_dirs(huc8, huc12):
    """ Make sure directories exist, please """
    for d in ['man', 'slp', 'sol']:
        d = "Z:\\i\\%s\\%s\\%s" % (huc8, huc12, d)
        if not os.path.isdir(d):
            os.makedirs(d)

if __name__ == '__main__':
    # Go Main Go
    os.chdir("Z:\\i\\prj")
    for huc8 in glob.glob("*"):
        os.chdir(huc8)
        for huc12 in glob.glob("*"):
            os.chdir(huc12)
            check_dirs(huc8, huc12)
            for pfile in glob.glob("*.prj"):
                subprocess.call("c:\\wepp\prj2wepp.exe %s test c:\wepp no" % (
                            pfile,),
                            shell=True)
                # This generates .cli, .man, .run, .slp, .sol
                # We need the .man , .slp , .sol from this process
                for suffix in ['man', 'slp', 'sol']:
                    shutil.copyfile('test.%s' % (suffix,), 
                                    "Z:\\i\\%s\\%s\\%s\\%s.%s" % (
                                            suffix, huc8, huc12, 
                                            pfile[:-4], suffix))
                
                for suffix in ['cli', 'man', 'run', 'slp', 'sol']:
                    if os.path.isfile("test.%s" % (suffix,)):
                        os.unlink("test.%s" % (suffix,))
                    
            os.chdir("..")
        os.chdir("..")
