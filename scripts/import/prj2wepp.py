""" Generate WEPP project files, which we then hand off to prj2wepp for run"""
import subprocess
import os
import sys
import glob
import shutil

from tqdm import tqdm
from pyiem.util import logger

LOG = logger()
PROJDIR = "/opt/dep/prj2wepp"
EXE = f"{PROJDIR}/prj2wepp"
WEPP = f"{PROJDIR}/wepp"


def main(argv):
    """Go Main Go."""
    scenario = int(argv[1])
    basedir = f"/i/{scenario}/prj"
    myhucs = []
    if os.path.isfile("myhucs.txt"):
        with open("myhucs.txt", encoding="utf8") as fh:
            myhucs = fh.read().split("\n")
        LOG.info("using HUC12s found in myhucs.txt...")
    os.chdir(basedir)
    huc8s = glob.glob("*")
    errors = 0
    for huc8 in tqdm(huc8s):
        os.chdir(huc8)
        for huc4 in glob.glob("*"):
            huc12 = f"{huc8}{huc4}"
            if myhucs and huc12 not in myhucs:
                continue
            os.chdir(huc4)
            for pfile in glob.glob("*.prj"):
                # Run prj2wepp in its install dir so that the local userdb
                # is used
                os.chdir(PROJDIR)
                fullfn = f"/i/{scenario}/prj/{huc8}/{huc4}/{pfile}"
                cmd = f"{EXE} {fullfn} test {WEPP} no"
                proc = subprocess.Popen(
                    cmd,
                    shell=True,
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                )
                # Need to block the above
                stdout = proc.stdout.read()
                if not os.path.isfile("test.man"):
                    LOG.info(
                        "---> ERROR generating output for %s\n%s\n%s\n%s",
                        huc12,
                        cmd,
                        proc.stderr.read(),
                        stdout,
                    )
                    errors += 1
                    if errors > 10:
                        LOG.info("Aborting due to errors...")
                        sys.exit()
                    os.chdir(os.path.join(basedir, huc8, huc4))
                    continue
                # This generates .cli, .man, .run, .slp, .sol
                # We need the .man , .slp , .sol from this process
                # slp is generated in flowpath2prj
                for suffix in ["man", "sol"]:
                    shutil.copyfile(
                        f"test.{suffix}",
                        (
                            f"/i/{scenario}/{suffix}/{huc8}/{huc4}/"
                            f"{pfile[:-4]}.{suffix}"
                        ),
                    )

                for suffix in ["cli", "man", "run", "slp", "sol"]:
                    if os.path.isfile(f"test.{suffix}"):
                        os.unlink(f"test.{suffix}")
                os.chdir(os.path.join(basedir, huc8, huc4))
            os.chdir("..")
        os.chdir("..")


if __name__ == "__main__":
    # Go Main Go
    main(sys.argv)
