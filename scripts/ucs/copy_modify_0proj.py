"""Copy and modify the scenario 0 prj files"""
import glob
import os
import re

CLIFILE = re.compile("File = \"/i/7/cli/...x.../...\...x(...\...)\.cli")
LENGTH = re.compile("Length = (\d+\.\d+)")
ROTS = ['AACS', 'ACSA', 'CSAA', 'SAAC']


def main():
    """Do Something"""
    os.chdir("/i/0/prj")
    i = 0
    for huc8 in glob.glob("*"):
        os.chdir(huc8)
        for huc4 in glob.glob("*"):
            os.chdir(huc4)
            for fn in glob.glob("*.prj"):
                newfn = "/i/7/prj/%s/%s/%s" % (huc8, huc4, fn)
                old = open(fn).read().replace("/i/0/", "/i/7/")
                l = LENGTH.findall(old)
                res = CLIFILE.findall(old)
                lat = float(res[0])
                region = 'southern'
                if lat > 42.46:
                    region = 'northern'
                elif lat > 41.6:
                    region = 'central'
                rotfn = "IDEP2/UCS/%s_%s.rot" % (region, ROTS[i % 4])
                pos1 = old.find("Management {")
                pos2 = old.find("RunOptions {")
                o = open(newfn, 'w')
                o.write(old[:pos1])
                o.write("""Management {
   Breaks = 0
    %s {
        Distance = %s
        File = "%s"
    }

}
""" % (rotfn, l[0], rotfn))
                o.write(old[pos2:])
                o.close()
                i += 1
            os.chdir("..")
        os.chdir("..")

if __name__ == '__main__':
    main()
