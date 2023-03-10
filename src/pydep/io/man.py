"""Specific to reading management files."""
import datetime

import pandas as pd


def man2df(mandict: dict, year1: int = 1) -> pd.DataFrame:
    """Convert nasty dictionary returned from `read_man` into `pd.DataFrame`.

    The DataFrame is oriented with OFE, year.

    Args:
      mandict (dict): Dictionary populated from read_man.
      year1 (int,optional): What does WEPP year index 1 equate to in the
        real world!  The default of 1 just uses what WEPP does.

    Returns:
      pd.DataFrame
    """
    rows = []
    baseyear = year1  # roundabout
    for iofe in range(mandict["iofe"]):
        for iyear in range(mandict["inyr"]):
            year = iyear + baseyear
            scenyr = mandict["rotations"][iyear][iofe]["yearindex"]
            ncrop = mandict["scens"][scenyr - 1]["ntype"]
            tilseq = mandict["scens"][scenyr - 1]["tilseq"]
            plant_date = None
            for surfeff in mandict["surfeffects"][tilseq - 1]["tills"]:
                op = surfeff["op"]
                if (
                    mandict["operations"][op - 1]["scecomment"].find("Planter")
                    > -1
                ):
                    doy = surfeff["mdate"]
                    plant_date = datetime.date(
                        year, 1, 1
                    ) + datetime.timedelta(days=doy - 1)
            rows.append(
                {
                    "year": year,
                    "ofe": iofe + 1,
                    "plant_date": plant_date,
                    "crop_name": mandict["crops"][ncrop - 1]["crpnam"],
                }
            )
    return pd.DataFrame(rows)


def read_man(filename):
    """Implements WEPP's INFILE.for for reading management file

    Args:
      filename (str): Filename to read

    Returns:
      dict of management info
    """
    res = {}
    # Step one make a array of any data
    with open(filename, encoding="ascii") as fh:
        lines = [a[: a.find("#")].strip() for a in fh]
    res["manver"] = lines[0]
    res["iofe"] = int(lines[6])
    res["inyr"] = int(lines[7])
    res["ncrop"] = int(lines[13])
    res["crops"] = [None] * res["ncrop"]
    linenum = 16
    for ncrop in range(res["ncrop"]):
        res["crops"][ncrop] = {
            "crpnam": lines[linenum],
            "crpcomment": "\n".join(lines[linenum + 1 : linenum + 4]),
            "iplant": int(lines[linenum + 4]),
        }
        linenum += 5
        if res["crops"][ncrop]["iplant"] == 1:
            # TODO
            linenum += 7
    linenum += 4
    res["nop"] = int(lines[linenum])
    linenum += 3
    res["operations"] = [None] * res["nop"]
    for nop in range(res["nop"]):
        res["operations"][nop] = {
            "scenam": lines[linenum],
            "scecomment": "\n".join(lines[linenum + 1 : linenum + 4]),
            "iplant": int(lines[linenum + 4]),
        }
        linenum += 9
    linenum += 6
    res["nini"] = int(lines[linenum])
    res["ini"] = [None] * res["nini"]
    linenum += 3
    for ini in range(res["nini"]):
        res["ini"][ini] = {
            "scenam": lines[linenum],
            "scecomment": "\n".join(lines[linenum + 1 : linenum + 4]),
            "iplant": int(lines[linenum + 4]),
        }
        linenum += 14
    linenum += 6

    res["nsurf"] = int(lines[linenum])
    res["surfeffects"] = [None] * res["nsurf"]
    linenum += 6
    for surf in range(res["nsurf"]):
        res["surfeffects"][surf] = {
            "scenam": lines[linenum],
            "scecomment": "\n".join(lines[linenum + 1 : linenum + 4]),
            "iplant": int(lines[linenum + 4]),
            "ntill": int(lines[linenum + 5]),
        }
        res["surfeffects"][surf]["tills"] = [None] * res["surfeffects"][surf][
            "ntill"
        ]
        linenum += 6
        for till in range(res["surfeffects"][surf]["ntill"]):
            res["surfeffects"][surf]["tills"][till] = {
                "mdate": int(lines[linenum]),
                "op": int(lines[linenum + 1]),
                "depth": float(lines[linenum + 2]),
                "type": int(lines[linenum + 3]),
            }
            linenum += 4
        linenum += 4
    linenum += 2
    res["ncnt"] = int(lines[linenum])
    linenum += 7
    res["ndrain"] = int(lines[linenum])
    linenum += 7
    res["nmscen"] = int(lines[linenum])
    linenum += 4
    res["scens"] = [None] * res["nmscen"]
    for scen in range(res["nmscen"]):
        res["scens"][scen] = {
            "scenam": lines[linenum],
            "scecomment": "\n".join(lines[linenum + 1 : linenum + 4]),
            "iplant": int(lines[linenum + 4]),
            "ntype": int(lines[linenum + 5]),
            "tilseq": int(lines[linenum + 6]),
            "conseq": int(lines[linenum + 7]),
            "drseq": int(lines[linenum + 8]),
            "imngmt": int(lines[linenum + 9]),
        }
        if res["scens"][scen]["iplant"] == 1:
            if res["scens"][scen]["imngmt"] in [1, 3]:
                # Annual/Fallow Cropping system
                res["scens"][scen]["jdharv"] = int(lines[linenum + 10])
                res["scens"][scen]["jdplt"] = int(lines[linenum + 11])
                res["scens"][scen]["r1"] = float(lines[linenum + 12])
                res["scens"][scen]["resmgt"] = int(lines[linenum + 13])
                if res["scens"][scen]["resmgt"] == 1:
                    res["scens"][scen]["jdherb"] = int(lines[linenum + 14])
                    linenum += 15
                elif res["scens"][scen]["resmgt"] == 2:
                    res["scens"][scen]["jdburn"] = int(lines[linenum + 14])
                    res["scens"][scen]["fbrna1"] = float(
                        lines[linenum + 15].split()[0]
                    )
                    res["scens"][scen]["fbrno1"] = float(
                        lines[linenum + 15].split()[1]
                    )
                    linenum += 16
                elif res["scens"][scen]["resmgt"] == 3:
                    res["scens"][scen]["jdslge"] = int(lines[linenum + 14])
                    linenum += 15
                elif res["scens"][scen]["resmgt"] == 4:
                    res["scens"][scen]["jdcut"] = int(lines[linenum + 14])
                    res["scens"][scen]["frcu1"] = int(lines[linenum + 15])
                    linenum += 16
                elif res["scens"][scen]["resmgt"] == 5:
                    res["scens"][scen]["jdmove"] = int(lines[linenum + 14])
                    res["scens"][scen]["frmov1"] = float(lines[linenum + 14])
                    linenum += 16
                elif res["scens"][scen]["resmgt"] == 6:
                    linenum += 14
            else:
                # Perrenial Cropland
                res["scens"][scen]["jdharv"] = int(lines[linenum + 10])
                res["scens"][scen]["jdplt"] = int(lines[linenum + 11])
                res["scens"][scen]["jdstop"] = int(lines[linenum + 12])
                res["scens"][scen]["r1"] = float(lines[linenum + 13])
                res["scens"][scen]["mgtopt"] = int(lines[linenum + 14])
                if res["scens"][scen]["mgtopt"] == 1:
                    # Cutting
                    res["scens"][scen]["ncut"] = int(lines[linenum + 15])
                    res["scens"][scen]["cuts"] = [None] * res["scens"][scen][
                        "ncut"
                    ]
                    linenum += 16
                    for cut in range(res["scens"][scen]["ncut"]):
                        res["scens"][scen]["cuts"][cut] = int(lines[linenum])
                        linenum += 1
                elif res["scens"][scen]["mgtopt"] == 2:
                    # Grazing
                    res["scens"][scen]["ncycle"] = int(lines[linenum + 15])
                    res["scens"][scen]["cycles"] = [None] * res["scens"][scen][
                        "ncycle"
                    ]
                    linenum += 16
                    for cycle in range(res["scens"][scen]["ncycle"]):
                        res["scens"][scen]["cycles"][cycle] = {
                            "arr": lines[linenum],
                            "gday": int(lines[linenum + 1]),
                            "gend": int(lines[linenum + 2]),
                        }
                        linenum += 1
                elif res["scens"][scen]["mgtopt"] == 3:
                    linenum += 15
        elif res["scens"][scen]["iplant"] == 2:
            pass
        linenum += 3
    linenum += 3
    res["mantitle"] = lines[linenum]
    res["mandesc"] = "\n".join(lines[linenum + 1 : linenum + 4])
    linenum += 4
    res["nwsofe"] = int(lines[linenum])
    res["inindx"] = [None] * res["nwsofe"]
    linenum += 1
    for idx in range(res["nwsofe"]):
        res["inindx"][idx] = int(lines[linenum])
        linenum += 1
    res["nrots"] = int(lines[linenum])
    linenum += 1
    res["nyears"] = int(lines[linenum])
    sz = res["nyears"] * res["nrots"]
    res["rotations"] = [None] * sz
    linenum += 6
    yidx = 0
    for _rot in range(res["nrots"]):
        for _year in range(res["nyears"]):
            res["rotations"][yidx] = [None] * res["nwsofe"]
            for ofe in range(res["nwsofe"]):
                res["rotations"][yidx][ofe] = {
                    "plant": int(lines[linenum]),
                    "yearindex": int(lines[linenum + 1]),
                }
                linenum += 3
            yidx += 1
        linenum += 4

    return res
