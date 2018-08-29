import matplotlib.pyplot as plt
import random
import numpy as np

(fig, ax) = plt.subplots(1, 1)

x = []
y = []
cnts = []
data = []
for i in range(250):
    x.append(i)
    data.append(random.randint(0, 100))
    std = np.std(data)
    avg = np.average(data)
    y.append(avg)
    cnt = np.sum(np.where(data>(avg+std*2), 1, 0))
    cnt += np.sum(np.where(data<(avg-std*2), 1, 0))
    cnts.append((len(data)-cnt)/float(len(data))*100.)
    
ax.plot(x, y)
ax2 = ax.twinx()
ax2.plot(x, cnts, color='r')
ax2.set_ylabel("Percentage within 2 sigma [%]", color='r')
ax2.set_ylim(0,102)

ax.set_xlabel("Random Sample Size Increase")
ax.set_ylabel("Average", color='b')
ax.set_ylim(0,102)
ax.set_title("Random Sampling between 0 and 100")

ax.grid(True)
ax.set_yticks([0,25,50,75,100])

fig.savefig('test.png')