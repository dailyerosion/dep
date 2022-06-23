"""Create the generalized irrigation files, for now.

https://www.ars.usda.gov/ARSUserFiles/50201000/WEPP/usersum.pdf page 60
"""
from datetime import date

LASTYEAR = date.today().year


def main():
    """Create files."""
    for ofecnt in range(1, 7):  # Do we have more than 6 OFEs?
        fn = f"/i/0/irrigation/ofe{ofecnt}.txt"
        with open(fn, "w", encoding="utf-8") as fh:
            fh.write("95.7\n")  # datver
            fh.write(f"{ofecnt} 2 1\n")  # furrow depletion
            fh.write("0.013 0.025\n")  # mindepth maxdepth
            for year in range(2007, LASTYEAR + 1):
                for ofe in range(1, ofecnt):
                    fh.write(
                        f"{ofe} 0.176E-05 1.3 0.5 1.0 175 {year} 185 {year}\n"
                    )


if __name__ == "__main__":
    main()
