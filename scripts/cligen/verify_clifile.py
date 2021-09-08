"""Verify that a climate file is well formed."""
import sys
import datetime


def main(argv):
    """Run for a given file."""
    fn = argv[1]
    lines = open(fn).readlines()
    tokens = lines[4].strip().split()
    syear = int(tokens[4])
    # simyears = int(tokens[5])
    linenum = 15
    yesterday = datetime.date(syear - 1, 12, 31)
    while linenum < len(lines):
        tokens = lines[linenum].split()
        if len(tokens) < 4:
            print("linenum: %s has len(tokens): %s" % (linenum, len(tokens)))
            sys.exit()
        thisdate = datetime.date(
            int(tokens[2]), int(tokens[1]), int(tokens[0])
        )
        if (thisdate - yesterday) != datetime.timedelta(days=1):
            print(
                "linenum: %s has date: %s, not %s"
                % (linenum, thisdate, yesterday + datetime.timedelta(days=1))
            )
            sys.exit()
        yesterday = thisdate
        lastprecip = -1
        lasttime = ""
        for _ in range(int(tokens[3])):
            linenum += 1
            tokens = lines[linenum].split()
            if len(tokens) != 2:
                print("linenum: %s has bad token count" % (linenum,))
                sys.exit()
            if tokens[0] == lasttime:
                print(f"linenum: {linenum} has duplicated time")
            lasttime = tokens[0]
            tm = float(tokens[0])
            if tm < 0 or tm >= 24:
                print("linenum: %s has bad time: %s" % (linenum, tokens[0]))
                sys.exit()
            precip = float(tokens[1])
            if precip < 0 or precip >= 350:
                print("linenum: %s has bad precip: %s" % (linenum, tokens[1]))
                sys.exit()
            if precip <= lastprecip:
                print(
                    "linenum: %s has decreasing precip: %s, last %s"
                    % (linenum, tokens[1], lastprecip)
                )
                sys.exit()
            lastprecip = precip
        linenum += 1


if __name__ == "__main__":
    main(sys.argv)
