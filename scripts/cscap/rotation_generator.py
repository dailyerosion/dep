"""Generate the fancy pants rotation (.rot) files used by WEPP

These are for idealized scenarios and need to generate each phase of the two
year scenario."""
import sys

# These are the building blocks to the rotation puzzle
TILLAGE = {
    "plow": "1 Tillage     OpCropDef.MOPL  {0.152400, 1}",
    "chisel": "1 Tillage      OpCropDef.CHISSTSP      {0.203200, 1}",
    "fieldcult": "1 Tillage      OpCropDef.FIEL0001      {0.101600, 2}",
    "plant": "1 Tillage     OpCropDef.PLDDO {0.050800, 2}",
    "ntplant": "1 Tillage   OpCropDef.PLNTFC        {0.050800, 2}",
    "drill": "1 Tillage    OpCropDef.CRNTFRRI      {0.050000, 2}",
    "disk": "1 Tillage      OpCropDef.TAND0002      {0.101600, 2}",
    "anhydros": "1 Tillage      OpCropDef.ANHYDROS      {0.101600, 2}",
}

PLANT = {
    "corn": "1 Plant-Annual        CropDef.Corn     {0.762000}",
    "cover": "1 Plant-Perennial    CropDef.Alf_5069         {0.190500,0}",
    "soy": "1 Plant-Annual        CropDef.soybean2         {0.762000}",
}

HARVEST = {
    "corn": "1 Harvest-Annual     CropDef.Corn    {}",
    "cover": "1 Kill-Perennial       CropDef.Alf_5069        {}",
    "soy": "1 Harvest-Annual     CropDef.soybean2        {}",
}
BLOCKS = {"TILLAGE": TILLAGE, "PLANT": PLANT, "HARVEST": HARVEST}

# So lets build scenarios
SCENARIOS = {
    # continuous corn, no-cover, no-till
    18: [
        [
            (5, 10, "TILLAGE", "ntplant"),
            (5, 10, "PLANT", "corn"),
            (10, 15, "HARVEST", "corn"),
            (11, 1, "TILLAGE", "anhydros"),
        ],
        [
            (5, 10, "TILLAGE", "ntplant"),
            (5, 10, "PLANT", "corn"),
            (10, 15, "HARVEST", "corn"),
            (11, 1, "TILLAGE", "anhydros"),
        ],
    ],
    # Corn/Soybean, cover, conventional
    19: [
        [
            (5, 10, "TILLAGE", "plant"),
            (5, 10, "PLANT", "corn"),
            (10, 15, "HARVEST", "corn"),
            (10, 16, "TILLAGE", "drill"),
            (10, 16, "PLANT", "cover"),
            (5, 4, "HARVEST", "cover"),
            (5, 4, "TILLAGE", "chisel"),
            (5, 6, "TILLAGE", "disk"),
            (5, 8, "TILLAGE", "fieldcult"),
        ],
        [
            (5, 10, "TILLAGE", "plant"),
            (5, 10, "PLANT", "soy"),
            (10, 15, "HARVEST", "soy"),
            (10, 16, "TILLAGE", "drill"),
            (10, 16, "PLANT", "cover"),
            (5, 4, "HARVEST", "cover"),
            (5, 4, "TILLAGE", "anhydros"),
            (5, 4, "TILLAGE", "chisel"),
            (5, 8, "TILLAGE", "fieldcult"),
        ],
    ],
    # Corn/Soybean, no-cover, conventional
    20: [
        [
            (5, 10, "TILLAGE", "plant"),
            (5, 10, "PLANT", "corn"),
            (10, 15, "HARVEST", "corn"),
            (5, 4, "TILLAGE", "chisel"),
            (5, 6, "TILLAGE", "disk"),
            (5, 8, "TILLAGE", "fieldcult"),
        ],
        [
            (5, 10, "TILLAGE", "plant"),
            (5, 10, "PLANT", "soy"),
            (10, 15, "HARVEST", "soy"),
            (5, 4, "TILLAGE", "anhydros"),
            (5, 4, "TILLAGE", "chisel"),
            (5, 8, "TILLAGE", "fieldcult"),
        ],
    ],
    # Corn/Soybean, no-cover, plowing
    21: [
        [
            (5, 10, "TILLAGE", "plant"),
            (5, 10, "PLANT", "corn"),
            (10, 15, "HARVEST", "corn"),
            (10, 20, "TILLAGE", "plow"),
            (5, 6, "TILLAGE", "disk"),
            (5, 8, "TILLAGE", "fieldcult"),
        ],
        [
            (5, 10, "TILLAGE", "plant"),
            (5, 10, "PLANT", "soy"),
            (10, 15, "HARVEST", "soy"),
            (10, 20, "TILLAGE", "plow"),
            (5, 4, "TILLAGE", "anhydros"),
            (5, 4, "TILLAGE", "disk"),
            (5, 8, "TILLAGE", "fieldcult"),
        ],
    ],
    # Corn/Soybean, no-cover, no-till
    22: [
        [
            (5, 10, "TILLAGE", "ntplant"),
            (5, 10, "PLANT", "corn"),
            (10, 15, "HARVEST", "corn"),
        ],
        [
            (5, 10, "TILLAGE", "ntplant"),
            (5, 10, "PLANT", "soy"),
            (10, 15, "HARVEST", "soy"),
            (11, 1, "TILLAGE", "anhydros"),
        ],
    ],
    # Corn/Soybean, cover, no-till
    23: [
        [
            (5, 10, "TILLAGE", "ntplant"),
            (5, 10, "PLANT", "corn"),
            (10, 15, "HARVEST", "corn"),
            (10, 16, "TILLAGE", "drill"),
            (10, 16, "PLANT", "cover"),
            (5, 4, "HARVEST", "cover"),
        ],
        [
            (5, 10, "TILLAGE", "ntplant"),
            (5, 10, "PLANT", "soy"),
            (10, 15, "HARVEST", "soy"),
            (10, 16, "TILLAGE", "drill"),
            (10, 16, "PLANT", "cover"),
            (5, 4, "HARVEST", "cover"),
        ],
    ],
    # continuous corn, cover, no-till
    24: [
        [
            (5, 10, "TILLAGE", "ntplant"),
            (5, 10, "PLANT", "corn"),
            (10, 15, "HARVEST", "corn"),
            (10, 16, "TILLAGE", "drill"),
            (10, 16, "PLANT", "cover"),
            (5, 4, "HARVEST", "cover"),
            (5, 6, "TILLAGE", "anhydros"),
        ],
        [
            (5, 10, "TILLAGE", "ntplant"),
            (5, 10, "PLANT", "corn"),
            (10, 15, "HARVEST", "corn"),
            (10, 16, "TILLAGE", "drill"),
            (10, 16, "PLANT", "cover"),
            (5, 4, "HARVEST", "cover"),
            (5, 6, "TILLAGE", "anhydros"),
        ],
    ],
}
# Filenames
FILENAMES = {
    18: "CC_NC_NT.rot",
    19: "CS_CC_CT.rot",
    20: "CS_NC_CT.rot",
    21: "CS_NC_PL.rot",
    22: "CS_NC_NT.rot",
    23: "CS_CC_NT.rot",
    24: "CC_CC_NT.rot",
}


def do(scenario, filename, phase):
    fullpath = ("../../prj2wepp/wepp/data/managements/IDEP2/CSCAP/%s_%s") % (
        phase,
        filename,
    )
    o = open(fullpath, "w")
    o.write(
        """#
# WEPP rotation saved on: Wed Feb 22 03:31:21 PM 2017
#
# Created with WEPPWIN verion: Sep 17 2012
#
Version = 98.7
Name = corn,soybean - mulch till cover crop
Description {
}
Color = 0 255 0
LandUse = 1
InitialConditions = IniCropDef.Default {0.000000, 0}

Operations {
"""
    )
    rot = SCENARIOS[scenario]
    if phase == 2:
        # Flip the order
        rot = SCENARIOS[scenario][::-1]
    # We need 2007 through 2017, so eleven years
    rots = rot + rot + rot + rot + rot + rot
    year = 2007
    limit = 2018
    for rot in rots[:11]:
        lastmonth = 0
        for (month, day, operation, label) in rot:
            if month < lastmonth:
                year += 1
            lastmonth = month
            if year >= limit:
                break
            o.write(
                "%s %s %s %s\n"
                % (month, day, year - 2006, BLOCKS[operation][label])
            )
        if lastmonth > 8:
            year += 1

    o.write("""}""")
    o.close()


def main(argv):
    for scenario, filename in FILENAMES.iteritems():
        do(scenario, filename, 1)
        do(scenario, filename, 2)


if __name__ == "__main__":
    main(sys.argv)
