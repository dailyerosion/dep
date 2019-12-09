"""Add additional year to the climate files

    python add_new_year.py <scenario> <year_to_add>

The previous year is choosen based on if the year to add is a leap year or not,
if it is, then pick a year four years ago, if it isn't, use last year
"""
import glob
import sys
import os
import subprocess

from tqdm import tqdm
from pyiem.util import logger

LOG = logger()


def parse_filename(filename):
    """The filename tells us the location."""
    tokens = filename.rsplit(".", 1)[0].split("x")
    return float(tokens[0]) * -1.0, float(tokens[1])


def workflow(filename, year):
    """Effort this file, please"""
    # Figure out what this file's lon/lat values are
    lon, lat = parse_filename(filename)
    # LOG.debug("%s -> %.2f %.2f", filename, lon, lat)
    lines = open(filename).readlines()
    # Replace the header information denoting years simulated
    years_simulated = (year - 2007) + 1
    lines[4] = (
        "    %.2f   %.2f         289          %i        2007"
        "              %i\n"
    ) % (lat, lon, years_simulated, years_simulated)
    data = "".join(lines)
    analog = year - 1 if year % 4 != 0 else year - 4
    if data.find("1\t1\t%s" % (year,)) > 0:
        LOG.info("%s already has %s data", filename, year)
        return
    pos = data.find("1\t1\t%s" % (analog,))
    pos2 = data.find("1\t1\t%s" % (analog + 1,))
    content = data[pos:pos2] if pos2 > 0 else data[pos:]
    with open("/tmp/%s" % (filename,), "w") as fh:
        # careful here to get the line feeds right
        fh.write(data + content.replace(str(analog), str(year)))
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
