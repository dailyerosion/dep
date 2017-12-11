"""Copy the scenario 0 run files and make some mods"""
from __future__ import print_function
import sys
import os
import glob

from tqdm import tqdm


def main(argv):
    """Go Main Go"""
    scenario = int(argv[1])
    os.chdir("/i/0/run")
    for huc8 in tqdm(glob.glob("*")):
        os.chdir(huc8)
        for huc4 in glob.glob("*"):
            os.chdir(huc4)
            for fn in glob.glob("*.run"):
                newfn = "/i/%s/run/%s/%s/%s" % (scenario, huc8, huc4, fn)
                lines = open(fn).readlines()
                # disable water balance output
                lines[8] = "No\n"
                lines.pop(9)
                # correct env output
                lines[14] = lines[14].replace("/i/0/env",
                                              "/i/%s/env" % (scenario, ))
                # turn off yield
                lines[18] = "No\n"
                lines.pop(19)
                # hard code climate
                lines[21] = "/i/0/cli/093x041/093.07x040.71.cli\n"
                fh = open(newfn, 'w')
                fh.write("".join(lines))
                fh.close()
            os.chdir("..")
        os.chdir("..")


if __name__ == '__main__':
    main(sys.argv)
