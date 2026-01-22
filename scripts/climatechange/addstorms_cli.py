"""Add 1"/hr over one day storms."""

import os
import sys
from datetime import date

from pandas.io.sql import read_sql
from pyiem.database import get_dbconn
from tqdm import tqdm

from pydep.io.wepp import read_cli

with open("myhucs.txt") as fh:
    MYHUCS = [x.strip() for x in fh.readlines()]


def do(origfn, scenario, numstorms):
    """Work we do."""
    if not os.path.isfile(origfn):
        return False
    newfn = origfn.replace("/0/", f"/{scenario}/")
    newdir = os.path.dirname(newfn)
    if not os.path.isdir(newdir):
        os.makedirs(newdir)
    clidf = read_cli(origfn)
    # Find all spring dates without precipitation
    df = clidf[
        (
            clidf.index.month.isin([3, 4, 5])
            & (clidf["bpcount"] == 0)
            & (clidf["tmin"] > 0)
        )
    ]
    # For each year, pick X number of rows
    df2 = df.groupby(df.index.year).apply(lambda d: d.sample(numstorms))
    dates = df2.reset_index()["level_1"].dt.date.values
    # Edit the new climate file
    with open(newfn, "w") as fh:
        with open(origfn) as origfh:
            lines = origfh.readlines()
        linenum = 0
        while linenum < len(lines):
            if linenum < 15:
                fh.write(lines[linenum])
                linenum += 1
                continue
            tokens = lines[linenum].strip().split("\t")
            breakpoints = int(tokens[3])
            valid = date(int(tokens[2]), int(tokens[1]), int(tokens[0]))
            if valid in dates:
                tokens[3] = "5"
                fh.write("\t".join(tokens) + "\n")
                linenum += 1
                # Add the storm
                fh.write("12.00 0.00\n")
                fh.write("12.25 6.35\n")
                fh.write("12.50 12.70\n")
                fh.write("12.75 19.05\n")
                fh.write("13.00 25.40\n")
            else:
                fh.write(lines[linenum])
                linenum += 1
                for _i in range(breakpoints):
                    fh.write(lines[linenum])
                    linenum += 1
    return True


def main(argv):
    """Go Main Go."""
    scenario = int(argv[1])
    numstorms = int(argv[2])
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
        if not do(origfn, scenario, numstorms):
            failed += 1
    print(f"{failed}/{len(df.index)} runs failed.")


if __name__ == "__main__":
    main(sys.argv)
