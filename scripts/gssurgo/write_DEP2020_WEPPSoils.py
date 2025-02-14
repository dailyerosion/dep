"""
Write_DEP2020_WEPPsoils.py

Using data tables generated from the SDM Soils Data version 10.15.2012
write the WEPP soils files (.SOL) in the 2006.2 format.

Output files will be written using the SSURGO MUKEY as the name descriptor.

original coding: DE James 03.2013
04/3/2013 - add 'HrzCount > 0' to selection criteria
09/2014 - update to use FY2014 data - no changes except you must hand-edit
            those SOL files with more than 9 horizons...should be just 1
06/2015 - update to use 8-state MWDEP data
04/2018 - Use the subset -- MWDEP_SoilParameters table for reduced file count
            Set and use zCount to write no more than 9 horizon records -- 185
            records or so
11/2019 - modify to trap >9 recortds and write the correct hrzCount
10/28/2019 - Modify write statement for Kr from f6.2 to f6.4
12/16/2019 - add comment status to MUKEY declaration as per DHerzmann and his
    new reader
05/26/2021 - Add 'Is Not Null' test for KI, TC, KR after failed record for
    udorthents
    Add test for file exists so I didn't to do 200,000 records again, because
    this a national extraction (300,000+ MUKEYs)
"""

import os

from pyiem.database import get_dbconn
from pyiem.util import utc


def main():
    """Main loop."""
    #
    outPath = "/i/0/sol_input_fy2024"

    # SQL Server connect
    cxn = get_dbconn("idep")

    Pcursor = cxn.cursor()
    Pcursor.execute(
        """Select mukey, compname, Albedo, Texture, HrzCount, KI, KR, TC, KB
        From gssurgo24.DEP_SoilParameters
        Where HrzCount > 0 AND Albedo Is Not Null AND compname != 'Aquolls'
        AND KI Is Not Null AND KR Is Not Null AND TC Is Not Null
        AND KB Is Not Null
        """
    )

    MURows = Pcursor.fetchall()
    del Pcursor

    HrzCursor = cxn.cursor()
    for row in MURows:
        fname = f"{outPath}/DEP_{row[0]}.SOL"

        if os.path.exists(fname):
            continue
        lastdepth = 0
        with open(fname, "w", encoding="utf-8") as outf:
            print(f"writing: {fname}  - {row[1]}")

            outf.write("2006.2\n")
            outf.write("#\n")
            outf.write("# DEP SOL\n")
            outf.write(f"# daryl {utc():%Y-%m-%dT%H:%M:%SZ}\n")
            outf.write("# Source: US gSSURGO CONUS FY2024\n")
            outf.write("#\n")
            outf.write(f"SSURGO MUKEY: {row[0]}\n")
            outf.write("1 1\n")

            compname = row[1].replace("'", " ")

            # GH293 limit is 1.8m for soil depth
            HrzCursor.execute(
                """
                SELECT DepthTo_mm, Sand, Clay, OM, CEC7, FragTot
                FROM gssurgo24.DEP_SoilFractions
                WHERE mukey = %s ORDER by DepthTo_mm
                """,
                (row[0],),
            )
            layers = []
            for z, row2 in enumerate(HrzCursor):
                if z > 8:
                    break
                # We want to keep taking rows until we exceed 1.8m and truncate
                # the deepest back to 1800mm
                depth = min(row2[0], 1800)
                layers.append(
                    f"       {depth} {row2[1]} {row2[2]} {row2[3]} "
                    f"{row2[4]} {row2[5]}"
                )
                lastdepth = depth
                if depth == 1800:
                    break
            outf.write(
                f"'{compname}' '{row[3]}' {len(layers)} "
                f"{row[2]} 0.75 {row[5]:.2f} "
                f"{row[6]:.4f} {row[7]:.2f} {row[8]:.2f}\n"
            )
            outf.write("\n".join(layers) + "\n")

            outf.write("0 0 0 0\n")
            outf.write("255 255 255\n")
        # https://github.com/dailyerosion/dep/issues/175
        if lastdepth < 300:
            print(f"Soil {row[0]} too shallow {lastdepth}, culling")
            os.unlink(fname)


if __name__ == "__main__":
    main()
