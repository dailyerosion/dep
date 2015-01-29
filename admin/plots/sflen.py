#!/usr/bin/env python
""" Flowpath length scatter """
import cgi
import cStringIO
import sys
import glob

def read_slope(fn):
    lines = open(fn).readlines()
    data = []
    for line in lines:
        if len(line.strip()) == 0 or line[0] == '#':
            continue
        data.append(line)
    fplen = data[2].split()[0]
    xs = []
    slp = []
    travel = 0
    for i in range(3, len(data), 2):
        slen = float(data[i].split()[1])
        nums = data[i+1].replace(",", "").split()
        for pos in nums[0:len(nums):2]:
            xs.append( float(pos) * slen + travel )
        for pos in nums[1:len(nums):2]:
            slp.append( float(pos) )
        travel += slen
    h2 = [0]
    x2 = [0]
    for x, s in zip(xs, slp):
        h2.append( h2[-1] + (x - x2[-1]) * (0- s) )
        x2.append( x )

    return x2, h2, travel

def make_plot(huc_12):
    """ Generate the plot please """

    import matplotlib
    matplotlib.use('agg')
    import matplotlib.pyplot as plt
    (fig, ax) = plt.subplots(2,1)
    
    flengths = [[], [], []]
    for fn in glob.glob("/i/1/slp/%s/%s/*.slp" % (huc_12[:8], 
                                                   huc_12[8:])):
        x,y,flen = read_slope(fn)
        flengths[1].append( flen )

        x,y,flen = read_slope("/i/2"+fn[4:])
        flengths[2].append( flen )
     
    ax[0].set_title("Slope Length Comparison for HUC12: %s" % (huc_12,))
    ax[0].scatter(flengths[2], flengths[1])
    ax[0].set_xlim(left=0)
    ax[0].grid(True)
    ax[0].set_ylim(bottom=0)
    ax[0].plot([0, max(flengths[2])], [0, max(flengths[2])])
    ax[0].set_xlabel("dbfsOrgnlTesting slope length [m]")
    ax[0].set_ylabel("G4 slope length [m]")
    
    ax[1].boxplot([flengths[1], flengths[2]])
    ax[1].set_xticks([1,2])
    ax[1].set_xticklabels(['IDEPv2 G4', 'IDEPv2 dbfsOrgnlTesting'])
    ax[1].set_ylabel("Slope Length (m)")
    ax[1].grid(True)
     
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