"""
 Create a Shapefile with yearly erosion summarized by huc12
"""
import subprocess


def do(year):
    """ Process this year """
    subprocess.call(""" pgsql2shp -f idep%s.shp -h localhost -p 5555 -u mesonet -g geom idep  "select i.geom, r.huc_12, sum(avg_loss) as loss  from results_by_huc12 r JOIN ia_huc12 i on (i.huc_12 = r.huc_12)  where valid between '%s-01-01' and '%s-01-01'  GROUP by r.huc_12, i.geom" """ % (year, year, year+1), shell=True)


for yr in range(2007,2014):
    do(yr)