"""Generate plots."""

import subprocess
from datetime import date


def main():
    """Go Main Go."""
    for v in ["avg_loss", "avg_runoff", "qc_precip", "avg_delivery"]:
        for yr in range(2007, date.today().year + 1):
            cmd = f"python yearly_summary.py {yr} {v}_metric"
            print(cmd)
            subprocess.call(cmd, shell=True)


if __name__ == "__main__":
    main()
