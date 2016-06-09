import glob
import sys
import os
import pandas as pd
import re

SCENARIO = sys.argv[1]
REFIND = re.compile("([0-9]+)\s+# number of OFE's")

rows = []
os.chdir("/i/%s/man" % (SCENARIO,))
for huc8 in glob.glob("*"):
    os.chdir(huc8)
    for huc4 in glob.glob("*"):
        os.chdir(huc4)
        for man in glob.glob("*.man"):
            tokens = REFIND.findall(open(man).read())
            rows.append(dict(huc12=huc8+huc4, cnt=int(tokens[0])))
        os.chdir("..")
    os.chdir("..")

df = pd.DataFrame(rows)

print df.groupby('cnt').count()
