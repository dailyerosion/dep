"""Create a map of where we have climate files!"""
import psycopg2
import numpy as np
import os
import glob
from pyiem.plot import MapPlot


def get_domain():
    pgconn = psycopg2.connect(database='idep', host='iemdb', user='nobody')
    cursor = pgconn.cursor()
    cursor.execute("""with ext as (
        SELECT ST_Extent(ST_Transform(geom, 4326)) as e from huc12
        WHERE scenario = 0)
    SELECT st_xmin(ext.e), st_xmax(ext.e), st_ymin(ext.e), st_ymax(ext.e)
    from ext""")
    return np.array(cursor.fetchone())


def make_grid(extent):
    x100 = [int(x) for x in (extent * 100.)]
    nx = x100[1] - x100[0]
    ny = x100[3] - x100[2]
    return np.zeros((ny, nx))


def update_grid(extent, grid):
    os.chdir("/i/0/cli")
    for mydir in glob.glob("*"):
        os.chdir(mydir)
        for fn in glob.glob("*.cli"):
            tokens = fn[:-4].split("x")
            lon = 0 - float(tokens[0])
            lat = float(tokens[1])
            x = int((lon - extent[0]) * 100)
            y = int((lat - extent[2]) * 100)
            grid[y, x] = 1
        os.chdir("..")


def draw_map(extent, grid):
    a = np.sum(grid)
    shp = grid.shape
    b = shp[0] * shp[1]
    c = float(a) / float(b) * 100.
    m = MapPlot(sector='custom',
                west=extent[0], east=extent[1], south=extent[2],
                north=extent[3],
                title='2 August 2016 :: DEP Precip Cells',
                subtitle=('%.0f / %.0f %.2f%% Cells Currently Processed'
                          ) % (a, b, c))
    xaxis = extent[0] + np.arange(shp[1] + 1) * 0.01
    yaxis = extent[2] + np.arange(shp[0] + 1) * 0.01
    lons, lats = np.meshgrid(xaxis, yaxis)
    m.pcolormesh(lons, lats, grid, [0, 1, 2])
    m.postprocess(filename='/tmp/map_clipoints.png')
    m.close()


def main():
    extent = get_domain()
    grid = make_grid(extent)
    update_grid(extent, grid)
    draw_map(extent, grid)

if __name__ == '__main__':
    main()
