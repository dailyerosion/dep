"""Generate plots."""
import subprocess


def main():
    """Go Main Go."""
    for v in ["avg_loss", "avg_runoff", "qc_precip", "avg_delivery"]:
        for yr in range(2007, 2018):
            cmd = f"python yearly_summary.py {yr} {v}_metric"
            print(cmd)
            subprocess.call(cmd, shell=True)


if __name__ == "__main__":
    main()
