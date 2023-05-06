"""Verify that a climate file is well formed."""
import datetime
import sys


def main(argv):
    """Run for a given file."""
    with open(argv[1], encoding="ascii") as fh:
        lines = fh.readlines()
    tokens = lines[4].strip().split()
    syear = int(tokens[4])
    # simyears = int(tokens[5])
    linenum = 15
    yesterday = datetime.date(syear - 1, 12, 31)
    while linenum < len(lines):
        tokens = lines[linenum].split()
        if len(tokens) < 4:
            print(f"linenum: {linenum} has len(tokens): {len(tokens)}")
        thisdate = datetime.date(
            int(tokens[2]), int(tokens[1]), int(tokens[0])
        )
        if (thisdate - yesterday) != datetime.timedelta(days=1):
            print(
                f"linenum: {linenum} has date: {thisdate}, "
                f"not {yesterday + datetime.timedelta(days=1)}"
            )
        yesterday = thisdate
        lastprecip = -1
        lasttime = ""
        ftime = 0
        nrbkpts = int(tokens[3])
        if nrbkpts > 100:
            print(f"Date: {thisdate} has nrbkpts: {nrbkpts} > 100")
        for _ in range(nrbkpts):
            linenum += 1
            tokens = lines[linenum].split()
            if len(tokens) != 2:
                print(f"linenum: {linenum} has bad token count")
            if tokens[0] == lasttime:
                print(f"linenum: {linenum} has duplicated time")
            if float(tokens[0]) < ftime:
                print(f"linenum: {linenum} has time {tokens[0]} < {ftime}")
            ftime = float(tokens[0])
            lasttime = tokens[0]
            tm = float(tokens[0])
            if tm < 0 or tm >= 24:
                print(f"linenum: {linenum} has bad time: {tokens[0]}")
            precip = float(tokens[1])
            if precip < 0 or precip >= 350:
                print(f"{thisdate} line: {linenum} has bad prec: {tokens[1]}")
            if precip <= lastprecip:
                print(
                    f"{thisdate} line: {linenum} has decreasing "
                    f"prec: {tokens[1]}, last {lastprecip}"
                )
            lastprecip = precip
        linenum += 1


if __name__ == "__main__":
    main(sys.argv)
