"""Use what prj2wepp got for OFEs back into the database."""
import os
import sys
import glob

from tqdm import tqdm
import geopandas as gpd
import pandas as pd
from pyiem.dep import read_slp
from pyiem.util import logger, get_dbconn, get_sqlalchemy_conn
from shapely.geometry import LineString, Point

LOG = logger()
PROJDIR = "/opt/dep/prj2wepp"
EXE = f"{PROJDIR}/prj2wepp"
WEPP = f"{PROJDIR}/wepp"


def cut(line, distance):
    """Cuts a line in two at a distance from its starting point."""
    if distance <= 0.0 or distance >= line.length:
        return [LineString(line), None]
    coords = list(line.coords)
    for i, p in enumerate(coords):
        pp = line.project(Point(p))
        if pp == distance:
            return [LineString(coords[: i + 1]), LineString(coords[i:])]
        if pp > distance:
            cp = line.interpolate(distance)
            return [
                LineString(coords[:i] + [(cp.x, cp.y)]),
                LineString([(cp.x, cp.y)] + coords[i:]),
            ]
    return [None, None]


def main(argv):
    """Go Main Go."""
    scenario = int(argv[1])
    # Build df of current flowpaths for later splitting
    with get_sqlalchemy_conn("idep") as conn:
        flowpaths = gpd.read_postgis(
            "SELECT fid, geom from flowpaths where scenario = %s",
            conn,
            params=(scenario,),
            geom_col="geom",
            index_col="fid",
        )

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
            fpath = int(os.path.basename(slpfn).split(".")[0].split("_")[1])
            slp = read_slp(slpfn)
            # Find the flowpath fid
            cursor.execute(
                "SELECT fid from flowpaths where scenario = %s and "
                "huc_12 = %s and fpath = %s",
                (scenario, huc12, fpath),
            )
            fid = cursor.fetchone()[0]
            # Remove previous content :/
            cursor.execute(
                "DELETE from flowpath_ofes where flowpath = %s", (fid,)
            )
            # Get the flowpath geom
            line = flowpaths.at[fid, "geom"]
            traveled = 0
            for ofenum, ofe in enumerate(slp, start=1):
                total_ofes += 1
                # NB: we need to be careful here as we are dealing with
                # floating point values, so we do a bit of nudging
                # 0.5m is within the resolution of the data (3m)
                x0 = ofe["x"][0] - 0.5
                # Last OFE should be aggressive, b-e aggressive
                x1 = ofe["x"][-1] + (0.5 if len(slp) == ofenum else -0.5)
                cursor.execute(
                    """
                    UPDATE flowpath_points SET ofe = %s where
                    flowpath = %s and length >= %s and length < %s
                    returning gssurgo_id, length
                    """,
                    (
                        ofenum,
                        fid,
                        x0,
                        x1,
                    ),
                )
                updates += cursor.rowcount
                if cursor.rowcount == 0:
                    LOG.info("no pts %s %s [%s-%s]", ofenum, slpfn, x0, x1)
                    return
                # NB see dailyerosion/dep#151 for why we can't trust last pt
                surgos = pd.DataFrame(
                    cursor.fetchall(), columns=["gssurgo_id", "length"]
                ).sort_values("length", ascending=True)
                if len(surgos.index) > 1:
                    surgos = surgos.iloc[:-1]
                if len(surgos["gssurgo_id"].unique()) > 1:
                    print(surgos, ofenum, fid)
                    sys.exit()
                # OFE geometry work
                (ofeline, line) = cut(line, ofe["x"][-1] - traveled)
                bs = (ofe["y"][0] - ofe["y"][-1]) / (
                    ofe["x"][-1] - ofe["x"][0]
                )
                cursor.execute(
                    """
                    INSERT into flowpath_ofes
                    (flowpath, ofe, geom, scenario, bulk_slope, gssurgo_id)
                    VALUES(%s,%s,%s,%s,%s, %s)
                    """,
                    (
                        fid,
                        ofenum,
                        ofeline.wkt,
                        scenario,
                        bs,
                        surgos["gssurgo_id"].values[0],
                    ),
                )

                traveled = ofe["x"][-1]
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
