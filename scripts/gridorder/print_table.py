"""To match requested spreadsheet format"""
import sys
import pandas as pd

HUCS = """101702031901
101702031904
070600010905
070600010906
102300020302
102300020303
102400010103
102300060405
071000030504
071000030802
070801020403
070801020504
070801070302
070801070101
102400130102
102400130201
102802010404
102802010209
070801010701
070801010702"""

gridorder = int(sys.argv[1])

df = pd.read_csv("flowpaths%s.csv" % (gridorder,))
df["huc12"] = df["flowpath"].str.slice(0, 12)
for huc in HUCS.split("\n"):
    df2 = df[df["huc12"] == huc]
    res = dict()
    res["fplen"] = df2["length"].mean()
    res["delivery"] = df2["delivery"].mean()
    res["detach"] = df2["avg_det"].mean()
    df3 = df2[df2["length"] >= 22.1]
    res["fplen221"] = df3["length"].mean()
    res["delivery221"] = df3["delivery"].mean()
    res["detach221"] = df3["avg_det"].mean()
    res["percent"] = len(df3.index) / float(len(df2.index)) * 100.0

    print(
        (
            "%(fplen)s,%(fplen221)s,%(delivery)s,%(detach)s,"
            "%(delivery221)s,%(detach221)s,%(percent)s"
        )
        % res
    )
