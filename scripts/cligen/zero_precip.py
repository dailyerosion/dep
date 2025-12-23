"""Sometimes, we just want to zero out a precip event."""

import glob
import os
import sys
from datetime import date, timedelta


def do(fn, dt: date):
    """Do."""
    with open(fn, encoding="utf-8") as fh:
        data = fh.read()
    dt2 = dt + timedelta(days=1)
    pos1 = data.find(dt.strftime("%-d\t%-m\t%Y"))
    pos2 = data.find(dt2.strftime("%-d\t%-m\t%Y"))
    if -1 in [pos1, pos2]:
        print("Couldn't find date in", fn)
        return
    myline = data[pos1:pos2].split("\n")[0]
    tokens = myline.split("\t")
    tokens[3] = "0"

    with open(f"new{fn}", "w", encoding="utf-8") as fh:
        fh.write(data[:pos1])
        fh.write("\t".join(tokens) + "\n")
        fh.write(data[pos2:])

    os.rename(f"new{fn}", fn)


def main(argv):
    """Go main."""
    dt = date(int(argv[1]), int(argv[2]), int(argv[3]))
    os.chdir("/i/0/cli")
    for zone in glob.glob("*"):
        os.chdir(zone)
        for fn in glob.glob("*.cli"):
            do(fn, dt)
        os.chdir("..")


if __name__ == "__main__":
    main(sys.argv)
