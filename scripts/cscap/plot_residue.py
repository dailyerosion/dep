import datetime
import pandas as pd
import matplotlib.pyplot as plt


def myread(fn):
    rows = []
    for i, line in enumerate(open(fn)):
        if i < 13:
            continue
        tokens = line.strip().split()
        if len(tokens) < 9:
            continue
        date = datetime.date(int(tokens[2]), 1, 1)
        date = date + datetime.timedelta(days=(int(tokens[1])-1))
        rows.append(dict(date=date, rill=float(tokens[6]),
                         inter=float(tokens[7])))

    return pd.DataFrame(rows)

df22 = myread('22_102400120405_9.crop')
df23 = myread('23_102400120405_9.crop')

(fig, ax) = plt.subplots(1, 1, figsize=(8, 6))
ax.plot(df22['date'], df22['inter'], label="CS No Cover NoTill")
ax.plot(df23['date'], df23['inter'], label='CS Cover NoTill')
ax.grid(True)
ax.set_ylabel('Residue Cover')
ax.legend(ncol=2)
ax.set_title("CSCAP Scenario Comparison for HUC12: 102400120405 HS: 9")

fig.savefig('test.png')
