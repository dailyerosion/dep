"""Construct building block management files

In the database, we construct a list of unique rotation strings and then
generate WEPP .rot files for each unique string.  These .rot files are later
used by prj2wepp to generate the .man files.

  python build_management.py <scenario> <optional_to_overwrite>

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
import os
import datetime
import sys

from tqdm import tqdm
from pyiem.util import get_dbconn, logger
from pyiem.dep import load_scenarios

LOG = logger()
OVERWRITE = True
if len(sys.argv) == 2:
    LOG.info("WARNING: This does not overwrite old files!")
    OVERWRITE = False

PGCONN = get_dbconn("idep")

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
    59: datetime.date(2000, 4, 15),
    60: datetime.date(2000, 4, 20),
    61: datetime.date(2000, 4, 25),
    62: datetime.date(2000, 4, 30),
    63: datetime.date(2000, 5, 5),
    64: datetime.date(2000, 5, 10),
    65: datetime.date(2000, 5, 15),
    66: datetime.date(2000, 5, 20),
    67: datetime.date(2000, 5, 25),
    68: datetime.date(2000, 5, 30),
    69: datetime.date(2000, 6, 4),
    "KS_SOUTH": datetime.date(2000, 5, 25),
    "KS_CENTRAL": datetime.date(2000, 5, 25),
    "KS_NORTH": datetime.date(2000, 5, 25),
    "IA_SOUTH": datetime.date(2000, 5, 12),
    "IA_CENTRAL": datetime.date(2000, 5, 17),
    "IA_NORTH": datetime.date(2000, 5, 23),
}
CORN_PLANT = {
    59: datetime.date(2000, 4, 10),
    60: datetime.date(2000, 4, 15),
    61: datetime.date(2000, 4, 20),
    62: datetime.date(2000, 4, 25),
    63: datetime.date(2000, 4, 30),
    64: datetime.date(2000, 5, 5),
    65: datetime.date(2000, 5, 10),
    66: datetime.date(2000, 5, 15),
    67: datetime.date(2000, 5, 20),
    68: datetime.date(2000, 5, 25),
    69: datetime.date(2000, 5, 30),
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
    fn = "blocks/%s%s.txt" % (code, cfactor)
    if not os.path.isfile(fn):
        return ""
    data = open(fn, "r").read()
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


def do_rotation(scenario, zone, code, cfactor):
    """Create the rotation file

    Args:
      scenario (int): The DEP scenario
      zone (str): The DEP cropping zone
      code (char): the management code string used to identify crops
      cfactor (int): the c-factor at play here

    Returns:
      None
    """
    # We create a tree of codes to keep directory sizes in check
    dirname = ("../../prj2wepp/wepp/data/managements/%s/%s/%s/%s") % (
        "IDEP2" if scenario == 0 else "SCEN%s" % (scenario,),
        zone,
        code[:2],
        code[2:4],
    )
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
    fn = "%s/%s-%s.rot" % (dirname, code, cfactor)
    # Don't re-create this file if it already exists and we don't have
    # OVERWRITE set
    if not OVERWRITE and os.path.isfile(fn):
        return False
    # Dictionary of values used to fill out the file template below
    data = {}
    data["date"] = datetime.datetime.now()
    data["code"] = code
    data["name"] = "%s-%s" % (code, cfactor)
    data["initcond"] = INITIAL_COND.get(code[0], INITIAL_COND_DEFAULT)
    prevcode = "C" if code[0] not in INITIAL_COND else code[0]
    # 2007
    data["year1"] = read_file(scenario, zone, prevcode, code[0], cfactor, 1)
    data["year2"] = read_file(scenario, zone, code[0], code[1], cfactor, 2)
    data["year3"] = read_file(scenario, zone, code[1], code[2], cfactor, 3)
    data["year4"] = read_file(scenario, zone, code[2], code[3], cfactor, 4)
    data["year5"] = read_file(scenario, zone, code[3], code[4], cfactor, 5)
    data["year6"] = read_file(scenario, zone, code[4], code[5], cfactor, 6)
    data["year7"] = read_file(scenario, zone, code[5], code[6], cfactor, 7)
    data["year8"] = read_file(scenario, zone, code[6], code[7], cfactor, 8)
    data["year9"] = read_file(scenario, zone, code[7], code[8], cfactor, 9)
    data["year10"] = read_file(scenario, zone, code[8], code[9], cfactor, 10)
    data["year11"] = read_file(scenario, zone, code[9], code[10], cfactor, 11)
    data["year12"] = read_file(scenario, zone, code[10], code[11], cfactor, 12)
    data["year13"] = read_file(scenario, zone, code[11], code[12], cfactor, 13)

    with open(fn, "w") as fh:
        fh.write(
            """#
# WEPP rotation saved on: %(date)s
#
# Created with scripts/mangen/build_management.py
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
}
"""
            % data
        )
    return True


def get_zone(latitude):
    """Determine the DEP zone based on the provided latitude"""
    if latitude is None:
        return None
    zone = "KS_NORTH"
    if latitude >= 42.5:
        zone = "IA_NORTH"
    elif latitude >= 41.5:
        zone = "IA_CENTRAL"
    elif latitude >= 40.5:
        zone = "IA_SOUTH"
    return zone


def main(argv):
    """Our main code entry point"""
    scenario = int(argv[1])
    sdf = load_scenarios()
    flowpath_scenario = int(sdf.at[scenario, "flowpath_scenario"])
    cursor = PGCONN.cursor()
    cursor.execute(
        """
        WITH np as (
            SELECT ST_ymax(ST_Transform(geom, 4326)) as lat, fid
            from flowpaths WHERE scenario = %s)

        SELECT np.lat, landuse
        from flowpath_points p, np WHERE p.flowpath = np.fid
        and p.scenario = %s
    """,
        (flowpath_scenario, flowpath_scenario),
    )
    added = 0
    for row in tqdm(cursor, total=cursor.rowcount):
        zone = get_zone(row[0])
        if zone is None:
            continue
        for i in (1, 25):  # loop over c-factors
            if do_rotation(scenario, zone, row[1], i):
                added += 1
    LOG.info("Added %s new rotation files", added)


if __name__ == "__main__":
    main(sys.argv)
