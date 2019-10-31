"""For some reason, we have corrupt files to start the new year

So this script does a replacement, and some QC in the process"""
import glob
import os


def do(fn):
    """Do."""
    data = open(fn).read()
    pos1 = data.find("\n1\t1\t2015")
    pos2 = data.find("\n1\t1\t2016")
    pos3 = data.find("\n1\t1\t2017")

    newfp = open("new%s" % (fn,), "w")
    # everything up till 1 Jan 2017
    newfp.write(data[:pos3])
    # Then repeat 2015 data, with 2015 replaced
    newfp.write(data[pos1:pos2].replace("\t2015", "\t2017") + "\n")
    newfp.close()

    data = open("new%s" % (fn,)).read()
    print("%s %s" % (fn, data.find("31\t12\t2017")))
    os.rename("new%s" % (fn,), fn)


def main():
    """Go main."""
    os.chdir("i/0/cli")
    for zone in glob.glob("*"):
        os.chdir(zone)
        for fn in glob.glob("*.cli"):
            do(fn)
        os.chdir("..")


if __name__ == "__main__":
    main()
