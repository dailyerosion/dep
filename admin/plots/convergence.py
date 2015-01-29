#!/usr/bin/env python
import cgi
import cStringIO
import sys
import numpy as np

def make_plot(huc_12):
    """ Generate the plot please """
    import psycopg2
    import matplotlib
    matplotlib.use('agg')
    import matplotlib.pyplot as plt
    (fig, ax) = plt.subplots(2,1, figsize=(7,9))
    IDEPDB = psycopg2.connect(database='idep', host='iemdb', user='nobody')
    cursor = IDEPDB.cursor()


    cursor.execute("""
    select extract(year from valid) as yr, sum(loss), hs_id from results 
    where huc_12 = %s and scenario = 0 GROUP by hs_id, yr
    """, ( huc_12,))
    data = {}
    for row in cursor:
        year = row[0]
        if not data.has_key(year):
            data[year] = []
        data[year].append( row[1] * 4.463)

    colors = {}
    colorpool = list(plt.get_cmap('jet')(np.linspace(0, 1.0, len(data.keys()))))

    # Convert into numpy arrays    
    for yr in data.keys():
        data[yr] = np.array(data[yr])
    
        x = []
        y = []
        for i in range(1, len(data[yr])):
            x.append(i)
            y.append(np.average(data[yr][:i]))
        
        stddev = np.std(data[yr])
        mu = y[-1]
        cnt = np.sum(np.where(data[yr]>(mu+2.*stddev), 1, 0))
        cnt += np.sum(np.where(data[yr]<(mu-2.*stddev), 1, 0))
        c = colorpool.pop()
        line = ax[0].plot(x, y, color=c, 
            label="%i $\mu$=%.1f $\mathbb{R}$=%.1f\n$\sigma$=%.1f <$2\sigma$=%.1f%%" % (
            yr, mu, max(data[yr])-min(data[yr]), stddev, 
            (len(data[yr])-cnt)/float(len(data[yr]))*100.))
        colors[yr] = line[0].get_color()

    ax[0].set_title("Soil Detachment Convergence for HUC12: %s" % (huc_12))
    ax[0].set_ylabel("Average Soil Detachment [tons/acre]")
    ax[0].set_xlabel("Increasing Hillslope Sample Size")
    ax[0].grid(True)
    
    # Shrink current axis's height by 10% on the bottom
    box = ax[0].get_position()
    ax[0].set_position([box.x0, box.y0 + box.height * 0.35,
                 box.width, box.height * 0.65])

    ax[0].legend(loc='upper center', bbox_to_anchor=(0.5, -0.25),
          fancybox=True, shadow=True, ncol=3, scatterpoints=1, fontsize=10)


    for yr in data.keys():
        sorted_data = np.sort(data[yr])
        yvals=np.arange(len(sorted_data))/float(len(sorted_data))
        ax[1].plot(sorted_data, yvals * 100.0, color=colors[yr], lw=2)

    ax[1].grid(True)
    ax[1].set_yticks([0,10,25,50,75,90,100])
    ax[1].set_ylabel("Sample CDF [%]")
    ax[1].set_xlabel("Average Soil Detachment [tons/acre]")

    box = ax[1].get_position()
    ax[1].set_position([box.x0, box.y0,
                 box.width, box.height * 0.75])
    
    # Sent output    
    ram = cStringIO.StringIO()
    plt.savefig( ram, format='png')
    ram.seek(0)
    r = ram.read()

    sys.stdout.write("Content-type: image/png\n\n")
    sys.stdout.write(r)

if __name__ == '__main__':
    # Go Main Go
    form = cgi.FieldStorage()
    huc_12 = form.getfirst('huc_12', '070200090401')

    make_plot(huc_12)