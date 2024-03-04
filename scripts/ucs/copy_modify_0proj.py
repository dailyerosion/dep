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
                ll = LENGTH.findall(old)
                res = CLIFILE.findall(old)
                lat = float(res[0])
                if lat > 42.46:
                    pass
                elif lat > 41.6:
                    pass
                # using the legacy crops, not region specific
                rotfn = "IDEP2/UCS/%s_%s.rot" % (
                    "oldcrop2",
                    ROTS[i % len(ROTS)],
                )
                pos1 = old.find("Management {")
                pos2 = old.find("RunOptions {")
                with open(newfn, "w") as fp:
                    fp.write(old[:pos1])
                    fp.write(
                        """Management {
   Breaks = 0
    %s {
        Distance = %s
        File = "%s"
    }

}
"""
                        % (rotfn, ll[0], rotfn)
                    )
                    fp.write(old[pos2:])
                i += 1
            os.chdir("..")
        os.chdir("..")


if __name__ == "__main__":
    main()
