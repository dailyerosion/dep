# CopyMUraster_2021.py
# Assemble by state the 10m gSSURGO rasters for a national mosaic.
## NB: Needs to be updated to run in Pro - copyraster syntax failed.
# Import system modules
import arcpy
from arcpy import env
from arcpy.sa import *
import sys, string, os

env.overwriteOutput = True
env.parallelProcessingFactor = "90%"

# Set extensions & environments
arcpy.CheckOutExtension("Spatial")

##------------------------------------------------------------------------------
##------------------------------------------------------------------------------

if __name__ == "__main__":

    inFolder = r"D:\USData\US_Soils\stateSoils_Oct2021\stateSoilsData"
    outFGDB = r"D:\USData\US_Soils\stateSoil10mrasters.gdb"

    # Input data
    # -----------------------------------------------------------------------------
    env.workspace = inFolder
    # inStates = arcpy.ListWorkspaces("*", "FileGDB")
    inWrkFolder = arcpy.ListWorkspaces("*")

    for folder in inWrkFolder:

        ST = os.path.basename(folder[-2:])
        inFGDB = os.path.join(folder, "gSSURGO_%s.gdb" % ST)
        arcpy.AddMessage("copying %s" % (inFGDB))

        env.workspace = inFGDB
        outRaster = os.path.join(outFGDB, "%s_MURaster_10m" % (ST))
        # arcpy.AddMessage("copying %s  to %s" %(inFGDB, outRaster))

        if not arcpy.Exists(outRaster):

            arcpy.CopyRaster_management(
                "MapunitRaster_10m",
                outRaster,
                "",
                "",
                "",
                "",
                "",
                "32_BIT_SIGNED",
            )

        env.workspace = ""
