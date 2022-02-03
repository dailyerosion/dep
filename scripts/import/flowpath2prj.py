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

from tqdm import tqdm
from pandas import read_sql
from pyiem.util import get_dbconn, get_dbconnstr, logger
from pyiem.dep import load_scenarios

LOG = logger()
MISSED_SOILS = {}
MAX_SLOPE_RATIO = 0.9
MIN_SLOPE = 0.003

SURGO2FILE = {}

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


def load_surgo2file(cursor):
    """Populate"""
    cursor.execute("SELECT surgo, soilfile from xref_surgo")
    for row in cursor:
        SURGO2FILE[row[0]] = row[1]


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
    data["name"] = f"{landuse}-{management}"
    data["initcond"] = INITIAL_COND.get(landuse[0], INITIAL_COND_DEFAULT)
    prevcode = "C" if landuse[0] not in INITIAL_COND else landuse[0]
    f = partial(read_file, scenario, zone)
    # 2007
    data["year1"] = f(prevcode, landuse[0], int(management[0]), 1)
    for i in range(1, 16):
        data[f"year{i + 1}"] = f(
            landuse[i - 1], landuse[i], int(management[i]), i + 1
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


def non_zero(dy, dx):
    """Make sure slope is slightly non-zero"""
    # NB we used to have a check here that dx was non-zero, but this should
    # never happen now.
    # dailyerosion/dep#79 denotes some limits on WEPP precision
    return max(MIN_SLOPE, dy / dx)


def simplify(df):
    """WEPP can only handle 20 slope points it seems, so we must simplify"""
    df["useme"] = False
    # Any hack is a good hack here, take the first and last point
    df.iat[0, df.columns.get_loc("useme")] = True
    df.iat[-1, df.columns.get_loc("useme")] = True
    # Take the top 18 values by slope
    df.loc[df.sort_values("slope", ascending=False).index[:18]]["useme"] = True
    df = df[df["useme"]].copy()
    # We need to recompute slope values to keep elevation values correct,
    # the value is ahead down the hill
    df["dx"] = df["length"].shift(-1) - df["length"]
    df["dy"] = df["elevation"] - df["elevation"].shift(-1)
    df["slope"] = df["dy"] / df["dx"]
    # Repeat the last value as good enough
    slpidx = df.columns.get_loc("slope")
    df.iat[-1, slpidx] = df.iat[-2, slpidx]
    return df


def compute_slope(cursor, fid):
    """Compute the simple slope for the fid"""
    cursor.execute(
        "SELECT max(elevation), min(elevation), max(length) "
        "from flowpath_points where flowpath = %s and length < 9999",
        (fid,),
    )
    row2 = cursor.fetchone()
    return (row2[0] - row2[1]) / row2[2]


def delete_flowpath(cursor, fid):
    """remove this flowpath as its invalid"""
    cursor.execute("DELETE from flowpath_points where flowpath = %s", (fid,))
    cursor.execute("DELETE from flowpaths where fid = %s", (fid,))
    if cursor.rowcount != 1:
        print(f"Whoa, delete_flowpath failed for {fid}")


def filter_soils_slopes(df, scenario):
    """Remove things we can't deal with"""
    df["useme"] = False
    if df["slope"].min() < 0:
        return None
    for idx, row in df.iterrows():
        if row["soilfile"] == "DEP_9999.SOL":
            continue
        if not os.path.isfile(f"/i/{scenario}/sol_input/{row['soilfile']}"):
            if row["soilfile"] not in MISSED_SOILS:
                LOG.info("Missing soilfile: %s", row["soilfile"])
                MISSED_SOILS[row["soilfile"]] = 0
            MISSED_SOILS[row["soilfile"]] += 1
            continue
        if row["slope"] < MIN_SLOPE:
            df.at[idx, "slope"] = MIN_SLOPE
        df.at[idx, "useme"] = True

    return df[df["useme"]].copy()


def rewrite_flowpath(cursor, scenario, flowpath_id, df):
    """Rewrite the flowpath with the new slope values"""
    cursor.execute(
        "DELETE from flowpath_points where flowpath = %s",
        (flowpath_id,),
    )
    for _idx, row in df.iterrows():
        cursor.execute(
            "INSERT INTO flowpath_points (flowpath, segid, elevation, length, "
            "surgo, slope, geom, scenario, gridorder, landuse, management, "
            "fbndid, genlu) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                flowpath_id,
                row["segid"],
                row["elevation"],
                row["length"],
                row["surgo"],
                row["slope"],
                f"SRID=5070;POINT({row['xx']} {row['yy']})",
                scenario,
                row["gridorder"],
                row["landuse"],
                row["management"],
                row["fbndid"],
                row["genlu"],
            ),
        )


def do_flowpath(cursor, scenario, zone, metadata):
    """Process a given flowpathid"""
    # slope = compute_slope(fid)
    # I need bad soilfiles so that the length can be computed
    df = read_sql(
        """
        SELECT segid, elevation, length, f.surgo,
        slope, management, 'DEP_'||surgo||'.SOL' as soilfile, landuse,
        ST_x(geom) as xx, ST_y(geom) as yy, fbndid, genlu, gridorder,
        round(ST_X(ST_Transform(geom,4326))::numeric,2) as x,
        round(ST_Y(ST_Transform(geom,4326))::numeric,2) as y from
        flowpath_points f
        WHERE flowpath = %s and length < 9999
        ORDER by segid ASC
    """,
        get_dbconnstr("idep"),
        params=(metadata["fid"],),
    )
    origsize = len(df.index)
    df = filter_soils_slopes(df, scenario)
    if df is None or len(df.index) < 2:
        LOG.info(
            "deleting %s,%s as failed filter_soil_slopes",
            metadata["huc_12"],
            metadata["fpath"],
        )
        delete_flowpath(cursor, metadata["fid"])
        return None
    if len(df.index) > 19:
        df = simplify(df)
    # If the size changed, we need to rewrite this flowpath to database
    if origsize != len(df.index):
        rewrite_flowpath(cursor, scenario, metadata["fid"], df)

    maxslope = df["slope"].max()
    if maxslope > MAX_SLOPE_RATIO:
        s = compute_slope(cursor, metadata["fid"])
        LOG.info(
            "Error max-slope>%s %s[%3i] max:%4.1f len:%5.1f bulk:%5.1f",
            MAX_SLOPE_RATIO,
            metadata["huc_12"],
            metadata["fpath"],
            maxslope,
            df.iloc[-1]["length"],
            s,
        )
        delete_flowpath(cursor, metadata["fid"])
        return None

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
        df.iloc[0]["x"], df.iloc[0]["y"], df.iloc[-1]["x"], df.iloc[-1]["y"]
    )
    res["prj_fn"] = (
        f"/i/{scenario}/prj/{res['huc8']}/{res['huc12'][-4:]}/"
        f"{res['huc12']}_{metadata['fpath']}.prj"
    )
    res["length"] = df.iloc[-1]["length"]
    res["slope_points"] = len(df.index)

    # Iterate over the rows and figure out the slopes and distance fracs
    slpdata = ""
    if df.iloc[0]["length"] != 0:
        LOG.info(
            "WARNING: HUC12:%s FPATH:%s had missing soil at top of slope",
            metadata["huc_12"],
            metadata["fpath"],
        )
        slpdata = " 0.000,0.00001"
        res["slope_points"] = len(df.index) + 1

    soil = df.iloc[0]["surgo"]
    soilstart = 0
    soils = []
    soillengths = []

    for idx, row in df.iterrows():
        if soil != row["surgo"] or idx == df.index[-1]:
            soils.append(soil)
            soillengths.append(row["length"] - soilstart)
            soil = row["surgo"]
            soilstart = row["length"]
        # NEED lots of precision to get grid rectifying right
        # see dailyerosion/dep#79
        slpdata += f" {row['length'] / res['length']},{row['slope']:5f}"

    res["soilbreaks"] = len(soillengths) - 1
    res["soils"] = ""
    res["slpdata"] = slpdata

    for d, s in zip(soillengths, soils):
        res[
            "soils"
        ] += f"""    {s} {{
        Distance = {d:.3f}
        File = "/i/{scenario}/sol_input/DEP_{s}.SOL"
    }}\n"""

    prev_landuse = df.iloc[0]["landuse"]
    manstart = 0
    prev_man = df.iloc[0]["management"]
    mans = []
    manlengths = []

    # Figure out our landuse situation
    for idx, row in df.iterrows():
        if (
            prev_landuse == row["landuse"]
            and prev_man == row["management"]
            and idx != df.index[-1]
        ):
            continue
        # Management has changed, write out the old row
        mans.append(
            rotation_magic(scenario, zone, len(mans), df.loc[idx], metadata)
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
        return None
    res["manbreaks"] = len(manlengths) - 1
    res["managements"] = ""

    for d, s in zip(manlengths, mans):
        res[
            "managements"
        ] += f"""    {s} {{
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


def get_flowpath_scenario(scenario):
    """internal accounting."""
    sdf = load_scenarios()
    return int(sdf.at[scenario, "flowpath_scenario"])


def main(argv):
    """Go main go"""
    scenario = int(argv[1])
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()
    load_surgo2file(cursor)
    df = read_sql(
        "SELECT ST_ymax(ST_Transform(geom, 4326)) as lat, fpath, fid, huc_12, "
        "climate_file from flowpaths WHERE scenario = %s and fpath != 0 "
        "ORDER by huc_12 ASC",
        get_dbconnstr("idep"),
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
        data = do_flowpath(cursor, scenario, zone, row)
        if data is not None:
            write_prj(data)
    cursor.close()
    pgconn.commit()
    for fn, sn in MISSED_SOILS.items():
        print(f"{sn:6s} {fn}")


if __name__ == "__main__":
    main(sys.argv)
