"""  Crop is Swi_2785

IDEP2/CSCAP/SWITCHGRASS.rot
"""
from __future__ import print_function
import os
import glob

from pyiem.dep import read_slp


SCENARIO = 36
SLOPE_THRESHOLD = 3.


def main():
    """Go Main Go"""
    # make needed mods
    # use old one with mods if slope less than threshold
    # replace rotation if slope greater
    os.chdir("/i/0/prj")
    hits = 0
    total = 0
    for huc8 in glob.glob("*"):
        os.chdir(huc8)
        for huc4 in glob.glob("*"):
            os.chdir(huc4)
            for fn in glob.glob("*.prj"):
                total += 1
                hillslope = fn.split("_")[1].split(".")[0]
                newfn = "/i/%s/prj/%s/%s/%s" % (SCENARIO, huc8, huc4, fn)
                # Figure out the slope
                slpfn = "/i/0/slp/%s/%s/%s%s_%s.slp" % (huc8, huc4, huc8, huc4,
                                                        hillslope)
                slp = read_slp(slpfn)
                bulk = (slp[-1]['y'][-1]) / slp[-1]['x'][-1]
                slope_percent = (0 - bulk) * 100.
                if slope_percent >= SLOPE_THRESHOLD:
                    hits += 1
                lines = open(fn).readlines()
                for i, line in enumerate(lines):
                    if line.find("EventFile") > 0:
                        lines[i] = line.replace("/i/0/env",
                                                "/i/%s/env" % (SCENARIO, ))
                    if line.find('File = "IDEP2/') > 0:
                        lines[i] = ('        File = '
                                    '"IDEP2/CSCAP/SWITCHGRASS.rot"\n')
                fp = open(newfn, 'w')
                fp.write("".join(lines))
                fp.close()
            os.chdir("..")
        os.chdir("..")

    print(("Slope: %s hits: %s total: %s ratio: %.2f"
           ) % (SLOPE_THRESHOLD, hits, total, hits / float(total) * 100.))


if __name__ == '__main__':
    main()
