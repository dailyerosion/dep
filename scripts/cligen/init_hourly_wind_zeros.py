"""Create empty/zero hourly wind file.

This file is goosed to be all zeros as we run WEPS in a way to only generate
a SWEEP file.  Attm, it seems all zeros is OK.

"""

from datetime import datetime
from pathlib import Path

import click
import pandas as pd


@click.command()
def main():
    """Go Main Go."""
    fn = Path("/i/0/wind/zeros.win")
    fn.parent.mkdir(parents=True, exist_ok=True)
    hourly = " 0.0" * 24
    with open(fn, "w", encoding="ascii") as fh:
        # WEPS baseline is picky about this format.
        fh.write("""#   WIND_GEN4
#
#
#
#
#
#\n""")
        for dt in pd.date_range("2007/01/01", f"{datetime.now().year}/12/31"):
            fh.write(f" {dt:%-2d} {dt:%-2m} {dt:%Y} 0.0 {hourly}\n")


if __name__ == "__main__":
    main()
