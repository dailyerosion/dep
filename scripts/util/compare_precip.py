import psycopg2
from pandas.io.sql import read_sql

iem = psycopg2.connect(database='iem', host='iemdb', user='nobody')

idep = psycopg2.connect(database='idep', host='iemdb', user='nobody')

# Get obs
df = read_sql("""SELECT day, coalesce(pday, 0) as pday
    from summary_2015 s JOIN stations t on
  (t.iemid = s.iemid) WHERE t.id = 'AMW'""", iem, index_col='day')

# Get idep
df2 = read_sql("""SELECT valid, qc_precip / 25.4 as pday from results_by_huc12
  WHERE scenario = 0 and huc_12 = '070801050903' and valid >= '2015-01-01'
  """, idep, index_col='valid')

df['idep'] = df2['pday']
df.fillna(0, inplace=True)
df['diff'] = df['pday'] - df['idep']

df2 = df.sort('diff')

df.to_excel('test.xls')
