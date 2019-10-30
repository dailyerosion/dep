"""Generate the WEPP prj files based on what our database has for us"""
from __future__ import print_function
import copy
import sys
import os
import datetime
from math import atan2, degrees, pi

import psycopg2.extras
from tqdm import tqdm
from pyiem.util import get_dbconn, logger
from pyiem.dep import load_scenarios

LOG = logger()
MISSED_SOILS = {}
MAX_SLOPE_RATIO = 0.9
PGCONN = get_dbconn("idep")
cursor = PGCONN.cursor(cursor_factory=psycopg2.extras.DictCursor)
cursor2 = PGCONN.cursor(cursor_factory=psycopg2.extras.DictCursor)
cursor3 = PGCONN.cursor(cursor_factory=psycopg2.extras.DictCursor)

surgo2file = {}
cursor.execute("SELECT surgo, soilfile from xref_surgo")
for _row in cursor:
    surgo2file[_row[0]] = _row[1]


def get_rotation(scenario, zone, code, maxmanagement):
    """ Convert complex things into a simple WEPP management for now """
    rotfn = "%s/%s/%s/%s/%s-%s.rot" % (
        "IDEP2" if scenario == 0 else "SCEN%s" % (scenario,),
        zone,
        code[:2],
        code[2:4],
        code,
        "1" if maxmanagement == 1 else "25",
    )
    return rotfn


def compute_aspect(x0, y0, x1, y1):
    """ Compute the aspect angle between two points """
    dx = x1 - x0
    dy = y1 - y0
    rads = atan2(-dy, dx)
    rads %= 2 * pi
    return degrees(rads)


def non_zero(dy, dx):
    """ Make sure slope is slightly non-zero """
    if dx == 0:
        return 0.00001
    return max(0.00001, dy / dx)


def simplify(rows):
    """ WEPP can only handle 20 slope points it seems, so we must simplify """
    newrows = []
    lrow = rows[0]
    newrows.append(lrow)
    for i, row in enumerate(rows):
        # If they are the 'same', continue
        if row["lstring"] == "UUUUUUUUUU":
            continue
        if (
            row["management"] == lrow["management"]
            and row["surgo"] == lrow["surgo"]
            and row["lstring"] == lrow["lstring"]
        ):
            continue
        # print 'Add row %s' % (i,)
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
                    "%(segid)s %(length)s %(elevation)s %(lstring)s "
                    "%(surgo)s %(management)s %(slope)s"
                )
                % row
            )

        print("Length of new: %s" % (len(newrows),))
        for row in newrows:
            print(
                (
                    "%(segid)s %(length)s %(elevation)s %(lstring)s "
                    "%(surgo)s %(management)s %(slope)s"
                )
                % row
            )

        sys.exit()

    return newrows


def compute_slope(fid):
    """ Compute the simple slope for the fid """
    cursor2.execute(
        """
        SELECT max(elevation), min(elevation), max(length)
        from flowpath_points where flowpath = %s and length < 9999
    """,
        (fid,),
    )
    row2 = cursor2.fetchone()
    return (row2[0] - row2[1]) / row2[2]


def delete_flowpath(fid):
    """ remove this flowpath as its invalid """
    cursor3.execute(
        """
        DELETE from flowpath_points where flowpath = %s
    """,
        (fid,),
    )
    cursor3.execute(
        """
        DELETE from flowpaths where fid = %s
    """,
        (fid,),
    )
    if cursor3.rowcount != 1:
        print("Whoa, delete_flowpath failed for %s" % (fid,))


def do_flowpath(scenario, zone, metadata):
    """ Process a given flowpathid """
    # slope = compute_slope(fid)
    # I need bad soilfiles so that the length can be computed
    cursor2.execute(
        """
        SELECT segid, elevation, length, f.surgo,
        slope, management, 'DEP_'||surgo||'.SOL' as soilfile,
        lu2007 || lu2008 || lu2009 ||
        lu2010 || lu2011 || lu2012 || lu2013 || lu2014 || lu2015 ||
        lu2016 || lu2017 || lu2018 || lu2019 as lstring,
        round(ST_X(ST_Transform(geom,4326))::numeric,2) as x,
        round(ST_Y(ST_Transform(geom,4326))::numeric,2) as y from
        flowpath_points f
        WHERE flowpath = %s and length < 9999
        ORDER by segid ASC
    """,
        (metadata["fid"],),
    )
    rows = []
    x = None
    # y = None
    maxmanagement = 0
    for row in cursor2:
        if row["slope"] < 0:
            LOG.info(
                "%s,%s had a negative slope, deleting!",
                metadata["huc_12"],
                metadata["fpath"],
            )
            delete_flowpath(metadata["fid"])
            return None
        if row["soilfile"] == "DEP_9999.SOL":
            continue
        if not os.path.isfile(
            "/i/%s/sol_input/%s" % (scenario, row["soilfile"])
        ):
            if row["soilfile"] not in MISSED_SOILS:
                LOG.info("Missing soilfile: %s", row["soilfile"])
                MISSED_SOILS[row["soilfile"]] = 0
            MISSED_SOILS[row["soilfile"]] += 1
            continue
        if x is None:
            x = row["x"]
            # y = row['y']
        if row["management"] > maxmanagement:
            maxmanagement = row["management"]
        if row["slope"] < 0.00001:
            row["slope"] = 0.00001
        # hard coded...
        # row['slope'] = slope
        rows.append(row)

    if x is None:
        LOG.info(
            "%s,%s had no valid soils, deleting",
            metadata["huc_12"],
            metadata["fpath"],
        )
        delete_flowpath(metadata["fid"])
        return None
    if len(rows) < 2:
        LOG.info(
            "%s,%s had only 1 row of data, deleting",
            metadata["huc_12"],
            metadata["fpath"],
        )
        delete_flowpath(metadata["fid"])
        return None
    if len(rows) > 19:
        rows = simplify(rows)

    maxslope = 0
    for row in rows:
        if row["slope"] > maxslope:
            maxslope = row["slope"]
    if maxslope > MAX_SLOPE_RATIO:
        s = compute_slope(metadata["fid"])
        LOG.info(
            "Error max-slope>%s %s[%3i] max:%4.1f len:%5.1f bulk:%5.1f",
            MAX_SLOPE_RATIO,
            metadata["huc_12"],
            metadata["fpath"],
            maxslope,
            rows[-1]["length"],
            s,
        )
        delete_flowpath(metadata["fid"])
        return None

    if rows[-1]["length"] < 1:
        LOG.info(
            "%s,%s has zero length, deleting",
            metadata["huc_12"],
            metadata["fpath"],
        )
        delete_flowpath(metadata["fid"])
        return None

    res = {}
    res["clifile"] = metadata["climate_file"]

    # Store climate_file name with flowpath to make life easier
    cursor3.execute(
        """
        UPDATE flowpaths SET climate_file = %s
        WHERE fid = %s
    """,
        (res["clifile"], metadata["fid"]),
    )
    if cursor3.rowcount != 1:
        LOG.info("ERROR Updating climate_file for FID: %s", metadata["fid"])
    # return
    res["huc8"] = metadata["huc_12"][:8]
    res["huc12"] = metadata["huc_12"]
    res["envfn"] = "/i/%s/env/%s/%s_%s.env" % (
        scenario,
        res["huc8"],
        res["huc12"],
        metadata["fpath"],
    )
    res["date"] = datetime.datetime.now()
    res["aspect"] = compute_aspect(
        rows[0]["x"], rows[0]["y"], rows[-1]["x"], rows[-1]["y"]
    )
    res["prj_fn"] = "/i/%s/prj/%s/%s/%s_%s.prj" % (
        scenario,
        res["huc8"],
        res["huc12"][-4:],
        res["huc12"],
        metadata["fpath"],
    )
    res["length"] = rows[-1]["length"]
    res["slope_points"] = len(rows)

    # Iterate over the rows and figure out the slopes and distance fracs
    slpdata = ""
    if rows[0]["length"] != 0:
        LOG.info(
            "WARNING: HUC12:%s FPATH:%s had missing soil at top of slope",
            metadata["huc_12"],
            metadata["fpath"],
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

    for d, s in zip(soillengths, soils):
        res[
            "soils"
        ] += """    %s {
        Distance = %.3f
        File = "/i/%s/sol_input/DEP_%s.SOL"
    }\n""" % (
            s,
            d,
            scenario,
            s,
        )

    prevman = None
    lmanstart = 0
    mans = []
    manlengths = []

    for row in rows:
        if row["lstring"] is None:
            continue
        if prevman is None or prevman != row["lstring"]:
            if prevman is not None:
                mans.append(
                    get_rotation(scenario, zone, prevman, maxmanagement)
                )
                manlengths.append(row["length"] - lmanstart)
            prevman = row["lstring"]
            lmanstart = row["length"]

    if prevman is None:
        LOG.info(
            "%s,%s has no managements, skipping",
            metadata["huc_12"],
            metadata["fpath"],
        )
        return
    mans.append(get_rotation(scenario, zone, prevman, maxmanagement))
    manlengths.append(res["length"] - lmanstart)
    res["manbreaks"] = len(manlengths) - 1
    res["managements"] = ""

    for d, s in zip(manlengths, mans):
        res[
            "managements"
        ] += """    %s {
        Distance = %.3f
        File = "%s"
    }\n""" % (
            s,
            d,
            s,
        )

    return res


def write_prj(data):
    """ Create the WEPP prj file """
    # Profile format
    # [x] The first number is the hillslope aspect,
    # [?] the second is the profile width in meters.
    # [x] The next line contains the number of slope points
    # [x] and the total distance in meters.
    # [x] The last line contains the fraction of the distance down the slope
    # [x] and the slope at that point.
    with open(data["prj_fn"], "w") as fh:
        fh.write(
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
    """ Go main go """
    scenario = int(argv[1])
    sdf = load_scenarios()
    flowpath_scenario = int(sdf.at[scenario, "flowpath_scenario"])
    myhucs = []
    if os.path.isfile("myhucs.txt"):
        myhucs = open("myhucs.txt").read().split("\n")
        LOG.info("Only running for HUC_12s in myhucs.txt")
    cursor.execute(
        """
        SELECT ST_ymax(ST_Transform(geom, 4326)) as lat,
        fpath, fid, huc_12, climate_file from flowpaths
        WHERE scenario = %s and fpath != 0
    """,
        (flowpath_scenario,),
    )
    for row in tqdm(cursor, total=cursor.rowcount):
        # continue
        if myhucs and row["huc_12"] not in myhucs:
            continue
        zone = "KS_NORTH"
        if row["lat"] >= 42.5:
            zone = "IA_NORTH"
        elif row["lat"] >= 41.5:
            zone = "IA_CENTRAL"
        elif row["lat"] >= 40.5:
            zone = "IA_SOUTH"
        data = do_flowpath(scenario, zone, row)
        if data is not None:
            write_prj(data)


if __name__ == "__main__":
    main(sys.argv)
    cursor3.close()
    PGCONN.commit()
    for fn in MISSED_SOILS:
        print("%6s %s" % (MISSED_SOILS[fn], fn))
