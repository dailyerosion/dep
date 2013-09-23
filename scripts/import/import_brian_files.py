import glob
import os

os.chdir("c")
for filename in glob.glob("*"):
    tokens = filename.split("_")
    huc12 = tokens[1]
    typ = tokens[2].split(".")[1]
    newfn = "/i/%s/%s/%s" % (typ, huc12, filename)
    os.rename(filename, newfn)