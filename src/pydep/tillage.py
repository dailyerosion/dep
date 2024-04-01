"""DEP Tillage Logic and Life Choices."""

import os
from datetime import date, timedelta

WHEAT_PLANT = {
    "KS_SOUTH": date(2000, 5, 25),
    "KS_CENTRAL": date(2000, 5, 25),
    "KS_NORTH": date(2000, 5, 25),
    "IA_SOUTH": date(2000, 5, 12),
    "IA_CENTRAL": date(2000, 5, 17),
    "IA_NORTH": date(2000, 5, 23),
}

SOYBEAN_PLANT = {
    "KS_SOUTH": date(2000, 5, 25),
    "KS_CENTRAL": date(2000, 5, 25),
    "KS_NORTH": date(2000, 5, 25),
    "IA_SOUTH": date(2000, 5, 12),
    "IA_CENTRAL": date(2000, 5, 17),
    "IA_NORTH": date(2000, 5, 23),
}
CORN_PLANT = {
    "KS_SOUTH": date(2000, 4, 20),
    "KS_CENTRAL": date(2000, 4, 25),
    "KS_NORTH": date(2000, 4, 30),
    "IA_SOUTH": date(2000, 4, 30),
    "IA_CENTRAL": date(2000, 5, 5),
    "IA_NORTH": date(2000, 5, 10),
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


def make_tillage(scenario, zone, prevcode, code, nextcode, cfactor, year):
    """Read a block file and do replacements

    Args:
      scenario (int): The DEP scenario
      zone (str): The DEP cropping zone
      prevcode (str): the previous crop code
      code (str): the crop code
      nextcode (str): The next year's crop code.
      cfactor (int): the c-factor for tillage
      year (int): the year of this crop

    Returns:
      str with the raw data used for the .rot file
    """
    # FIXME
    blockfn = f"/opt/dep/scripts/import/blocks/{code}{cfactor}.txt"
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
    # Remove fall chisel after corn when going into soybeans for 2
    if cfactor == 2 and nextcode == "B":
        pos = data.find("11  1")
        if pos > 0:
            data = data[:pos]

    # The fall tillage operation is governed by the next year crop
    if cfactor == 5 and nextcode == "C":
        # Replace 11  1 operation with plow
        pos = data.find("11  1")
        if pos > 0:
            data = (
                f"{data[:pos]}"
                "11  1  %(yr)s  1 Tillage      OpCropDef.MOPL  {0.203200, 1}\n"
            )

    # Anhydrous ammonia application when we are going into Corn
    if nextcode == "C":
        # HACK: look for a present 1 Nov operation and insert this before it
        pos = data.find("11  1")
        extra = ""
        if pos > 0:
            extra = data[pos:].replace("11  1", "11  8")
            data = data[:pos]
        data = (
            f"{data}"
            f"11  1  {year}  1 Tillage   OpCropDef.ANHYDROS  {{0.101600, 2}}\n"
            f"{extra}"
        )

    pdate = ""
    pdatem5 = ""
    pdatem10 = ""
    pdatem15 = ""
    plant = ""
    # We currently only have zone specific files for Corn and Soybean
    if code == "C":
        date = CORN_PLANT.get(scenario, CORN_PLANT[zone])
        pdate = date.strftime("%m    %d")
        pdatem5 = (date - timedelta(days=5)).strftime("%m    %d")
        pdatem10 = (date - timedelta(days=10)).strftime("%m    %d")
        pdatem15 = (date - timedelta(days=15)).strftime("%m    %d")
        plant = CORN[zone]
    elif code in ["B", "L"]:  # TODO support double crop
        date = SOYBEAN_PLANT.get(scenario, SOYBEAN_PLANT[zone])
        pdate = date.strftime("%m    %d")
        pdatem5 = (date - timedelta(days=5)).strftime("%m    %d")
        pdatem10 = (date - timedelta(days=10)).strftime("%m    %d")
        pdatem15 = (date - timedelta(days=15)).strftime("%m    %d")
        plant = SOYBEAN[zone]
    elif code == "W":
        date = SOYBEAN_PLANT.get(scenario, SOYBEAN_PLANT[zone])  # TODO
        plant = WHEAT_PLANT[zone]
        pdate = date.strftime("%m    %d")
        pdatem5 = (date - timedelta(days=5)).strftime("%m    %d")
        pdatem10 = (date - timedelta(days=10)).strftime("%m    %d")
        pdatem15 = (date - timedelta(days=15)).strftime("%m    %d")
    return data % {
        "yr": year,
        "pdate": pdate,
        "pdatem5": pdatem5,
        "pdatem10": pdatem10,
        "pdatem15": pdatem15,
        "plant": plant,
    }
