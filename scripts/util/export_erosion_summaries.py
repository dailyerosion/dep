"""
 Create a Shapefile with yearly erosion summarized by huc12

THIS IS EXPORTING DELIVERY AT THE MOMENT

"""
import subprocess


def do(year):
    """ Process this year """
    subprocess.call(('pgsql2shp -f idep%s.shp -h localhost -p 5555 '
                     '-u mesonet -g geom idep  "select i.geom, r.huc_12, '
                     'sum(avg_delivery) as delivery, '
                     'sum(avg_runoff) as runoff from results_by_huc12 r '
                     'JOIN ia_huc12 i on (i.huc_12 = r.huc_12) where '
                     'valid between \'%s-01-01\' and \'%s-01-01\' '
                     'and avg_delivery >= 0 and avg_delivery < 1000 '
                     'and scenario = 0 GROUP by r.huc_12, i.geom" '
                     '') % (year, year, year+1), shell=True)


for yr in range(2007,2015):
    do(yr)