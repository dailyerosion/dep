"""Generate the WEPP prj files based on what our database has for us.

Here's a listing of project landuse codes used

                     No-till (1)   (2-5)
  B - Soy               B1          B25    IniCropDef.Default
  F - forest            F1          F25    IniCropDef.Tre_2239
  G - Sorghum
  P - Pasture           P1          P25    IniCropDef.gra_3425
      (If all P, then pasture.  If P intermixed, then Alfalfa see GH270)
  C - Corn              C1          C25    IniCropDef.Default
  R - Other crops (Barley?)  R1          R25    IniCropDef.Aft_12889
  T - Water (could have flooded out for one year, wetlands)
  U - Developed
  X - Unclassified
  I - Idle
  L - Double Crop  (started previous year) (winter wheat + soybea)
  W - Wheat
  S - Durum/Spring Wheat
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
from datetime import datetime
from functools import partial
from math import atan2, degrees, pi

import click
import pandas as pd
from pyiem.database import get_dbconn, get_sqlalchemy_conn, sql_helper
from pyiem.util import logger
from tqdm import tqdm

from pydep.tillage import make_tillage
from pydep.util import load_scenarios

LOG = logger()
MISSED_SOILS = {}
YEARS = 2025 - 2006
# WEPP can not handle a zero slope, so we ensure that all slopes are >= 0.3%
MIN_SLOPE = 0.003

# Things to control for
KNOBS = {
    "dummy_slope": True,  # Write placeholder into prj file
}

# Note that the default used below is
INITIAL_COND_DEFAULT = "IniCropDef.Default"
INITIAL_COND = {
    "F": "IniCropDef.Tre_2239",  # TODO for new forest stuff
    "P": "IniCropDef.gra_3425",
    "R": "IniCropDef.Aft_12889",
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


def do_rotation(scenario, zone, rotfn, landuse: str, management):
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
    data = {"yearly": ""}
    data["name"] = f"{landuse}-{management}"
    # Special hack for forest
    if landuse[0] == "F" and len(set(landuse)) == 1:
        data["initcond"] = FOREST[management[0]]
        for i in range(1, YEARS):
            # Reset roughness each year
            data["yearly"] += (
                f"1 2 {i} 1 Tillage OpCropDef.Old_6807 {{0.001, 2}}\n"
            )
    # Special hack for pasture
    elif landuse[0] == "P" and len(set(landuse)) == 1:
        data["initcond"] = INITIAL_COND[landuse[0]]
        # For WEPP purposes and to our knowledge, we still need to initially
        # do a light tillage and plant this pasture to alfalfa
        data["yearly"] += (
            "4  14 1 1 Tillage OpCropDef.FCSTACDP      {0.101600, 2}\n"
            "4  15 1 1 Plant-Perennial CropDef.ALFALFA  {0.000000}\n"
        )
    else:
        data["initcond"] = INITIAL_COND.get(landuse[0], INITIAL_COND_DEFAULT)
        prevcode = "C" if landuse[0] not in INITIAL_COND else landuse[0]
        func = partial(make_tillage, scenario, zone)
        # 2007
        data["yearly"] += func(
            prevcode, landuse[0], landuse[1], management[0], 1
        )
        for i in range(1, YEARS):
            nextcode = "" if i == (YEARS - 1) else landuse[i + 1]
            data["yearly"] += func(
                landuse[i - 1], landuse[i], nextcode, management[i], i + 1
            )

    with open(rotfn, "w", encoding="utf8") as fh:
        fh.write(
            f"""#
# WEPP rotation saved on: {datetime.now()}
#
# Created with scripts/import/flowpath2prj.py
#
Version = 98.7
Name = {data["name"]}
Description {{
}}
Color = 0 255 0
LandUse = 1
InitialConditions = {data["initcond"]}

Operations {{
{data["yearly"]}
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
        sql_helper(
            """
        with data as (
            select ofe, (st_dumppoints(geom)).* as g,
            st_startpoint(geom) as stpt, st_endpoint(geom) as endpt,
            management, landuse,
            'DEP_'||mukey||'.SOL' as soilfile, real_length
            from flowpath_ofes o JOIN gssurgo g on (o.gssurgo_id = g.id)
            where flowpath = :fid)
        select ofe,
        greatest((lag(st_z(geom)) OVER (
             PARTITION by ofe ORDER by st_z(geom) DESC)
        - st_z(geom)) / st_distance(geom, lag(geom) OVER (
             PARTITION by ofe ORDER by st_z(geom) DESC)
        ), :min_slope) as slope, st_z(geom), st_distance(geom, stpt) as length,
        st_x(stpt) as start_x, st_x(endpt) as end_x,
        st_y(stpt) as start_y, st_y(endpt) as end_y,
        real_length, soilfile, management, landuse
        from data
        ORDER by ofe asc, length asc
    """
        ),
        pgconn,
        params={"fid": fid, "min_slope": MIN_SLOPE},
        index_col=None,
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
    res["date"] = datetime.now()
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
    # Add up the OFEs to get the total length
    res["length"] = df.groupby("ofe").first()["real_length"].sum()

    # Slope data
    # Here be dragons: dailyerosion/dep#79 dailyerosion/dep#158
    # Current approach is that since we are defining OFEs, we subvert whatever
    # prj2wepp is doing with the slope files and prescribe them below
    slpdata = ""
    for _ofe, gdf in df.groupby("ofe"):
        lens = gdf["length"].values / gdf["length"].values[-1]
        slopes = gdf["slope"].values
        # First value is null, so we just repeat it
        slopes[0] = slopes[1]
        tokens = [f"{r:.6f},{s:.6f}" for r, s in zip(lens, slopes)]
        slpdata += (
            f"{len(lens)} {gdf.iloc[0]['real_length']:.4f}\n"
            f"{' '.join(tokens)}\n"
        )
    if KNOBS["dummy_slope"]:
        res["slpdata"] = f"2 {res['length']:.4f}\n0.00, 0.01 1.00, 0.01\n"
    else:
        res["slpdata"] = slpdata
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
            f"{df['ofe'].max():.0f}\n"
            f"{res['aspect']:.4f} 1.000\n"
            f"{slpdata}\n"
        )

    res["soilbreaks"] = df["ofe"].max() - 1
    res["manbreaks"] = res["soilbreaks"]
    res["soils"] = ""
    res["managements"] = ""
    s = 1
    for _, row in df.groupby("ofe").first().iterrows():
        soilfile = row["soilfile"]
        soillength = row["real_length"]
        res["soils"] += (
            f"    soil{s} {{\n"
            f"Distance = {soillength:.3f}\n"
            f'File = "/i/{scenario}/sol_input/{soilfile}"\n'
            "}\n"
        )
        res["managements"] += (
            f"    man{s} {{\n"
            f"Distance = {soillength:.3f}\n"
            f'File = "{rotation_magic(scenario, zone, s, row, metadata)}"\n'
            "}\n"
        )
        s += 1

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
%(slpdata)s
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
        """
    SELECT ST_ymax(ST_Transform(f.geom, 4326)) as lat, fpath, fid, huc_12,
    filepath as climate_file from flowpaths f JOIN climate_files c on
    (f.climate_file_id = c.id) WHERE f.scenario = %s ORDER by huc_12 ASC""",
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


@click.command()
@click.option("-s", "--scenario", type=int, help="DEP Scenario", required=True)
@click.option(
    "--dummy-slope",
    "ds",
    default=True,
    type=bool,
    help="Write slope placeholder instead of real data",
)
def main(scenario: int, ds: bool):
    """Go main go"""
    KNOBS["dummy_slope"] = ds
    with get_sqlalchemy_conn("idep") as pgconn:
        workflow(pgconn, scenario)


def generate_combos():
    """Create rotation files for Eduardo inspection."""
    for cfactor in range(1, 7):
        for rot in "CC CB BC BB".split():
            res = make_tillage(0, "IA_NORTH", "M", rot[0], rot[1], cfactor, 1)
            with open(f"ex_{rot}_{cfactor}.rot", "w", encoding="utf8") as fh:
                fh.write(res)


if __name__ == "__main__":
    main()
    # generate_combos()
