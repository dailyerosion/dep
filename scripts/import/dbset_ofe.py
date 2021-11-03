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
        myhucs = [x.strip() for x in fh]
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()
    total_ofes = 0
    updates = 0
    total_flowpaths = 0
    for huc12 in tqdm(myhucs):
        for slpfn in glob.glob(f"{basedir}/{huc12[:8]}/{huc12[8:]}/*.slp"):
            total_flowpaths += 1
            fpath = os.path.basename(slpfn).split(".")[0].split("_")[1]
            slp = read_slp(slpfn)
            for i, ofe in enumerate(slp):
                total_ofes += 1
                cursor.execute(
                    "UPDATE flowpath_points p SET ofe = %s FROM flowpaths f "
                    "where p.flowpath = f.fid and p.scenario = %s and "
                    "f.huc_12 = %s and f.fpath = %s and p.length >= %s and "
                    "p.length < %s",
                    (i, scenario, huc12, fpath, ofe["x"][0], ofe["x"][-1]),
                )
                updates += cursor.rowcount
                if cursor.rowcount == 0:
                    LOG.info("no points updated %s %s", i, slpfn)
                    return
    cursor.close()
    pgconn.commit()
    LOG.info(
        "Assigned %s OFEs to %s flowpaths over %s points",
        total_ofes,
        total_flowpaths,
        updates,
    )


if __name__ == "__main__":
    # Go Main Go
    main(sys.argv)
