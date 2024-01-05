"""Daily Reprocessing.

Run from systemd dep-reprocess.timer
"""
import datetime
import os
import subprocess


def main():
    """Go Main Go."""
    d9 = datetime.datetime.now() - datetime.timedelta(days=9)
    d10 = datetime.datetime.now() - datetime.timedelta(days=10)
    # Run env2database from 10 days ago
    subprocess.call(
        [
            "python",
            "env2database.py",
            "--date",
            d10.strftime("%Y-%m-%d"),
            "-s",
            "0",
        ]
    )
    os.chdir("../cligen")
    # Edit CLI files from 9 days ago
    subprocess.call(
        [
            "python",
            "proctor_tile_edit.py",
            "0",
            f"{d9:%Y}",
            f"{d9:%m}",
            f"{d9:%d}",
        ]
    )


if __name__ == "__main__":
    main()
