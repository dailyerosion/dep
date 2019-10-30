"""Get some things straight in my head about these OFE files"""
from __future__ import print_function
from pyiem.dep import read_env, read_ofe


def main():
    """Go Main Go"""
    # 272m slope length?  database says 200m, prj has 266m and 6m
    ofe = read_ofe("/i/0/ofe/07040006/0203/070400060203_213.ofe")
    print("OFETOT %s" % (ofe["sedleave"].sum(),))
    print("1 %s" % (ofe[ofe["ofe"] == 1]["sedleave"].sum(),))
    print("2 %s" % (ofe[ofe["ofe"] == 2]["sedleave"].sum(),))
    env = read_env("/i/0/env/07040006/0203/070400060203_213.env")
    print(env["sed_del"].sum())


if __name__ == "__main__":
    main()
