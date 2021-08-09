"""For each HUC12 we are processing, dump our present file database."""
import os
import sys


def main(argv):
    """Go Main Go."""
    scenario = int(argv[1])
    for line in open("myhucs.txt"):
        huc12 = line.strip()
        removed = 0
        for (
            subdir
        ) in "crop error man ofe prj run slp sol wb yld env rot".split():
            mydir = "/i/%s/%s/%s/%s" % (scenario, subdir, huc12[:8], huc12[8:])
            if not os.path.isdir(mydir):
                continue
            for _, _, fns in os.walk(mydir):
                for fn in fns:
                    os.unlink("%s/%s" % (mydir, fn))
                    removed += 1
        print("    %s removed %s files" % (huc12, removed))


if __name__ == "__main__":
    main(sys.argv)
