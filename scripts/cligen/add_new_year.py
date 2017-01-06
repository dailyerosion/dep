"""Add additional year to the climate files

Note that this does not adjust the header for years modeled. Why not?  Because
we currently have it set to a large number and WEPP appears to ignore it.
"""
import glob
import sys
import os
import subprocess
from tqdm import tqdm


def do(fn, year):
    data = open(fn).read()
    analog = year - 1 if year % 4 != 0 else year - 4
    if data.find("1\t1\t%s" % (year, )) > 0:
        print("%s already has %s data" % (fn, year))
        return
    pos = data.find("1\t1\t%s" % (analog, ))
    pos2 = data.find("1\t1\t%s" % (analog + 1,))
    out = open("/tmp/%s" % (fn,), 'w')
    extra = "\n" if data[-1] != "\n" else ''
    out.write(data + extra + data[pos:pos2].replace(str(analog), str(year)) +
              extra)
    out.close()
    subprocess.call("mv /tmp/%s %s" % (fn, fn), shell=True)


def main(argv):
    scenario = argv[1]
    year = int(argv[2])
    os.chdir("/i/%s/cli" % (scenario,))
    errors = 0
    for mydir in tqdm(glob.glob("*")):
        if errors > 100:
            print("Aborting with too many errors")
            sys.exit()
        os.chdir(mydir)
        for fn in glob.glob("*.cli"):
            try:
                do(fn, year)
            except Exception as exp:
                print("%s resulted in exp: %s" % (fn, exp))
                errors += 1
        os.chdir("..")

if __name__ == "__main__":
    main(sys.argv)
