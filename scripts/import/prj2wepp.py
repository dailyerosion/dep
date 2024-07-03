"""Generate WEPP project files, which we then hand off to prj2wepp for run"""

import os
import shutil
import subprocess
import sys
import tempfile
import threading
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool

from pyiem.util import logger
from tqdm import tqdm

LOG = logger()
PROJDIR = "/opt/dep/prj2wepp"
EXE = f"{PROJDIR}/prj2wepp"
CPUCOUNT = min([4, int(cpu_count() / 2)])


def find_prjs(scenario, myhucs):
    """Yield up found prj files."""
    for root, _dirs, files in os.walk(f"/i/{scenario}/prj"):
        tokens = root.split("/")
        if len(tokens) == 6:
            huc12 = f"{tokens[4]}{tokens[5]}"
            if myhucs and huc12 not in myhucs:
                continue
        for fn in files:
            if not fn.endswith(".prj"):
                continue
            yield f"{root}/{fn}"


def prj_job(fn) -> bool:
    """Process this proj!"""
    mydir = threading.current_thread().tmpdir
    testfn = os.path.basename(fn)[:-4]
    cmd = [EXE, fn, testfn, f"{mydir}/wepp", "no"]
    with subprocess.Popen(
        cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, cwd=mydir
    ) as proc:
        # Need to block the above
        stdout = proc.stdout.read()
        stderr = proc.stderr.read()
        if not os.path.isfile(f"{mydir}/{testfn}.man"):
            print("bzzzz", testfn)
            print(" ".join(cmd))
            print(stdout.decode("ascii"))
            print(stderr.decode("ascii"))
            return False
        # This generates .cli, .man, .run, .slp, .sol
        # We need the .man , .slp , .sol from this process
        # slp is generated in flowpath2prj
        for suffix in ["man", "sol"]:
            shutil.copyfile(
                f"{mydir}/{testfn}.{suffix}", fn.replace("prj", suffix)
            )
        for suffix in ["cli", "man", "run", "slp", "sol"]:
            os.unlink(f"{mydir}/{testfn}.{suffix}")
    return True


def setup_thread():
    """Ensure that we have temp folders and sym links constructed."""
    tmpdir = tempfile.mkdtemp()
    # Store the reference for later use
    threading.current_thread().tmpdir = tmpdir
    os.makedirs(f"{tmpdir}/wepp/runs", exist_ok=True)
    for dn in ["data", "output", "wepp", "weppwin"]:
        subprocess.call(
            ["ln", "-s", f"{PROJDIR}/wepp/{dn}"], cwd=f"{tmpdir}/wepp"
        )
    subprocess.call(["ln", "-s", f"{PROJDIR}/userdb"], cwd=tmpdir)


def main(argv):
    """Go Main Go."""
    scenario = int(argv[1])
    myhucs = []
    if os.path.isfile("myhucs.txt"):
        with open("myhucs.txt", encoding="utf8") as fh:
            myhucs = fh.read().split("\n")
        LOG.info("using HUC12s found in myhucs.txt...")
    # Need to run from project dir so local userdb is found
    os.chdir(PROJDIR)

    progress = tqdm(disable=not sys.stdout.isatty())

    with ThreadPool(CPUCOUNT, initializer=setup_thread) as pool:

        def _cb(res):
            """Callback."""
            if not res:
                LOG.warning("Abort")
                pool.terminate()
            progress.update()

        def _eb(error):
            """Erroback."""
            print(error)
            pool.terminate()

        total = 0
        for fn in find_prjs(scenario, myhucs):
            pool.apply_async(prj_job, (fn,), callback=_cb, error_callback=_eb)
            total += 1
        progress.reset(total=total)
        pool.close()
        pool.join()


if __name__ == "__main__":
    # Go Main Go
    main(sys.argv)
