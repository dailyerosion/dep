"""
Adjust IDEPv1 climate files to match our reality
"""
import glob
import os
import sys

SCENARIO = sys.argv[1]

os.chdir("/i/%s/cli/" % (SCENARIO,))
for d in glob.glob("*"):
    os.chdir(d)
    for fn in glob.glob("*.cli"):
        print("Modify: %s" % (fn,))
        data = open(fn).readlines()
        if data[4].find(" 1997 ") == 0:
            continue
        o = open(fn, "w")
        newdata = False
        for i, line in enumerate(data):
            if i == 4:
                line = line.replace("1997", "2007").replace(" 17 ", " 9 ")
            if not newdata and line.find("1\t1\t2007") == 0:
                newdata = True
            if i < 15 or newdata:
                o.write(line)
        o.close()
    os.chdir("..")
