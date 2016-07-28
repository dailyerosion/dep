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
    coop = psycopg2.connect(database='coop', host='iemdb', user='nobody')
    ccursor = coop.cursor()
    idep = psycopg2.connect(database='idep', host='iemdb', user='nobody')
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
            ST_Transform(ST_SetSRID(ST_Point(%s, %s), 4326), 26915))
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
        iprecip = distance(icursor.fetchone()[0], 'MM').value('IN')
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
    iem = psycopg2.connect(database='iem', host='iemdb', user='nobody')

    idep = psycopg2.connect(database='idep', host='iemdb', user='nobody')

    # Get obs
    df = read_sql("""SELECT day, coalesce(pday, 0) as pday
        from summary_2015 s JOIN stations t on
      (t.iemid = s.iemid) WHERE t.id = 'AMW'""", iem, index_col='day')

    # Get idep
    df2 = read_sql("""
        SELECT valid, qc_precip / 25.4 as pday from results_by_huc12
        WHERE scenario = 0 and huc_12 = '070801050903'
        and valid >= '2015-01-01'
      """, idep, index_col='valid')

    df['idep'] = df2['pday']
    df.fillna(0, inplace=True)
    df['diff'] = df['pday'] - df['idep']

    df2 = df.sort('diff')

    df.to_excel('test.xls')

for year in range(2007, 2017):
    two(year)
