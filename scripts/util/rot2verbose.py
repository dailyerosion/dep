"""Convert the .rot file into something Dr Wilson wants."""

import glob
from datetime import datetime, timedelta

import click


@click.command()
@click.option("--huc12", type=str, help="HUC12 code")
def main(huc12):
    """Go Main Go."""
    for fn in glob.glob(f"/i/0/rot/{huc12[:8]}/{huc12[8:]}/*.rot"):
        now = datetime(2007, 1, 1)
        with (
            open(fn, encoding="ascii") as fh,
            open(fn.replace(".rot", ".txt"), "w") as outfh,
        ):
            for line in fh:
                if len(line) > 10 and line.endswith("}\n"):
                    tokens = line.split(maxsplit=6)
                    dt = datetime(
                        int(tokens[2]) + 2006, int(tokens[0]), int(tokens[1])
                    )
                    while now < dt:
                        outfh.write(f"{now:%Y %03j} 0\n")
                        now = now + timedelta(days=1)
                    outfh.write(f"{dt:%Y %03j} 1 {tokens[5]:>20s} {tokens[6]}")
            while now < datetime(2025, 1, 1):
                outfh.write(f"{now:%Y %03j} 0\n")
                now = now + timedelta(days=1)


if __name__ == "__main__":
    main()
