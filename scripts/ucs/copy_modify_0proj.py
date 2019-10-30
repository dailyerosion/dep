"""Copy and modify the scenario 0 prj files

7 -> 4 year rotation
9 -> 3 year rotation
"""
import glob
import os
import re

SCENARIO = 11
CLIFILE = re.compile(
    ('File = "/i/%s/cli/...x.../...\...x(...\...)\.cli') % (SCENARIO,)
)
LENGTH = re.compile("Length = (\d+\.\d+)")
# ROTS = ['CSOA', 'OACS', 'SOAC']
ROTS = ["CSO", "OCS", "SOC"]


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
                l = LENGTH.findall(old)
                res = CLIFILE.findall(old)
                lat = float(res[0])
                region = "southern"
                if lat > 42.46:
                    region = "northern"
                elif lat > 41.6:
                    region = "central"
                # using the legacy crops, not region specific
                rotfn = "IDEP2/UCS/%s_%s.rot" % (
                    "oldcrop2",
                    ROTS[i % len(ROTS)],
                )
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
                    % (rotfn, l[0], rotfn)
                )
                o.write(old[pos2:])
                o.close()
                i += 1
            os.chdir("..")
        os.chdir("..")


if __name__ == "__main__":
    main()
