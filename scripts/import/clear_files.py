"""For each HUC12 we are processing, dump our present file database."""

import os

import click

TARGETS = "crop error man ofe prj run slp sol wb yld env rot out".split()


@click.command()
@click.option("--scenario", type=int, required=True)
def main(scenario: int):
    """Go Main Go."""
    myhucs = [x.strip() for x in open("myhucs.txt", encoding="utf8")]
    for huc12 in myhucs:
        removed = 0
        for subdir in TARGETS:
            mydir = f"/i/{scenario}/{subdir}/{huc12[:8]}/{huc12[8:]}"
            if not os.path.isdir(mydir):
                continue
            for _, _, fns in os.walk(mydir):
                for fn in fns:
                    os.unlink(os.path.join(mydir, fn))
                    removed += 1
        print(f"    {huc12} removed {removed:5.0f} files")


if __name__ == "__main__":
    main()
