"""Modify the harvest index found in the management files

See work related to github issue akrherz/dep#41
"""

import os


def main():
    """Go main go"""
    hits = 0
    misses = 0
    for root, _dirs, files in os.walk("/i/27/man"):
        for filename in files:
            with open(f"{root}/{filename}") as fp:
                data = fp.read()
            if data.find(" 0.50000 2.60099") == -1:
                if data.find("Corn") > -1:
                    print("BUG %s" % (filename,))
                misses += 1
                continue
            with open(f"{root}/{filename}", "w") as fp:
                fp.write(data.replace(" 0.50000 2.60099", " 0.90000 2.60099"))
            hits += 1
    print("Rewrote %s files, skipped %s files" % (hits, misses))


if __name__ == "__main__":
    main()
