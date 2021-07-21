"""Summarize the OFE files"""
import os
import datetime

import pandas as pd
from tqdm import tqdm
from pyiem.dep import read_ofe, read_man, read_slp

# See import/flowpath2prj for table about these codes.
LABEL2CODE = {
    "ALFALFA": "P",
    "soybean2": "B",
    "Soy_2191": "B",
    "Soy_2192": "B",
    "Soy_2193": "B",
    "Soy_2194": "B",
    "Corn": "C",
    "Cor_0967": "C",
    "Cor_0966": "C",
    "Cor_0965": "C",
    "Cor_0964": "C",
    "Tre_2932": "I",
    "bromegr1": "P",
    "Bar_8319": "R",
}
# 2007 is skipped
YEARS = 2021 - 2008


def get_rotation_string(manres, ofe):
    """Uffff"""
    codes = []
    for rot in manres["rotations"]:
        idx = rot[ofe - 1]["yearindex"]
        ntype = manres["scens"][idx - 1]["ntype"]
        codes.append(LABEL2CODE.get(manres["crops"][ntype - 1]["crpnam"], "_"))
    return "".join(codes)


def get_soils(prjfn):
    """Hack to get soil names from prj and soil file"""
    soils = []
    for line in open(prjfn):
        if line.find("/sol_input/") == -1:
            continue
        soils.append(line.split("_")[2].split(".")[0])
    # now read sol file
    names = []
    for line in open(prjfn.replace("prj", "sol")):
        if not line.startswith("'"):
            continue
        names.append(line[1:].split("'")[0])
    if len(names) == len(soils):
        return soils
    # uh oh, more work to do
    mapping = {}
    i = 0
    for name in names:
        if name in mapping:
            continue
        mapping[name] = soils[i]
        i += 1
    return [mapping[name] for name in names]


def main():
    """Go Main Go"""
    # ['id', 'CropRotationString', 'slope',
    #                           'rainfall', 'runoff', 'detach', 'delivery'])
    rows = []
    for root, _dirs, files in tqdm(os.walk("/i/0/ofe")):
        for filename in files:
            ofedf = read_ofe("%s/%s" % (root, filename))
            # Drop any 2007 or 2018+ data
            ofedf = ofedf[
                (ofedf["date"] < datetime.datetime(2021, 1, 1))
                & (ofedf["date"] >= datetime.datetime(2008, 1, 1))
            ]
            # Figure out the crop string
            man = "%s/%s" % (
                root.replace("ofe", "man"),
                filename.replace("ofe", "man"),
            )
            try:
                manres = read_man(man)
            except Exception as exp:
                print("failure reading %s\n%s" % (man, exp))
                continue

            slp = "%s/%s" % (
                root.replace("ofe", "slp"),
                filename.replace("ofe", "slp"),
            )
            slpres = read_slp(slp)
            soils = get_soils(slp.replace("slp", "prj"))
            for ofe in ofedf["ofe"].unique():
                myofe = ofedf[ofedf["ofe"] == ofe]
                length = slpres[ofe - 1]["x"][-1] - slpres[ofe - 1]["x"][0]
                slp = (
                    slpres[ofe - 1]["y"][0] - slpres[ofe - 1]["y"][-1]
                ) / length
                rows.append(
                    {
                        "id": "%s_%s" % (filename[:-4], ofe),
                        "huc12": filename[:12],
                        "fpath": filename.split("_")[1][:-4],
                        "ofe": ofe,
                        "CropRotationString": (
                            get_rotation_string(manres, ofe)
                        ),
                        "slope[1]": slp,
                        "soil_mukey": soils[ofe - 1],
                        "rainfall": -1,
                        "runoff[mm/yr]": myofe["runoff"].sum() / YEARS,
                        "detach": -1,
                        "length[m]": length,
                        "delivery[t/a/yr]": (
                            myofe["sedleave"].sum() / YEARS / length * 4.463
                        ),
                    }
                )

    df = pd.DataFrame(rows)
    df.to_csv("results.csv", index=False)


if __name__ == "__main__":
    main()
