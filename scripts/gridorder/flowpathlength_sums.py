import sys

import pandas as pd

GRIDORDER = sys.argv[1]

df = pd.read_csv("flowpaths%s.csv" % (GRIDORDER,))

print(
    "%% Flowpaths > 22.1: %.3f"
    % (len(df[df["length"] >= 22.1].index) / float(len(df.index)) * 100.0,)
)
print("Delivery: %.3f" % (df[df["length"] >= 22.1]["delivery"].mean(),))
print("Detachment: %.3f" % (df[df["length"] >= 22.1]["avg_det"].mean(),))
