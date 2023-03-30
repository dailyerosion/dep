"""Generate the WEPP prj files based on what our database has for us.

Here's a listing of project landuse codes used

                     No-till (1)   (2-5)
  B - Soy               B1          B25    IniCropDef.Default
  F - forest            F1          F25    IniCropDef.Tre_2239
  G - Sorghum
  P - Pasture           P1          P25    IniCropDef.gra_3425
  C - Corn              C1          C25    IniCropDef.Default
  R - Other crops (Barley?)  R1          R25    IniCropDef.Aft_12889
  T - Water (could have flooded out for one year, wetlands)
  U - Developed
  X - Unclassified
  I - Idle
  L - Double Crop  (started previous year) (winter wheat + soybea)
  W - Wheat
  S - Durum/Spring Wheat
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
import sys
import os
import datetime
from functools import partial
from math import atan2, degrees, pi

import numpy as np
from tqdm import tqdm
import pandas as pd
from pyiem.util import get_dbconn, get_sqlalchemy_conn, logger
from pydep.util import load_scenarios

LOG = logger()
MISSED_SOILS = {}
YEARS = 2023 - 2006

# Note that the default used below is
INITIAL_COND_DEFAULT = "IniCropDef.Default"
INITIAL_COND = {
    "F": "IniCropDef.Tre_2239",  # TODO for new forest stuff
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
# Management code maps back to a forest crop
FOREST = {
    "J": "IniCropDef.DEP_forest_95",
    "I": "IniCropDef.DEP_forest_85",
    "H": "IniCropDef.DEP_forest_75",
    "G": "IniCropDef.DEP_forest_65",
    "F": "IniCropDef.DEP_forest_55",
    "E": "IniCropDef.DEP_forest_45",
    "D": "IniCropDef.DEP_forest_35",
    "C": "IniCropDef.DEP_forest_25",
    "B": "IniCropDef.DEP_forest_15",
    "A": "IniCropDef.DEP_forest_5",
    "0": "IniCropDef.DEP_forest_45",  # TODO
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
WHEAT = {
    "KS_SOUTH": "CropDef.spwheat1",
    "KS_CENTRAL": "CropDef.spwheat1",
    "KS_NORTH": "CropDef.spwheat1",
    "IA_SOUTH": "CropDef.spwheat1",
    "IA_CENTRAL": "CropDef.spwheat1",
    "IA_NORTH": "CropDef.spwheat1",
}


def read_file(scenario, zone, prevcode, code, nextcode, cfactor, year):
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
    blockfn = f"blocks/{code}{cfactor}.txt"
    if not os.path.isfile(blockfn):
        return ""
    with open(blockfn, "r", encoding="utf8") as fh:
        data = fh.read()
    # Special consideration for planting alfalfa
    if code == "P" and prevcode != "P":
        # Best we can do now is plant it on Apr 15, sigh
        data = (
            f"4  15 {year} 1 Plant-Perennial CropDef.ALFALFA  {{0.000000}}\n"
            f"{data}"
        )
    # One off
    if code == "B" and prevcode == "C" and cfactor == 2:
        # Remove fall chisel
        data = data[: data.find("11  1  %(yr)s")]
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
    elif code in ["B", "L"]:  # TODO support double crop
        date = SOYBEAN_PLANT.get(scenario, SOYBEAN_PLANT[zone])
        pdate = date.strftime("%m    %d")
        pdatem5 = (date - datetime.timedelta(days=5)).strftime("%m    %d")
        pdatem10 = (date - datetime.timedelta(days=10)).strftime("%m    %d")
        plant = SOYBEAN[zone]
    elif code == "W":
        date = SOYBEAN_PLANT.get(scenario, SOYBEAN_PLANT[zone])  # TODO
        plant = WHEAT_PLANT[zone]
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
    data["name"] = f"{landuse}-{management}"
    # Special hack for forest
    if landuse[0] == "F" and landuse == len(landuse) * landuse[0]:
        data["initcond"] = FOREST[management[0]]
        for i in range(1, 18):
            # Reset roughness each year
            data[
                f"year{i}"
            ] = f"1 2 {i} 1 Tillage OpCropDef.Old_6807 {{0.001, 2}}"
    else:
        data["initcond"] = INITIAL_COND.get(landuse[0], INITIAL_COND_DEFAULT)
        prevcode = "C" if landuse[0] not in INITIAL_COND else landuse[0]
        f = partial(read_file, scenario, zone)
        # 2007
        data["year1"] = f(
            prevcode, landuse[0], landuse[1], int(management[0]), 1
        )
        for i in range(1, 17):
            nextcode = "" if i == 16 else landuse[i + 1]
            data[f"year{i + 1}"] = f(
                landuse[i - 1], landuse[i], nextcode, int(management[i]), i + 1
            )

    with open(rotfn, "w", encoding="utf8") as fh:
        fh.write(
            f"""#
# WEPP rotation saved on: {datetime.datetime.now()}
#
# Created with scripts/import/flowpath2prj.py
#
Version = 98.7
Name = {data['name']}
Description {{
}}
Color = 0 255 0
LandUse = 1
InitialConditions = {data['initcond']}

Operations {{
{data['year1']}
{data['year2']}
{data['year3']}
{data['year4']}
{data['year5']}
{data['year6']}
{data['year7']}
{data['year8']}
{data['year9']}
{data['year10']}
{data['year11']}
{data['year12']}
{data['year13']}
{data['year14']}
{data['year15']}
{data['year16']}
{data['year17']}
}}
"""
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
    rotfn = (
        f"/i/{scenario}/rot/{metadata['huc_12'][:8]}/{metadata['huc_12'][8:]}"
        f"/{metadata['huc_12']}_{metadata['fpath']}_{seqnum}.rot"
    )
    # Oh my cats, we are about to create the .rot file here
    do_rotation(scenario, zone, rotfn, row["landuse"], row["management"])
    return rotfn


def compute_aspect(x0, y0, x1, y1):
    """Compute the aspect angle between two points"""
    dx = x1 - x0
    dy = y1 - y0
    rads = atan2(-dy, dx)
    rads %= 2 * pi
    return degrees(rads)


def load_flowpath_from_db(pgconn, fid):
    """Fetch me the flowpath."""
    return pd.read_sql(
        """
        WITH pts as (
            select array_agg(slope ORDER by segid ASC) as slopes,
            array_agg(length ORDER by segid ASC) as lengths
            from flowpath_points where flowpath = %s),
        ofes as (
            select o.ofe, o.management, o.landuse, o.real_length,
            'DEP_'||mukey||'.SOL' as soilfile, st_pointn(o.geom, 1) as spt,
            st_pointn(o.geom, -1) as ept from
            flowpath_ofes o JOIN gssurgo g on (o.gssurgo_id = g.id)
            WHERE o.flowpath = %s)
        SELECT lengths, slopes, o.*, st_x(spt) as start_x,
        st_y(spt) as start_y, st_x(ept) as end_x, st_y(ept) as end_y from
        ofes o, pts p ORDER by ofe ASC
    """,
        pgconn,
        params=(fid, fid),
        index_col="ofe",
    )


def do_flowpath(pgconn, scenario, zone, metadata):
    """Process a given flowpathid"""
    # slope = compute_slope(fid)
    # I need bad soilfiles so that the length can be computed
    df = load_flowpath_from_db(pgconn, metadata["fid"])

    res = {}
    res["clifile"] = metadata["climate_file"]
    res["huc8"] = metadata["huc_12"][:8]
    res["huc12"] = metadata["huc_12"]
    res["envfn"] = (
        f"/i/{scenario}/env/{res['huc8']}/"
        f"{res['huc12']}_{metadata['fpath']}.env"
    )
    res["date"] = datetime.datetime.now()
    res["aspect"] = compute_aspect(
        df.iloc[0]["start_x"],
        df.iloc[0]["start_y"],
        df.iloc[-1]["end_x"],
        df.iloc[-1]["end_y"],
    )
    res["prj_fn"] = (
        f"/i/{scenario}/prj/{res['huc8']}/{res['huc12'][-4:]}/"
        f"{res['huc12']}_{metadata['fpath']}.prj"
    )
    res["length"] = df["real_length"].sum()

    # Slope data
    # Here be dragons: dailyerosion/dep#79 dailyerosion/dep#158
    # Current approach is that since we are defining OFEs, we subvert whatever
    # prj2wepp is doing with the slope files and prescribe them below
    slpdata = ""
    res["slp_dummy"] = f"2 {res['length']:.4f}\n0.00, 0.01 1.00, 0.01\n"
    startlen = 0
    for _ofe, row in df.iterrows():
        endlen = startlen + row["real_length"]
        lens = []
        slopes = []
        for x, s in zip(row["lengths"], row["slopes"]):
            if (
                abs(x - startlen) < 0.01
                or abs(x - endlen) < 0.01
                or startlen < x < endlen
            ):
                lens.append(x)
                slopes.append(s)
        if not lens:
            print(df)
            print(startlen, endlen)
            sys.exit()
        lens = np.array(lens) - lens[0]
        lens = lens / lens[-1]
        startlen = endlen
        tokens = [f"{r:.6f},{s:.6f}" for r, s in zip(lens, slopes)]
        slpdata += (
            f"{len(lens)} {row['real_length']:.4f}\n" f"{' '.join(tokens)}\n"
        )
    slpfn = (
        f"/i/{scenario}/slp/{res['huc8']}/{res['huc12'][-4:]}/"
        f"{res['huc12']}_{metadata['fpath']}.slp"
    )
    # We do this ourselves do to prj2wepp limitations
    with open(slpfn, "w", encoding="ascii") as fh:
        fh.write(
            "97.5\n"
            "#\n"
            f"# from flowpath2prj.py {res['date']}\n"
            "#\n"
            "#\n"
            f"{len(df.index)}\n"
            f"{res['aspect']:.4f} 1.000\n"
            f"{slpdata}\n"
        )

    soilfiles = df["soilfile"].values
    soillengths = df["real_length"].values

    res["soilbreaks"] = len(soillengths) - 1
    res["soils"] = ""

    for s, (d, soilfn) in enumerate(zip(soillengths, soilfiles), start=1):
        res[
            "soils"
        ] += f"""    soil{s} {{
        Distance = {d:.3f}
        File = "/i/{scenario}/sol_input/{soilfn}"
    }}\n"""

    mans = []
    manlengths = []

    # Figure out our landuse situation
    for idx, row in df.iterrows():
        # Management has changed, write out the old row
        mans.append(rotation_magic(scenario, zone, idx, row, metadata))
        manlengths.append(row["real_length"])

    res["manbreaks"] = len(manlengths) - 1
    res["managements"] = ""

    for i, (d, s) in enumerate(zip(manlengths, mans), start=1):
        res[
            "managements"
        ] += f"""    man{i} {{
        Distance = {d:.3f}
        File = "{s}"
    }}\n"""

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
    with open(data["prj_fn"], "w", encoding="utf8") as fh:
        # pylint: disable=consider-using-f-string
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
%(slp_dummy)s
    }
}
Climate {
   # We need a file, any file for prj2wepp, unused later
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
   SimulationYears = %(years)s
   SmallEventByPass = 1
}
"""
            % data
        )


def get_flowpath_scenario(scenario):
    """internal accounting."""
    sdf = load_scenarios()
    return int(sdf.at[scenario, "flowpath_scenario"])


def workflow(pgconn, scenario):
    """Go main go"""
    conn = get_dbconn("idep")
    cursor = conn.cursor()
    df = pd.read_sql(
        "SELECT ST_ymax(ST_Transform(geom, 4326)) as lat, fpath, fid, huc_12, "
        "climate_file from flowpaths WHERE scenario = %s "
        "ORDER by huc_12 ASC",
        pgconn,
        params=(get_flowpath_scenario(scenario),),
    )
    if os.path.isfile("myhucs.txt"):
        myhucs = []
        with open("myhucs.txt", encoding="utf8") as fh:
            myhucs = fh.read().split("\n")
        LOG.info("Only running for HUC_12s in myhucs.txt")
        df = df[df["huc_12"].isin(myhucs)]
    progress = tqdm(df.iterrows(), total=len(df.index))
    for _idx, row in progress:
        progress.set_description(f"{row['huc_12']} {row['fpath']:04.0f}")
        zone = "KS_NORTH"
        if row["lat"] >= 42.5:
            zone = "IA_NORTH"
        elif row["lat"] >= 41.5:
            zone = "IA_CENTRAL"
        elif row["lat"] >= 40.5:
            zone = "IA_SOUTH"
        data = do_flowpath(pgconn, scenario, zone, row)
        if data is not None:
            data["years"] = YEARS
            write_prj(data)
    cursor.close()
    conn.commit()
    for fn, sn in MISSED_SOILS.items():
        print(f"{sn:6s} {fn}")


def main(argv):
    """Go main go"""
    scenario = int(argv[1])
    with get_sqlalchemy_conn("idep") as pgconn:
        workflow(pgconn, scenario)


if __name__ == "__main__":
    main(sys.argv)
