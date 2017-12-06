"""Add additional year to the climate files

    python add_new_year.py <scenario> <year_to_add>

The previous year is choosen based on if the year to add is a leap year or not,
if it is, then pick a year four years ago, if it isn't, use last year

"""
from __future__ import print_function
import glob
import sys
import os
import subprocess
from tqdm import tqdm


def workflow(filename, year):
    """Effort this file, please"""
    lines = open(filename).readlines()
    # Replace the header information denoting years simulated
    years_simulated = (year - 2007) + 1
    lines[4] = ("    41.53   -93.65         289          %i        2007"
                "              %i\n"
                ) % (years_simulated, years_simulated)
    data = "".join(lines)
    analog = year - 1 if year % 4 != 0 else year - 4
    if data.find("1\t1\t%s" % (year, )) > 0:
        print("%s already has %s data" % (filename, year))
        return
    pos = data.find("1\t1\t%s" % (analog, ))
    pos2 = data.find("1\t1\t%s" % (analog + 1,))
    content = data[pos:pos2] if pos2 > 0 else data[pos:]
    out = open("/tmp/%s" % (filename,), 'w')
    # careful here to get the line feeds right
    out.write(data + content.replace(str(analog), str(year)))
    out.close()
    subprocess.call("mv /tmp/%s %s" % (filename, filename), shell=True)


def main(argv):
    """Go Main Go"""
    scenario = argv[1]
    year = int(argv[2])
    os.chdir("/i/%s/cli" % (scenario,))
    for mydir in tqdm(glob.glob("*")):
        os.chdir(mydir)
        for fn in glob.glob("*.cli"):
            workflow(fn, year)
        os.chdir("..")


if __name__ == "__main__":
    main(sys.argv)
