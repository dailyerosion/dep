"""Copy the scenario 0 run files and make some mods"""
from __future__ import print_function
import sys
import os
import glob

from tqdm import tqdm


def main(argv):
    """Go Main Go"""
    use_scenario = 0
    scenario = int(argv[1])
    os.chdir("/i/%s/run" % (use_scenario, ))
    for huc8 in tqdm(glob.glob("*")):
        os.chdir(huc8)
        for huc4 in glob.glob("*"):
            os.chdir(huc4)
            for fn in glob.glob("*.run"):
                newdir = "/i/%s/run/%s/%s" % (scenario, huc8, huc4)
                if not os.path.isdir(newdir):
                    continue
                newfn = "%s/%s" % (newdir, fn)
                lines = open(fn).readlines()
                if len(lines) < 22:
                    print("Bad fn? %s" % (fn, ))
                    continue
                lines[8] = "No\n"
                lines.pop(9)
                # correct env output
                lines[14] = lines[14].replace("/i/%s/env" % (use_scenario, ),
                                              "/i/%s/env" % (scenario, ))
                lines[20] = lines[20].replace("/i/%s/man" % (use_scenario, ),
                                              "/i/%s/man" % (scenario, ))
                lines[21] = lines[21].replace("/i/%s/slp" % (use_scenario, ),
                                              "/i/%s/slp" % (scenario, ))
                lines[23] = lines[23].replace("/i/%s/sol" % (use_scenario, ),
                                              "/i/%s/sol" % (scenario, ))
                # hard code climate
                # lines[21] = "/i/0/cli/093x041/093.07x040.71.cli\n"
                fh = open(newfn, 'w')
                fh.write("".join(lines))
                fh.close()
            os.chdir("..")
        os.chdir("..")


if __name__ == '__main__':
    main(sys.argv)
