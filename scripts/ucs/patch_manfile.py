"""Need to manually edit the .man files after we ran through prj2wepp

So my current thought is that anywhere I find this string in the generated
.man file:

   184 # perennial plant date --- 7 /3
   304 # perennial stop growth date --- 10/31

I should replace it with

   0 # perennial plant date --- 0 /0
   304 # perennial stop growth date --- 10/31
"""
import glob
import os

os.chdir('/i/7/man')
for huc8 in glob.glob("*"):
    os.chdir(huc8)
    for huc4 in glob.glob("*"):
        os.chdir(huc4)
        for manfn in glob.glob("*.man"):
            data = open(manfn).read()
            # Replace bug with Alfalfa
            data = data.replace(
                ("   184 # perennial plant date --- 7 /3\n"
                 "   304 # perennial stop growth date --- 10/31"),
                ("   0 # perennial plant date --- 0 /0\n"
                 "   304 # perennial stop growth date --- 10/31"))
            o = open(manfn, 'w')
            o.write(data)
            o.close()
        os.chdir("..")
    os.chdir("..")
