"""
 Quick check to see that the CLI files have all the data we think they do
"""
import glob
import sys
import os

SCENARIO = sys.argv[1]
YEAR = sys.argv[2]

os.chdir("/i/%s/cli" % (SCENARIO,))
for mydir in glob.glob("*"):
    os.chdir(mydir)
    for fn in glob.glob("*.cli"):
        data = open(fn).read()
        pos = data.find("%s\t%s\t%s" % (31, 12, YEAR))
        if pos == -1:
            print '/i/%s/cli/%s/%s failed to find 12/31/%s' % (SCENARIO,
                                                               mydir, fn, YEAR)
    os.chdir("..")
