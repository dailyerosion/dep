"""Daily Reprocessing.

Careful of the timing here.  IEMRE reruns -10 days at Noon, so we should
reprocess that date here too.

Run from systemd dep-reprocess.timer
"""

import datetime
import os
import subprocess


def main():
    """Go Main Go."""
    d10 = datetime.datetime.now() - datetime.timedelta(days=10)
    d11 = datetime.datetime.now() - datetime.timedelta(days=11)
    # Run env2database from 10 days ago
    with subprocess.Popen(
        [
            "python",
            "env2database.py",
            "--date",
            d11.strftime("%Y-%m-%d"),
            "-s",
            "0",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as proc:
        (stdout, stderr) = proc.communicate()
        if stdout != b"":
            print(stdout.decode("ascii"))
        if stderr != b"":
            print(stderr.decode("ascii"))
    os.chdir("../cligen")
    # Edit CLI files from 9 days ago
    with subprocess.Popen(
        [
            "python",
            "proctor_tile_edit.py",
            "--scenario=0",
            f"--date={d10:%Y-%m-%d}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as proc:
        (stdout, stderr) = proc.communicate()
        if stdout != b"":
            print(stdout.decode("ascii"))
        if stderr != b"":
            print(stderr.decode("ascii"))


if __name__ == "__main__":
    main()
