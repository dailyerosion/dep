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
                # NB: we need to be careful here as we are dealing with
                # floating point values, so we do a bit of nudging
                # 0.5m is within the resolution of the data (3m)
                x0 = ofe["x"][0] - 0.5
                x1 = ofe["x"][-1] + 0.5
                cursor.execute(
                    "UPDATE flowpath_points p SET ofe = %s FROM flowpaths f "
                    "where p.flowpath = f.fid and p.scenario = %s and "
                    "f.huc_12 = %s and f.fpath = %s and p.length >= %s and "
                    "p.length < %s",
                    (
                        i + 1,  # store OFE as 1-based
                        scenario,
                        huc12,
                        fpath,
                        x0,
                        x1,
                    ),
                )
                updates += cursor.rowcount
                if cursor.rowcount == 0:
                    LOG.info("no points found %s %s [%s-%s]", i, slpfn, x0, x1)
                    return
            # Update flowpaths now as well
            cursor.execute(
                "UPDATE flowpaths SET ofe_count = %s WHERE scenario = %s and "
                "huc_12 = %s and fpath = %s",
                (len(slp), scenario, huc12, fpath),
            )
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
