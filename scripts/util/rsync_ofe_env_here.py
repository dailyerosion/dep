"""Bring env/ofe files to my laptop."""

import os
import subprocess

from tqdm import tqdm


def main():
    """Go Main Go."""
    myhucs = []
    with open("myhucs.txt") as hucs:
        for line in hucs:
            myhucs.append(line.strip())

    progress = tqdm(myhucs)
    for huc in progress:
        progress.set_description(huc)
        huc8 = huc[:8]
        huc4 = huc[8:]
        for mydir in ["ofe", "env"]:
            localdir = f"/i/0/{mydir}/{huc8}/{huc4}"
            if not os.path.isdir(localdir):
                os.makedirs(localdir)
            cmd = [
                "rsync",
                "-a",
                "--delete",
                f"mesonet@metvm2-dc:/i/0/{mydir}/{huc8}/{huc4}/.",
                f"/i/0/{mydir}/{huc8}/{huc4}/",
            ]
            subprocess.call(cmd)


if __name__ == "__main__":
    main()
