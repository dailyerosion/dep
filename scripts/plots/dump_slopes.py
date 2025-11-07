"""Go."""

from pyiem.util import get_dbconn

DBCONN = get_dbconn("wepp")
cursor = DBCONN.cursor()


def read_slope(fn):
    """Go."""
    with open(fn) as fh:
        lines = fh.readlines()
    data = []
    for line in lines:
        if len(line.strip()) == 0 or line[0] == "#":
            continue
        data.append(line)
    data[2].split()[0]
    xs = []
    slp = []
    travel = 0
    for i in range(3, len(data), 2):
        slen = float(data[i].split()[1])
        nums = data[i + 1].replace(",", "").split()
        for pos in nums[0 : len(nums) : 2]:
            xs.append(float(pos) * slen + travel)
        for pos in nums[1 : len(nums) : 2]:
            slp.append(float(pos))
        travel += slen
    h2 = [0]
    x2 = [0]
    for x, s in zip(xs, slp, strict=False):
        h2.append(h2[-1] + (x - x2[-1]) * (0 - s))
        x2.append(x)

    return x2, h2


cursor.execute("SELECT id, model_twp from nri where model_twp = 'T82NR05E'")

slopes1 = {}
for row in cursor:
    x2, y2 = read_slope("/mnt/idep/data/slopes/%s.slp" % (row[0],))
    if not slopes1.has_key(row[1]):
        slopes1[row[1]] = []
    slopes1[row[1]].append((y2[-1] - y2[0]) / (x2[0] - x2[-1]))
