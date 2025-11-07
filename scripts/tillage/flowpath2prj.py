"""Generate the WEPP prj files based on what our database has for us"""

import copy
import datetime
import os
import sys
from math import atan2, degrees, pi

from psycopg.rows import dict_row
from pyiem.database import get_dbconn
from tqdm import tqdm

from pydep.util import get_cli_fname

SCENARIO = int(sys.argv[1])
TILLAGE_CLASS = int(sys.argv[2])
MISSED_SOILS = {}
PGCONN = get_dbconn("idep")
cursor = PGCONN.cursor(row_factory=dict_row)
cursor2 = PGCONN.cursor(row_factory=dict_row)
cursor3 = PGCONN.cursor(row_factory=dict_row)


def get_rotation(code):
    """Convert complex things into a simple WEPP management for now"""
    return "tillage_issue63/IA_CENTRAL/%s/%s/%s-%s.rot" % (
        code[:2],
        code[2:4],
        code,
        TILLAGE_CLASS,
    )


def compute_aspect(x0, y0, x1, y1):
    """Compute the aspect angle between two points"""
    dx = x1 - x0
    dy = y1 - y0
    rads = atan2(-dy, dx)
    rads %= 2 * pi
    return degrees(rads)


def non_zero(dy, dx):
    """Make sure slope is slightly non-zero"""
    if dx == 0:
        return 0.00001
    return max(0.00001, dy / dx)


def simplify(rows):
    """WEPP can only handle 20 slope points it seems, so we must simplify"""
    newrows = []
    lrow = rows[0]
    newrows.append(lrow)
    for _, row in enumerate(rows):
        # If they are the 'same', continue
        if row["landuse"] == "UUUUUUUUUU":
            continue
        if (
            row["management"] == lrow["management"]
            and row["surgo"] == lrow["surgo"]
            and row["landuse"] == lrow["landuse"]
        ):
            continue
        # Recompute slope
        dy = lrow["elevation"] - row["elevation"]
        dx = row["length"] - lrow["length"]
        row["slope"] = non_zero(dy, dx)
        newrows.append(copy.deepcopy(row))
        lrow = row

    if newrows[-1]["segid"] != rows[-1]["segid"]:
        # Recompute slope
        dy = newrows[-1]["elevation"] - rows[-1]["elevation"]
        dx = rows[-1]["length"] - newrows[-1]["length"]
        newrows.append(copy.deepcopy(rows[-1]))
        newrows[-1]["slope"] = non_zero(dy, dx)

    if len(newrows) < 20:
        return newrows

    # Brute force!
    threshold = 0.01
    while len(newrows) > 19:
        if threshold > 0.1:
            print(
                ("threshold: %.2f len(newrows): %s")
                % (threshold, len(newrows))
            )
            for row in newrows:
                print(len(row))
            return newrows[:20]
        newrows2 = []
        newrows2.append(copy.deepcopy(newrows[0]))
        for i in range(1, len(newrows) - 1):
            if newrows[i]["slope"] > threshold:
                newrows2.append(copy.deepcopy(newrows[i]))
        newrows2.append(copy.deepcopy(newrows[-1]))
        newrows = copy.deepcopy(newrows2)
        threshold += 0.01

    # TODO: recompute the slopes

    if len(newrows) > 19:
        print("Length of old: %s" % (len(rows),))
        for row in rows:
            print(
                (
                    "%(segid)s %(length)s %(elevation)s %(landuse)s "
                    "%(surgo)s %(management)s %(slope)s"
                )
                % row
            )

        print("Length of new: %s" % (len(newrows),))
        for row in newrows:
            print(
                (
                    "%(segid)s %(length)s %(elevation)s %(landuse)s "
                    "%(surgo)s %(management)s %(slope)s"
                )
                % row
            )

        sys.exit()

    return newrows


def compute_slope(fid):
    """Compute the simple slope for the fid"""
    cursor2.execute(
        """SELECT max(elevation), min(elevation), max(length)
    from flowpath_points where flowpath = %s and length < 9999
    and scenario = %s""",
        (fid, SCENARIO),
    )
    row2 = cursor2.fetchone()
    return (row2[0] - row2[1]) / row2[2]


def do_flowpath(zone, huc_12, fid, fpath):
    """Process a given flowpathid"""
    # I need bad soilfiles so that the length can be computed
    cursor2.execute(
        """SELECT segid, elevation, length, f.surgo,
    slope, management, 'MWDEP_'||surgo||'.SOL' as soilfile, landuse,
    round(ST_X(ST_Transform(geom,4326))::numeric,2) as x,
    round(ST_Y(ST_Transform(geom,4326))::numeric,2) as y from
    flowpath_points f
    WHERE flowpath = %s and length < 9999 and scenario = 0
    ORDER by segid ASC""",
        (fid,),
    )
    rows = []
    x = None
    y = None
    maxmanagement = 0
    for row in cursor2:
        if row["slope"] < 0:
            print("%s,%s had a negative slope, deleting!" % (huc_12, fpath))
            return None
        if row["soilfile"] == "MWDEP_9999.SOL":
            continue
        if not os.path.isfile("/i/0/sol_input/%s" % (row["soilfile"],)):
            if row["soilfile"] not in MISSED_SOILS:
                print("Missing soilfile: %s" % (row["soilfile"],))
                MISSED_SOILS[row["soilfile"]] = 0
            MISSED_SOILS[row["soilfile"]] += 1
            continue
        if x is None:
            x = row["x"]
            y = row["y"]
        if row["management"] > maxmanagement:
            maxmanagement = row["management"]
        if row["slope"] < 0.00001:
            row["slope"] = 0.00001
        rows.append(row)

    if x is None:
        print("%s,%s had no valid soils, deleting" % (huc_12, fpath))
        return None
    if len(rows) < 2:
        print("%s,%s had only 1 row of data, deleting" % (huc_12, fpath))
        return None
    if len(rows) > 19:
        rows = simplify(rows)

    maxslope = 0
    for row in rows:
        if row["slope"] > maxslope:
            maxslope = row["slope"]
    if maxslope > 1:
        s = compute_slope(fid)
        print(
            "%s %3i %4.1f %5.1f %5.1f"
            % (huc_12, fpath, maxslope, rows[-1]["length"], s)
        )

    if rows[-1]["length"] < 1:
        print("%s,%s has zero length, deleting" % (huc_12, fpath))
        return None

    res = {}
    res["clifile"] = get_cli_fname(x, y, 0)
    cursor3.execute(
        """
        UPDATE flowpaths SET climate_file = %s
        WHERE fpath = %s and huc_12 = %s and scenario = %s
    """,
        (res["clifile"], fpath, huc_12, SCENARIO),
    )

    res["huc8"] = huc_12[:8]
    res["huc12"] = huc_12
    res["envfn"] = "/i/%s/env/%s/%s_%s.env" % (
        SCENARIO,
        res["huc8"],
        huc_12,
        fpath,
    )
    res["date"] = datetime.datetime.now()
    res["aspect"] = compute_aspect(
        rows[0]["x"], rows[0]["y"], rows[-1]["x"], rows[-1]["y"]
    )
    res["prj_fn"] = "/i/%s/prj/%s/%s/%s_%s.prj" % (
        SCENARIO,
        res["huc8"],
        huc_12[-4:],
        huc_12,
        fpath,
    )
    res["length"] = rows[-1]["length"]
    res["slope_points"] = len(rows)

    # Iterate over the rows and figure out the slopes and distance fracs
    slpdata = ""
    if rows[0]["length"] != 0:
        print(
            ("WARNING: HUC12:%s FPATH:%s had missing soil at top of slope")
            % (huc_12, fpath)
        )
        slpdata = " 0.000,0.00001"
        res["slope_points"] = len(rows) + 1
    prevsoil = None
    lsoilstart = 0
    soils = []
    soillengths = []

    for row in rows:
        if prevsoil != row["surgo"]:
            if prevsoil is not None:
                soils.append(prevsoil)
                soillengths.append(row["length"] - lsoilstart)
            prevsoil = row["surgo"]
            lsoilstart = row["length"]
        if res["length"] == 0:
            continue
        slpdata += " %.3f,%.5f" % (row["length"] / res["length"], row["slope"])
    soils.append(prevsoil)
    soillengths.append(res["length"] - lsoilstart)

    res["soilbreaks"] = len(soillengths) - 1
    res["soils"] = ""
    res["slpdata"] = slpdata

    for d, s in zip(soillengths, soils, strict=False):
        res["soils"] += """    %s {
        Distance = %.3f
        File = "/i/0/sol_input/MWDEP_%s.SOL"
    }\n""" % (
            s,
            d,
            s,
        )

    prevman = None
    lmanstart = 0
    mans = []
    manlengths = []

    for row in rows:
        if row["landuse"] is None:
            continue
        if prevman is None or prevman != row["landuse"]:
            if prevman is not None:
                mans.append(get_rotation(prevman))
                manlengths.append(row["length"] - lmanstart)
            prevman = row["landuse"]
            lmanstart = row["length"]

    if prevman is None:
        print("%s,%s has no managements, skipping" % (huc_12, fpath))
        return None
    mans.append(get_rotation(prevman))
    manlengths.append(res["length"] - lmanstart)
    res["manbreaks"] = len(manlengths) - 1
    res["managements"] = ""

    for d, s in zip(manlengths, mans, strict=False):
        res["managements"] += """    %s {
        Distance = %.3f
        File = "%s"
    }\n""" % (
            s,
            d,
            s,
        )

    return res


def write_prj(data):
    """Create the WEPP prj file"""
    # Profile format
    # [x] The first number is the hillslope aspect,
    # [?] the second is the profile width in meters.
    # [x] The next line contains the number of slope points
    # [x] and the total distance in meters.
    # [x] The last line contains the fraction of the distance down the slope
    # [x] and the slope at that point.
    with open(data["prj_fn"], "w") as fp:
        fp.write(
            """#
# WEPP project written: %(date)s
#
Version = 98.6
Name = default
Comments {
Example hillslope in Iowa.
}
Units = English
Landuse = 1
Length = %(length).4f
Profile {
    Data {
        %(aspect).4f  1.0
        %(slope_points)s  %(length).4f
        %(slpdata)s
    }
}
Climate {
   # Unused anyway, so just fake it
   File = "/i/0/cli/096x040/096.01x039.88.cli"
}
Soil {
   Breaks = %(soilbreaks)s
%(soils)s
}
Management {
   Breaks = %(manbreaks)s
%(managements)s
}
RunOptions {
   Version = 1
   SoilLossOutputType = 1
   EventFile = "%(envfn)s"
   WaterBalanceFile = "test.wb"
   SimulationYears = 7
   SmallEventByPass = 1
}
"""
            % data
        )


def main(argv):
    """Go main go"""
    cursor.execute(
        """
        WITH scenario0 as (
            SELECT huc_12, fpath, fid from flowpaths
            where scenario = 0
        )
        SELECT ST_ymax(ST_Transform(geom, 4326)) as lat,
        s.fpath, s.fid, s.huc_12 from flowpaths f JOIN scenario0 s ON
        (f.fpath = s.fpath and f.huc_12 = s.huc_12)
        WHERE scenario = %s and f.fpath != 0
    """,
        (SCENARIO,),
    )
    for row in tqdm(cursor, total=cursor.rowcount):
        zone = "IA_CENTRAL"
        data = do_flowpath(zone, row["huc_12"], row["fid"], row["fpath"])
        if data is not None:
            write_prj(data)


if __name__ == "__main__":
    main(sys.argv)
    cursor3.close()
    PGCONN.commit()
    for fn in MISSED_SOILS:
        print("%6s %s" % (MISSED_SOILS[fn], fn))
