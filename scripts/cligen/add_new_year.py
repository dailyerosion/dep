"""Add additional year to the climate files

    python add_new_year.py <scenario> <year_to_add>

The previous year is choosen based on if the year to add is a leap year or not,
if it is, then pick a year four years ago, if it isn't, use last year
"""

import glob
import os
import subprocess
from datetime import date

import click
from pyiem.util import logger
from tqdm import tqdm

LOG = logger()


def parse_filename(filename):
    """The filename tells us the location."""
    tokens = filename.rsplit(".", 1)[0].split("x")
    return float(tokens[0]) * -1.0, float(tokens[1])


def workflow(filename, newyear, analogyear):
    """Effort this file, please"""
    with open(filename, encoding="ascii") as fh:
        lines = fh.readlines()
    # Replace the header information denoting years simulated
    years_simulated = int((newyear - 2007) + 1)
    tokens = lines[4].strip().split()
    tokens[3] = str(years_simulated)
    tokens[5] = str(years_simulated)
    lines[4] = f"{' '.join(tokens)}\n"
    data = "".join(lines)
    if data.find(f"1\t1\t{newyear}") > 0:
        LOG.info("%s already has %s data", filename, newyear)
        return
    pos = data.find(f"1\t1\t{analogyear}")
    pos2 = data.find(f"1\t1\t{analogyear + 1}")
    content = data[pos:pos2] if pos2 > 0 else data[pos:]
    # Ensure that both data and content has a trailing linefeed
    if content[-1] != "\n":
        content += "\n"
    if data[-1] != "\n":
        data += "\n"
    with open(f"/tmp/{filename}", "w", encoding="ascii") as fh:
        # careful here to get the line feeds right
        fh.write(data + content.replace(str(analogyear), str(newyear)))
    subprocess.call(["mv", f"/tmp/{filename}", filename])


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


@click.command()
@click.option("--scenario", type=int, default=0)
@click.option("--year", type=int, default=date.today().year + 1)
def main(scenario, year):
    """Go Main Go"""
    analogyear = compute_analog_year(year)
    LOG.info("Using analog year %s for new year %s", analogyear, year)
    os.chdir(f"/i/{scenario}/cli")
    for mydir in tqdm(glob.glob("*")):
        os.chdir(mydir)
        for fn in glob.glob("*.cli"):
            workflow(fn, year, analogyear)
        os.chdir("..")


if __name__ == "__main__":
    main()
