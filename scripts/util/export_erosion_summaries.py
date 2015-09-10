"""
 Create a Shapefile with yearly erosion summarized by huc12

THIS IS EXPORTING DELIVERY AT THE MOMENT

"""
import subprocess
import datetime

dates = """4/9/2011    4/10/2011
5/25/2011    8/1/2011
7/9/2011    7/14/2011
7/27/2011    7/29/2011
4/9/2013    4/11/2013
4/17/2013    4/30/2013
5/19/2013    6/14/2013
6/21/2013    6/28/2013"""


def do(sts, ets):
    """ Process this year """
    subprocess.call(('pgsql2shp -f idep%s_%s.shp -h localhost -p 5555 '
                     '-u mesonet -g geom idep  "select i.geom, r.huc_12, '
                     'sum(avg_delivery) as delivery, '
                     'sum(avg_loss) as loss, '
                     'sum(avg_runoff) as runoff from results_by_huc12 r '
                     'JOIN ia_huc12 i on (i.huc_12 = r.huc_12) where '
                     'valid between \'%s\' and \'%s\' '
                     'and avg_delivery >= 0 and avg_delivery < 1000 '
                     'and scenario = 0 GROUP by r.huc_12, i.geom" '
                     '') % (sts.strftime("%Y%m%d"),
                            ets.strftime("%Y%m%d"),
                            sts.strftime("%Y-%m-%d"),
                            ets.strftime("%Y-%m-%d")), shell=True)


for line in dates.split("\n"):
    tokens = line.strip().split()
    sts = datetime.datetime.strptime(tokens[0], '%m/%d/%Y')
    ets = datetime.datetime.strptime(tokens[1], '%m/%d/%Y')
    print sts, ets
    do(sts, ets)
#for yr in range(2007, 2015):
#    do(yr)