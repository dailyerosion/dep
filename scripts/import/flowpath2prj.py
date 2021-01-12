"""Generate the WEPP prj files based on what our database has for us.

Here's a listing of project landuse codes used

                     No-till (1)   (2-5)
  B - Soy               B1          B25    IniCropDef.Default
  F - forest            F1          F25    IniCropDef.Tre_2239
  G - Sorghum
  P - Pasture           P1          P25    IniCropDef.gra_3425
  C - Corn              C1          C25    IniCropDef.Default
  R - Other crops       R1          R25    IniCropDef.Aft_12889
  T - Water (could have flooded out for one year, wetlands)
  U - Developed
  X - Unclassified
  I - Idle
  L - Double Crop  (started previous year)
  W - Wheat
  N - Small Grain
  E - Sugarbeets
  J - Rice
  N - Cotton
  a - Nuts
  d - Fruit
  g - Small Grains
  m - Legumes
  o - Oilseed
  p - Grapes
  q - Orchards
  v - Vegetables


"""
from __future__ import print_function
import copy
import sys
import os
import datetime
from functools import partial
from math import atan2, degrees, pi

import psycopg2.extras
from tqdm import tqdm
from pyiem.util import get_dbconn, logger
from pyiem.dep import load_scenarios

LOG = logger()
MISSED_SOILS = {}
MAX_SLOPE_RATIO = 0.9
MIN_SLOPE = 0.003
PGCONN = get_dbconn("idep")
cursor = PGCONN.cursor(cursor_factory=psycopg2.extras.DictCursor)
cursor2 = PGCONN.cursor(cursor_factory=psycopg2.extras.DictCursor)
cursor3 = PGCONN.cursor(cursor_factory=psycopg2.extras.DictCursor)

surgo2file = {}
cursor.execute("SELECT surgo, soilfile from xref_surgo")
for _row in cursor:
    surgo2file[_row[0]] = _row[1]

# Note that the default used below is
INITIAL_COND_DEFAULT = "IniCropDef.Default"
INITIAL_COND = {
    "F": "IniCropDef.Tre_2239",
    "P": "IniCropDef.gra_3425",
    "R": "IniCropDef.Aft_12889",
}
WHEAT_PLANT = {
    "KS_SOUTH": datetime.date(2000, 5, 25),
    "KS_CENTRAL": datetime.date(2000, 5, 25),
    "KS_NORTH": datetime.date(2000, 5, 25),
    "IA_SOUTH": datetime.date(2000, 5, 12),
    "IA_CENTRAL": datetime.date(2000, 5, 17),
    "IA_NORTH": datetime.date(2000, 5, 23),
}

SOYBEAN_PLANT = {
    "KS_SOUTH": datetime.date(2000, 5, 25),
    "KS_CENTRAL": datetime.date(2000, 5, 25),
    "KS_NORTH": datetime.date(2000, 5, 25),
    "IA_SOUTH": datetime.date(2000, 5, 12),
    "IA_CENTRAL": datetime.date(2000, 5, 17),
    "IA_NORTH": datetime.date(2000, 5, 23),
}
CORN_PLANT = {
    "KS_SOUTH": datetime.date(2000, 4, 20),
    "KS_CENTRAL": datetime.date(2000, 4, 25),
    "KS_NORTH": datetime.date(2000, 4, 30),
    "IA_SOUTH": datetime.date(2000, 4, 30),
    "IA_CENTRAL": datetime.date(2000, 5, 5),
    "IA_NORTH": datetime.date(2000, 5, 10),
}
CORN = {
    "KS_SOUTH": "CropDef.Cor_0964",
    "KS_CENTRAL": "CropDef.Cor_0964",
    "KS_NORTH": "CropDef.Cor_0964",
    "IA_SOUTH": "CropDef.Cor_0965",
    "IA_CENTRAL": "CropDef.Cor_0966",
    "IA_NORTH": "CropDef.Cor_0967",
}
SOYBEAN = {
    "KS_SOUTH": "CropDef.Soy_2191",
    "KS_CENTRAL": "CropDef.Soy_2191",
    "KS_NORTH": "CropDef.Soy_2191",
    "IA_SOUTH": "CropDef.Soy_2192",
    "IA_CENTRAL": "CropDef.Soy_2193",
    "IA_NORTH": "CropDef.Soy_2194",
}


def read_file(scenario, zone, prevcode, code, cfactor, year):
    """Read a block file and do replacements

    Args:
      scenario (int): The DEP scenario
      zone (str): The DEP cropping zone
      prevcode (str): the previous crop code
      code (str): the crop code
      cfactor (int): the c-factor for tillage
      year (int): the year of this crop

    Returns:
      str with the raw data used for the .rot file
    """
    cfactor = 25 if cfactor != 1 else 1
    blockfn = "blocks/%s%s.txt" % (code, cfactor)
    if not os.path.isfile(blockfn):
        # LOG.debug("Missing %s", blockfn)
        return ""
    data = open(blockfn, "r").read()
    # Special consideration for planting alfalfa
    if code == "P" and prevcode != "P":
        # Best we can do now is plant it on Apr 15, sigh
        data = (
            "4  15 %s  1 Plant-Perennial CropDef.ALFALFA  {0.000000}\n%s"
        ) % (year, data)
    pdate = ""
    pdatem5 = ""
    pdatem10 = ""
    plant = ""
    # We currently only have zone specific files for Corn and Soybean
    if code == "C":
        date = CORN_PLANT.get(scenario, CORN_PLANT[zone])
        pdate = date.strftime("%m    %d")
        pdatem5 = (date - datetime.timedelta(days=5)).strftime("%m    %d")
        pdatem10 = (date - datetime.timedelta(days=10)).strftime("%m    %d")
        plant = CORN[zone]
    elif code == "B":
        date = SOYBEAN_PLANT.get(scenario, SOYBEAN_PLANT[zone])
        pdate = date.strftime("%m    %d")
        pdatem5 = (date - datetime.timedelta(days=5)).strftime("%m    %d")
        pdatem10 = (date - datetime.timedelta(days=10)).strftime("%m    %d")
        plant = SOYBEAN[zone]
    elif code == "W":
        date = WHEAT_PLANT[zone]
        pdate = date.strftime("%m    %d")
        pdatem5 = (date - datetime.timedelta(days=5)).strftime("%m    %d")
        pdatem10 = (date - datetime.timedelta(days=10)).strftime("%m    %d")
    return data % {
        "yr": year,
        "pdate": pdate,
        "pdatem5": pdatem5,
        "pdatem10": pdatem10,
        "plant": plant,
    }


def do_rotation(scenario, zone, rotfn, landuse, management):
    """Create the rotation file.

    Args:
      scenario (int): The DEP scenario
      zone (str): The DEP cropping zone
      rotfn (str): The rotation file to generate.
      landuse (str): the landuse rotation string.
      management (str): the management rotation string.

    Returns:
      None
    """
    # Dictionary of values used to fill out the file template below
    data = {}
    data["date"] = datetime.datetime.now()
    data["name"] = "%s-%s" % (landuse, management)
    data["initcond"] = INITIAL_COND.get(landuse[0], INITIAL_COND_DEFAULT)
    prevcode = "C" if landuse[0] not in INITIAL_COND else landuse[0]
    f = partial(read_file, scenario, zone)
    # 2007
    data["year1"] = f(prevcode, landuse[0], int(management[0]), 1)
    for i in range(1, 15):
        data["year%s" % (i + 1,)] = f(
            landuse[i - 1], landuse[i], int(management[i]), i + 1
        )

    with open(rotfn, "w") as fh:
        fh.write(
            """#
# WEPP rotation saved on: %(date)s
#
# Created with scripts/import/flowpath2prj.py
#
Version = 98.7
Name = %(name)s
Description {
}
Color = 0 255 0
LandUse = 1
InitialConditions = %(initcond)s

Operations {
%(year1)s
%(year2)s
%(year3)s
%(year4)s
%(year5)s
%(year6)s
%(year7)s
%(year8)s
%(year9)s
%(year10)s
%(year11)s
%(year12)s
%(year13)s
%(year14)s
%(year15)s
}
"""
            % data
        )
    return True


def rotation_magic(scenario, zone, seqnum, row, metadata):
    """Rotation Magic happens here.

    Generates the needed prj2wepp rotation file and then returns the name of
    that file.

    Args:
      scenario (int): The DEP scenario we are on.
      zone (str): the cropping zone we are in.
      seqnum (int): the sequential number of this .rot file we generate
      row (dict): the database info for this row.
    """
    rotfn = "/i/%s/rot/%s/%s/%s_%s_%s.rot" % (
        scenario,
        metadata["huc_12"][:8],
        metadata["huc_12"][8:],
        metadata["huc_12"],
        metadata["fpath"],
        seqnum,
    )
    # Oh my cats, we are about to create the .rot file here
    do_rotation(scenario, zone, rotfn, row["landuse"], row["management"])
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
    # NB we used to have a check here that dx was non-zero, but this should
    # never happen now.
    # dailyerosion/dep#79 denotes some limits on WEPP precision
    return max(MIN_SLOPE, dy / dx)


def simplify(rows):
    """ WEPP can only handle 20 slope points it seems, so we must simplify """
    newrows = []
    lrow = rows[0]
    newrows.append(lrow)
    for i, row in enumerate(rows):
        # Throw out points that have Urban landuse in at least 3 years
        if row["landuse"].count("U") > 2:
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
    cursor3.execute("DELETE from flowpath_points where flowpath = %s", (fid,))
    cursor3.execute("DELETE from flowpaths where fid = %s", (fid,))
    if cursor3.rowcount != 1:
        print("Whoa, delete_flowpath failed for %s" % (fid,))


def do_flowpath(scenario, zone, metadata):
    """ Process a given flowpathid """
    # slope = compute_slope(fid)
    # I need bad soilfiles so that the length can be computed
    cursor2.execute(
        """
        SELECT segid, elevation, length, f.surgo,
        slope, management, 'DEP_'||surgo||'.SOL' as soilfile, landuse,
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
        if row["slope"] < MIN_SLOPE:
            row["slope"] = MIN_SLOPE
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

    soil = rows[0]["surgo"]
    soilstart = 0
    soils = []
    soillengths = []

    for i, row in enumerate(rows):
        if soil != row["surgo"] or i == (len(rows) - 1):
            soils.append(soil)
            soillengths.append(row["length"] - soilstart)
            soil = row["surgo"]
            soilstart = row["length"]
        # NEED lots of precision to get grid rectifying right
        # see dailyerosion/dep#79
        slpdata += " %s,%.5f" % (row["length"] / res["length"], row["slope"])

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

    prev_landuse = rows[0]["landuse"]
    manstart = 0
    prev_man = rows[0]["management"]
    mans = []
    manlengths = []

    # Figure out our landuse situation
    for i, row in enumerate(rows):
        if (
            prev_landuse == row["landuse"]
            and prev_man == row["management"]
            and i != (len(rows) - 1)
        ):
            continue
        # Management has changed, write out the old row
        mans.append(
            rotation_magic(scenario, zone, len(mans), rows[i - 1], metadata)
        )
        manlengths.append(row["length"] - manstart)
        prev_landuse = row["landuse"]
        prev_man = row["management"]
        manstart = row["length"]

    if not mans:
        LOG.info(
            "%s,%s has no managements, skipping",
            metadata["huc_12"],
            metadata["fpath"],
        )
        return
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
   File = "/i/0/cli/096x040/096.01x040.60.cli"
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
   SimulationYears = 15
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
    progress = tqdm(cursor, total=cursor.rowcount)
    for row in progress:
        # continue
        if myhucs and row["huc_12"] not in myhucs:
            continue
        progress.set_description("%s %4s" % (row[3], row[1]))
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
