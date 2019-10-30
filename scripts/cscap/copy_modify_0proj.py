"""Copy and modify the scenario 0 prj files

"""
import glob
import os
import re
import sys

SCENARIO = int(sys.argv[1])
LENGTH = re.compile("Length = (\d+\.\d+)")
FILENAMES = {
    18: "CC_NC_NT.rot",
    19: "CS_CC_CT.rot",
    20: "CS_NC_CT.rot",
    21: "CS_NC_PL.rot",
    22: "CS_NC_NT.rot",
    23: "CS_CC_NT.rot",
    24: "CC_CC_NT.rot",
}


def main():
    """Do Something"""
    os.chdir("/i/0/prj")
    i = 0
    for huc8 in glob.glob("*"):
        os.chdir(huc8)
        for huc4 in glob.glob("*"):
            os.chdir(huc4)
            for fn in glob.glob("*.prj"):
                newfn = "/i/%s/prj/%s/%s/%s" % (SCENARIO, huc8, huc4, fn)
                old = open(fn).read().replace("/i/0/", "/i/%s/" % (SCENARIO,))
                thelength = LENGTH.findall(old)
                # using the legacy crops, not region specific
                rotfn = "IDEP2/CSCAP/%s_%s" % (i % 2 + 1, FILENAMES[SCENARIO])
                pos1 = old.find("Management {")
                pos2 = old.find("RunOptions {")
                o = open(newfn, "w")
                o.write(old[:pos1])
                o.write(
                    """Management {
   Breaks = 0
    %s {
        Distance = %s
        File = "%s"
    }

}
"""
                    % (rotfn, thelength[0], rotfn)
                )
                o.write(old[pos2:])
                o.close()
                i += 1
            os.chdir("..")
        os.chdir("..")


if __name__ == "__main__":
    main()
