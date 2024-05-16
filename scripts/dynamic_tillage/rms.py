import glob

import pandas as pd

dfs = []
for fn in glob.glob("corn*KS.csv"):
    dfs.append(pd.read_csv(fn))

df = pd.concat(dfs)
df["valid"] = pd.to_datetime(df["valid"])
df["delta"] = df["dep_planted"] - df["corn planted"]

# compute root mean square error
print(df["delta"].pow(2).groupby(df["valid"].dt.year).mean().pow(0.5))
