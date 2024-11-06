"""Run Regression tests."""

import json
import os
import subprocess
import sys

from pydep.io.dep import read_wb
from pydep.io.wepp import read_env


def main():
    """Go."""
    for fn in os.listdir("."):
        if not os.path.isdir(fn) or fn == "common":
            continue
        os.chdir(fn)
        # Ensure we get new data
        if os.path.isfile("wepp_env.txt"):
            os.remove("wepp_env.txt")
        with subprocess.Popen(
            "../../wepp20230117/wepp < fp.run",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as proc:
            (stdout, stderr) = proc.communicate()
            if proc.returncode:
                sys.stdout.write(
                    f"FAILED: {fn},\n"
                    f"WEPP returned {proc.returncode}\n"
                    "stdout:\n"
                    f"{stdout.decode()}\n"
                    "stderr:\n"
                    f"{stderr.decode()}\n"
                )
                sys.exit(1)

        df = read_env("wepp_env.txt")
        avg_det = df["av_det"].sum() / 15.0 * 4.463
        with open("answer.json", "r", encoding="ascii") as fh:
            answer = json.load(fh)
        failed = abs(avg_det - answer["av_det"]) > 0.01
        sys.stdout.write(
            f"{'FAILED' if failed else 'PASS'}: {fn}, "
            f"expected {answer['av_det']:.3f}, got {avg_det:.3f}\n"
        )
        if failed:
            sys.exit(3)

        df = read_wb("wepp_wb.txt")
        max_sw1 = df["sw1"].max()
        failed = abs(max_sw1 - answer["max_sw1"]) > 1  # forgiving
        sys.stdout.write(
            f"{'FAILED' if failed else 'PASS'}: {fn}, "
            f"expected {answer['max_sw1']:.3f}, got {max_sw1:.3f}\n"
        )
        if failed:
            sys.exit(3)

        os.chdir("..")


if __name__ == "__main__":
    main()
