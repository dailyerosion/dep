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


def workflow(filename, newyear, analogyear):
    """Effort this file, please"""
    # Figure out what this file's lon/lat values are
    lon, lat = parse_filename(filename)
    # LOG.debug("%s -> %.2f %.2f", filename, lon, lat)
    lines = open(filename).readlines()
    # Replace the header information denoting years simulated
    years_simulated = (newyear - 2007) + 1
    lines[4] = (
        "    %.2f   %.2f         289          %i        2007"
        "              %i\n"
    ) % (lat, lon, years_simulated, years_simulated)
    data = "".join(lines)
    if data.find("1\t1\t%s" % (newyear,)) > 0:
        LOG.info("%s already has %s data", filename, newyear)
        return
    pos = data.find("1\t1\t%s" % (analogyear,))
    pos2 = data.find("1\t1\t%s" % (analogyear + 1,))
    content = data[pos:pos2] if pos2 > 0 else data[pos:]
    with open("/tmp/%s" % (filename,), "w") as fh:
        # careful here to get the line feeds right
        fh.write(data + content.replace(str(analogyear), str(newyear)))
    subprocess.call("mv /tmp/%s %s" % (filename, filename), shell=True)


def compute_analog_year(year):
    """Figure out which year to use as an analog."""
    analogyear = year - 1
    # If last year is a leap year. go another back
    if analogyear % 4 == 0:
        analogyear -= 1
    # if the new year is a leap year, use something 4 years back
    if year % 4 == 0:
        analogyear = year - 4
    return analogyear


def main(argv):
    """Go Main Go"""
    scenario = argv[1]
    year = int(argv[2])
    analogyear = compute_analog_year(year)
    LOG.info("Using analog year %s for new year %s", analogyear, year)
    os.chdir("/i/%s/cli" % (scenario,))
    for mydir in tqdm(glob.glob("*")):
        os.chdir(mydir)
        for fn in glob.glob("*.cli"):
            workflow(fn, year, analogyear)
        os.chdir("..")


if __name__ == "__main__":
    main(sys.argv)


def test_analog():
    """Test that we can do the right thing."""
    assert compute_analog_year(2021) == 2019
    assert compute_analog_year(2020) == 2016
