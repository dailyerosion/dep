'''
Adjust IDEPv1 climate files to match our reality
'''
import glob
import os

os.chdir('/mnt/idep/data/clifiles/')
for fn in glob.glob("*.dat"):
    data = open(fn).readlines()
    if data[4].find(" 1997 ") == 0:
        continue
    print 'Modify: %s' % (fn,)
    o = open(fn, 'w')
    newdata = False
    for i, line in enumerate(data):
        if i == 4:
            line = line.replace("1997", "2007").replace(" 17 ", " 7 ")
        if not newdata and line.find("1\t1\t2007") == 0:
            newdata = True
        if i < 15 or newdata:
            o.write(line)
    o.close()