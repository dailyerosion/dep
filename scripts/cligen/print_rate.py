data = """
02.46    0.00
03.63   10.16
05.83   20.41
08.06   30.87
09.66   40.96
10.06   46.29
10.10   48.97
10.13   52.59
10.16   56.21
10.20   58.68
10.73   68.87
10.83   73.06
10.86   75.26
10.90   77.42
11.20   88.81
16.63   99.11
16.93  109.00
16.96  111.06
19.36  114.02
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
