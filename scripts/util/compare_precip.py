import psycopg2
import datetime
import pandas as pd
from pandas.io.sql import read_sql
from pyiem.datatypes import distance
from pyiem.network import Table as NetworkTable
from pyiem.plot import MapPlot
import matplotlib.pyplot as plt


def two(year):
    """Compare yearly totals in a scatter plot"""
    coop = psycopg2.connect(database='coop', host='localhost', port=5555,
                            user='nobody')
    ccursor = coop.cursor()
    idep = psycopg2.connect(database='idep', host='localhost', port=5555,
                            user='nobody')
    icursor = idep.cursor()

    ccursor.execute("""
        SELECT station, sum(precip) from alldata_ia
        WHERE year = %s and station != 'IA0000'
        and substr(station, 3, 1) != 'C' GROUP by station ORDER by station ASC
    """, (year,))
    nt = NetworkTable("IACLIMATE")
    rows = []
    for row in ccursor:
        station = row[0]
        precip = row[1]
        if station not in nt.sts:
            continue
        lon = nt.sts[station]['lon']
        lat = nt.sts[station]['lat']
        icursor.execute("""
            select huc_12 from huc12
            where ST_Contains(geom,
            ST_Transform(ST_SetSRID(ST_Point(%s, %s), 4326), 5070))
            and scenario = 0
        """, (lon, lat))
        if icursor.rowcount == 0:
            continue
        huc12 = icursor.fetchone()[0]
        icursor.execute("""
        select sum(qc_precip) from results_by_huc12
        WHERE valid between %s and %s and huc_12 = %s and scenario = 0
        """, (datetime.date(year, 1, 1), datetime.date(year, 12, 31),
              huc12))
        val = icursor.fetchone()[0]
        if val is None:
            continue
        iprecip = distance(val, 'MM').value('IN')
        rows.append(dict(station=station,
                         precip=precip,
                         iprecip=iprecip,
                         lat=lat, lon=lon))
        # print("%s %s %5.2f %5.2f" % (station, huc12, precip, iprecip))
    df = pd.DataFrame(rows)
    df['diff'] = df['iprecip'] - df['precip']
    bias = df['diff'].mean()
    print("%s %5.2f %5.2f %5.2f" % (year, df['iprecip'].mean(),
                                    df['precip'].mean(), bias))
    m = MapPlot(title=("%s IDEP Precipitation minus IEM Climodat (inch)"
                       ) % (year,),
                subtitle=("HUC12 Average minus point observation, "
                          "Overall bias: %.2f") % (bias,),
                axisbg='white')
    m.plot_values(df['lon'], df['lat'], df['diff'], fmt='%.2f',
                  labelbuffer=1)
    m.postprocess(filename='%s_map.png' % (year,))
    m.close()

    (fig, ax) = plt.subplots(1, 1)
    ax.scatter(df['precip'], df['iprecip'])
    ax.grid(True)
    ylim = ax.get_ylim()
    ax.plot([ylim[0], ylim[1]], [ylim[0], ylim[1]], lw=2)
    ax.set_xlabel("IEM Climodat Precip")
    ax.set_ylabel("IDEP HUC12 Precip")
    ax.set_title("%s Precipitation Comparison, bias=%.2f" % (year, bias))
    fig.savefig('%s_xy.png' % (year,))
    plt.close()


def one():
    iem = psycopg2.connect(database='iem', host='localhost', port=5555,
                           user='nobody')

    idep = psycopg2.connect(database='idep', host='localhost', port=5555,
                            user='nobody')
    icursor = idep.cursor()

    # Get obs
    df = read_sql("""SELECT day, min(pday) as min_pday, avg(pday) as avg_pday,
        max(pday) as max_pday
        from summary_2014 s JOIN stations t on
      (t.iemid = s.iemid) WHERE t.network = 'IA_ASOS'
      GROUP by day""", iem, index_col='day')

    # Get idep
    # Due to join issues, we hardcode the huc12 count
    icursor.execute("""SELECT count(*) from huc12 where states = 'IA'
    and scenario =0""")
    huccount = icursor.fetchone()[0]
    df2 = read_sql("""
        WITH iahuc12 as (
            SELECT huc_12 from huc12 where states = 'IA' and scenario = 0
        )
        SELECT valid, sum(qc_precip) / 25.4 as precip
        from results_by_huc12 r JOIN iahuc12 i on (r.huc_12 = i.huc_12)
        WHERE r.scenario = 0 and r.valid >= '2014-01-01' and
        r.valid < '2015-01-01' GROUP by valid
      """, idep, index_col='valid')

    df['idep'] = df2['precip'] / huccount
    df.fillna(0, inplace=True)
    df['diff2max'] = df['max_pday'] - df['idep']
    df['diff2avg'] = df['avg_pday'] - df['idep']

    df.sort_values(by='diff2avg', inplace=True, ascending=False)

    df.to_excel('test.xls')

if __name__ == '__main__':
    one()
    # for year in range(2007, 2017):
    #    two(year)
