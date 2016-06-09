"""Need to manually edit the .man files after we ran through prj2wepp


northern_AACS.rot:InitialConditions = IniCropDef.Alf_8188 {0.000000, 0}
northern_ACSA.rot:InitialConditions = IniCropDef.Alf_0109 {0.000000, 0}
northern_CSAA.rot:InitialConditions = IniCropDef.Aft_6492 {0.000000, 0}
northern_SAAC.rot:InitialConditions = IniCropDef.Aft_6492 {0.000000, 0}

replace initial conditions section between the string of

###############################
# Initial Conditions Section  #
###############################

1  # Number of initial scenarios

############################
# Surface Effects Section  #
############################

So my current thought is that anywhere I find this string in the generated
.man file:

   184 # perennial plant date --- 7 /3

I should replace it with

   0 # perennial plant date --- 0 /0

"""
import glob
import os
import re

ALF_8188 = """Alf_8188  0
Alfalfa then fall moldboard plowing
Initial conditions following alfalfa and plowing
5 percent ground cover, rough surface
(null)
Alf_5069
1  #landuse
1.10000 0.00000 60 90 0.10000 0.05000
1 # mang annual
50.00000 0.10000 0.00000 0.10000 0.00000
1  # rtyp - temporary
0.00000 0.00000 0.10000 0.20000 0.00000
0.10000 0.20000

"""
ALF_0109 = """Alf_0109
Alfalfa after oats/alfalfa, 1 cutting prior year, for Davis et al rotation
B. K. Gelder
High initial residue levels.
1  #landuse
1.10000 0.00000 180 80 0.05000 0.95000
1 # iresd  <Alf_5069>
2 # mang perennial
200.00000 0.02000 0.95000 0.02000 0.00000
1  # rtyp - temporary
0.00000 0.00000 0.10000 0.20000 0.00000
0.50000 0.20000

"""
AFT_6492 = """Aft_6492
After corn and chisel plow
B.K. Gelder for Davis et al rotation
corn, soy, oats-alfalfa, alfalfa
1  #landuse
1.10000 0.30000 250 80 0.10000 0.30000
1 # iresd  <Cor_0965>
1 # mang annual
50.00000 0.05000 0.30000 0.05000 0.00000
1  # rtyp - temporary
0.00000 0.00000 0.10000 0.20000 0.00000
0.50000 0.20000

"""

ROT2INIT = {'AACS': ALF_8188, 'ACSA': ALF_0109, 'CSAA': AFT_6492,
            'SAAC': AFT_6492}
ROTRE = re.compile("_([CSA]{4}).rot.tmp")

os.chdir('/i/7/prj')
for huc8 in glob.glob("*"):
    os.chdir(huc8)
    for huc4 in glob.glob("*"):
        os.chdir(huc4)
        for prjfn in glob.glob("*.prj"):
            data = open(prjfn).read()
            # Figure out which rotation this is
            rot = ROTRE.findall(data)[0]
            manfn = "/i/7/man/%s/%s/%s.man" % (huc8, huc4, prjfn[:-4])
            data = open(manfn).read()
            # Replace bug with Alfalfa
            data = data.replace("   184 # perennial plant date --- 7 /3",
                                "   0 # perennial plant date --- 0 /0")
            pos1 = data.find("# Initial Conditions Section  #")
            pos2 = data.find("# Surface Effects Section  #")
            newinit = """# Initial Conditions Section  #
###############################

1  # Number of initial scenarios

%s

############################
""" % (ROT2INIT[rot], )
            o = open(manfn, 'w')
            o.write("%s%s%s" % (data[:pos1], newinit, data[pos2:]))
            o.close()
        os.chdir("..")
    os.chdir("..")
