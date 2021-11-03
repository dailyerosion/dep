"""Use what prj2wepp got for OFEs back into the database."""
import os
import sys
import glob

from tqdm import tqdm
from pyiem.dep import read_slp
from pyiem.util import logger, get_dbconn

LOG = logger()
PROJDIR = "/opt/dep/prj2wepp"
EXE = f"{PROJDIR}/prj2wepp"
WEPP = f"{PROJDIR}/wepp"


def main(argv):
    """Go Main Go."""
    scenario = int(argv[1])
    basedir = f"/i/{scenario}/slp"
    with open("myhucs.txt", encoding="utf8") as fh:
        myhucs = fh.read().split("\n")
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()
    for huc12 in tqdm(myhucs):
        for slpfn in glob.glob(f"{basedir}/{huc12[:8]}/{huc12[8:]}/*.slp"):
            fpath = os.path.basename(slpfn).split(".")[0].split("_")[1]
            slp = read_slp(slpfn)
            for i, ofe in enumerate(slp):
                cursor.execute(
                    "UPDATE flowpath_points p SET ofe = %s FROM flowpaths f "
                    "where p.flowpath = f.fid and p.scenario = %s and "
                    "f.huc_12 = %s and f.fpath = %s and p.length >= %s and "
                    "p.length < %s",
                    (i, scenario, huc12, fpath, ofe["x"][0], ofe["x"][-1]),
                )
                if cursor.rowcount == 0:
                    LOG.info("no points updated %s %s", i, slpfn)
                    return
    cursor.close()
    pgconn.commit()


if __name__ == "__main__":
    # Go Main Go
    main(sys.argv)
