# D:\Data\IAErosion\IDEP_Expansion\MWDEP_SoilScripts\update_MWDEP_SOL_field.py
# update the name of the WEPP SOL file in the WEPP soils raster
# if the .SOL file does not exist, set as MWDEP_666.SOL
#
# 09/2014 - Updated for the FY2014 soils
# 06/2015 - Updated for the MWDEP soils

# Import arcpy module
import arcpy
from arcpy import env
from arcpy.sa import *

# from arcpy import mapping as MAP
import sys, os, tempfile, time


def updsoilFiles():
    muList = []
    inRas = r"D:\Data\IAErosion\IDEP_Expansion\DEP_Soils.gdb\MWDEP_gSSURGO"
    solpath = r"D:\Data\IAErosion\IDEP_Expansion\MWDEP_WEPP_SOL2014\\"
    badsoil = "MWDEP_666.SOL"

    # Make a table view

    arcpy.MakeTableView_management(inRas, "mwdepMU_View")

    # Select TileIDs
    Rows = arcpy.da.UpdateCursor("mwdepMU_View", ["MUKEY", "WEPP_SOL"])
    for row in Rows:
        mukey = row[0]
        row[1] = "MWDEP_" + mukey + ".SOL"

        fstr = row[1]
        if not arcpy.Exists(solpath + fstr):
            row[1] = badsoil
            muList.append(fstr)
        Rows.updateRow(row)

    del row
    del Rows

    arcpy.AddMessage("Invalid files: " + str(len(muList)))
    # arcpy.AddMessage(muList)


if __name__ == "__main__":
    # upa the WEPP SOL name
    updsoilFiles()
