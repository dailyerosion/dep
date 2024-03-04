"""Apply arbitrary daily shifts within the climate file."""

import os
import sys
from datetime import date, timedelta

from pandas.io.sql import read_sql
from pyiem.util import get_dbconn
from tqdm import tqdm

MYHUCS = [x.strip() for x in open("myhucs.txt")]
FLOOR = date(2007, 1, 1)
CEILING = date(2020, 12, 31)


def do(origfn, scenario, dayshift):
    """Work we do."""
    if not os.path.isfile(origfn):
        return False
    newfn = origfn.replace("/0/", f"/{scenario}/")
    newdir = os.path.dirname(newfn)
    if not os.path.isdir(newdir):
        os.makedirs(newdir)
    with open(newfn, "w") as fh:
        lines = open(origfn).readlines()
        linenum = 0
        while linenum < len(lines):
            if linenum < 15:
                fh.write(lines[linenum])
                linenum += 1
                continue
            tokens = lines[linenum].strip().split("\t")
            breakpoints = int(tokens[3])
            valid = date(int(tokens[2]), int(tokens[1]), int(tokens[0]))
            newvalid = valid + timedelta(days=dayshift)
            if newvalid < FLOOR or newvalid > CEILING:
                linenum += 1
                linenum += breakpoints
                continue
            # If shifting forward, need to replicate 1 Jan
            if valid == FLOOR and dayshift > 0:
                for i in range(dayshift):
                    newvalid2 = FLOOR + timedelta(days=i)
                    tokens[0] = str(newvalid2.day)
                    tokens[1] = str(newvalid2.month)
                    tokens[2] = str(newvalid2.year)
                    fh.write("\t".join(tokens) + "\n")
                    for j in range(breakpoints):
                        fh.write(lines[linenum + j + 1].strip() + "\n")
            tokens[0] = str(newvalid.day)
            tokens[1] = str(newvalid.month)
            tokens[2] = str(newvalid.year)
            fh.write("\t".join(tokens) + "\n")
            for j in range(breakpoints):
                fh.write(lines[linenum + j + 1].strip() + "\n")
            # If shifting backward, need to replicate 31 Dec
            if valid == CEILING and dayshift < 0:
                for i in range(dayshift + 1, 1):
                    newvalid2 = CEILING + timedelta(days=i)
                    tokens[0] = str(newvalid2.day)
                    tokens[1] = str(newvalid2.month)
                    tokens[2] = str(newvalid2.year)
                    fh.write("\t".join(tokens) + "\n")
                    for j in range(breakpoints):
                        fh.write(lines[linenum + j + 1].strip() + "\n")
            linenum += 1
            linenum += breakpoints
    return True


def main(argv):
    """Go Main Go."""
    scenario = int(argv[1])
    dayshift = int(argv[2])
    # Find the climate files we need to edit
    df = read_sql(
        "SELECT distinct climate_file from flowpaths where scenario = 0 and "
        "huc_12 in %s",
        get_dbconn("idep"),
        params=(tuple(MYHUCS),),
        index_col=None,
    )
    # Create directories as needed
    progress = tqdm(df["climate_file"].values)
    failed = 0
    for origfn in progress:
        progress.set_description(origfn.split("/")[-1])
        if not do(origfn, scenario, dayshift):
            failed += 1
    print(f"{failed}/{len(df.index)} runs failed.")


if __name__ == "__main__":
    main(sys.argv)
