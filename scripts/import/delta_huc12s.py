"""Figure out which HUC12s are new or missing."""

import os


def main():
    """Go Main Go."""
    with open("myhucs.txt", encoding="utf8") as fh:
        newhucs = [s.strip() for s in fh]
    print("Missing HUC12s")
    missing = []
    for huc8 in os.listdir("/i/0/man"):
        for huc4 in os.listdir(f"/i/0/man/{huc8}"):
            huc12 = f"{huc8}{huc4}"
            if huc12 in newhucs:
                newhucs.remove(huc12)
            else:
                missing.append(huc12)
                print(huc12)
    print("New HUC12s")
    for huc in newhucs:
        print(huc)

    for m in missing:
        print(f"python delete_huc12.py {m} 0")


if __name__ == "__main__":
    main()
