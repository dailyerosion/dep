""" Generate WEPP project files, which we then hand off to prj2wepp for run"""

import subprocess
import os
import sys
import glob
import shutil
from tqdm import tqdm

SCENARIO = sys.argv[1]
PROJDIR = "/opt/dep/prj2wepp"
EXE = "%s/prj2wepp" % (PROJDIR,)
WEPP = "%s/wepp" % (PROJDIR,)
BASEDIR = "/i/%s/prj" % (SCENARIO,)


def main():
    os.chdir(BASEDIR)
    huc8s = glob.glob("*")
    # huc8s = ['10290101', ]
    for huc8 in tqdm(huc8s):
        os.chdir(huc8)
        for huc4 in glob.glob("*"):
            huc12 = "%s%s" % (huc8, huc4)
            os.chdir(huc4)
            for pfile in glob.glob("*.prj"):
                # Run prj2wepp in its install dir so that the local userdb
                # is used
                os.chdir(PROJDIR)
                fullfn = "/i/%s/prj/%s/%s/%s" % (SCENARIO, huc8, huc4, pfile)
                cmd = "%s %s test %s no" % (EXE, fullfn, WEPP)
                proc = subprocess.Popen(cmd,
                                        shell=True, stderr=subprocess.PIPE,
                                        stdout=subprocess.PIPE)
                # Need to block the above
                stdout = proc.stdout.read()
                if not os.path.isfile('test.man'):
                    print(('---> ERROR generating output for %s\n%s\n%s\n%s'
                           ) % (huc12, cmd, proc.stderr.read(), stdout))
                    sys.exit()
                # This generates .cli, .man, .run, .slp, .sol
                # We need the .man , .slp , .sol from this process
                for suffix in ['man', 'slp', 'sol']:
                    shutil.copyfile('test.%s' % (suffix,),
                                    ("/i/%s/%s/%s/%s/%s.%s"
                                     ) % (SCENARIO,
                                          suffix, huc8, huc4,
                                          pfile[:-4], suffix))

                for suffix in ['cli', 'man', 'run', 'slp', 'sol']:
                    if os.path.isfile("test.%s" % (suffix,)):
                        os.unlink("test.%s" % (suffix,))
                os.chdir("%s/%s/%s" % (BASEDIR, huc8, huc4))
            os.chdir("..")
        os.chdir("..")


if __name__ == '__main__':
    # Go Main Go
    main()
