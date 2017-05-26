"""We have Nones in our soil files, lets squash until fixed upstream"""
from __future__ import print_function
import glob


def main():
    """Go Main Go"""
    hits = 0
    files = 0
    for fn in glob.glob("/i/0/sol_input/*.SOL"):
        files += 1
        pos = open(fn).read().find(" None ")
        if pos > -1:
            oldata = open(fn).read()
            fp = open(fn, 'w')
            fp.write(oldata.replace(" None ", " 2.000 "))
            fp.close()
            hits += 1
    print("Fixed: %s/%s" % (hits, files))


if __name__ == '__main__':
    main()
