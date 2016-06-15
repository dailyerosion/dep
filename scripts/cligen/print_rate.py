data = """
00.00    0.00
01.73   10.63
04.10   20.88
04.60   30.98
06.86   41.26
08.03   51.42
14.10   61.67
15.56   71.77
17.66   82.21
17.83   92.76
23.96   96.55
"""
t = []
r = []
for line in data.split("\n"):
    tokens = line.split()
    if len(tokens) != 2:
        continue
    t.append(float(tokens[0]))
    r.append(float(tokens[1]))

maxr = 0
for i in range(1, len(t)):
    dt = t[i] - t[i-1]
    dr = r[i] - r[i-1]
    rate = (dr / dt)
    if rate > maxr:
        print("time: %5.2f, rate: %6.2f mm/hr" % (t[i], rate))
        maxr = rate
