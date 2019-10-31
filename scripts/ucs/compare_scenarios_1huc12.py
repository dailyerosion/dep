"""Sundry."""
import os
import glob

import pyiem.dep as dep_utils

os.chdir("/i/0/env/10230003/1504")
for fn in glob.glob("*.env"):
    df0 = dep_utils.read_env(fn)
    df0.set_index("date", inplace=True)
    df7 = dep_utils.read_env("/i/7/env/10230003/1504/" + fn)
    df7.set_index("date", inplace=True)
    if (df7["sed_del"].sum() - df0["sed_del"].sum()) > 1000:
        print("--- Investigating: %s" % (fn,))
        jdf = df0.join(df7, lsuffix="_s0", rsuffix="_s7")
        jdf["diff_sed_del"] = jdf["sed_del_s7"] - jdf["sed_del_s0"]
        jdf.sort_values(by="diff_sed_del", ascending=False, inplace=True)
        print(
            jdf[
                [
                    "precip_s7",
                    "sed_del_s7",
                    "sed_del_s0",
                    "av_det_s7",
                    "av_det_s0",
                    "runoff_s7",
                    "runoff_s0",
                ]
            ].head(5)
        )
