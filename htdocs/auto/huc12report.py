#!/usr/bin/env python
"""Generate a PDF Report for a given HUC12."""
from io import BytesIO
import datetime
import cgi
import calendar

import requests
from pandas.io.sql import read_sql
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                Table, TableStyle, PageBreak)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from pyiem.util import ssw, get_dbconn
PAGE_WIDTH = letter[0]
PAGE_HEIGHT = letter[1]
GENTIME = datetime.datetime.now().strftime("%B %-d %Y")
INTROTEXT = """Hello there! This is from glorious automation. Someday, you will
find interesting things here and actual details on what fun this is trying to
accomplish.  Until then, you must await more magic to happen.
"""


def generate_monthly_summary_table(huc12):
    """Make a table of monthly summary stats."""
    data = []
    data.append(['Year', 'Month', 'Precip', "Runoff", "Loss", "Delivery",
                '2+" Precip', 'Events'])
    data.append(['', '', '[inch]', "[inch]", "[tons/acre]", "[tons/acre]",
                 "[days]", "[days]"])
    pgconn = get_dbconn('idep')
    df = read_sql("""
        SELECT extract(year from valid)::int as year,
        extract(month from valid)::int as month,
        round((sum(qc_precip) / 25.4)::numeric, 2),
        round((sum(avg_runoff) / 25.4)::numeric, 2),
        round((sum(avg_loss) * 4.463)::numeric, 2),
        round((sum(avg_delivery) * 4.463)::numeric, 2),
        sum(case when qc_precip >= 50.8 then 1 else 0 end) as pdays,
        sum(case when avg_loss > 0 then 1 else 0 end) as events
        from results_by_huc12 WHERE scenario = 0 and huc_12 = %s
        and valid >= '2016-01-01'
        GROUP by year, month ORDER by year, month ASC
    """, pgconn, params=(huc12, ), index_col=None)
    for _, row in df.iterrows():
        vals = [int(row['year']), calendar.month_abbr[int(row['month'])]]
        vals.extend(["%.2f" % (f, ) for f in list(row)[2:-2]])
        vals.extend(["%.0f" % (f, ) for f in list(row)[-2:]])
        data.append(vals)
    data[-1][1] = "%s*" % (data[-1][1], )
    totals = df.iloc[:-1].mean()
    vals = ['', 'Average']
    vals.extend(["%.2f" % (f, ) for f in list(totals[2:])])
    data.append(vals)

    style = TableStyle(
        [('LINEBELOW', (2, 1), (-1, 1), 0.5, '#000000'),
         ('LINEAFTER', (1, 2), (1, -2), 0.5, '#000000'),
         ('LINEABOVE', (2, -1), (-1, -1), 0.5, '#000000'),
         ('ALIGN', (0, 0), (-1, -1), 'RIGHT')]
    )
    for rownum in range(3, len(data)+1, 2):
        style.add('LINEBELOW', (0, rownum), (-1, rownum), 0.25, '#EEEEEE')
    return Table(data, style=style)


def generate_summary_table(huc12):
    """Make a table summarizing our results, please."""
    data = []
    data.append(['Year', 'Precip', "Runoff", "Loss", "Delivery",
                '2+" Precip', 'Events'])
    data.append(['', '[inch]', "[inch]", "[tons/acre]", "[tons/acre]",
                 "[days]", "[days]"])
    pgconn = get_dbconn('idep')
    df = read_sql("""
        SELECT extract(year from valid)::int as year,
        round((sum(qc_precip) / 25.4)::numeric, 2),
        round((sum(avg_runoff) / 25.4)::numeric, 2),
        round((sum(avg_loss) * 4.463)::numeric, 2),
        round((sum(avg_delivery) * 4.463)::numeric, 2),
        sum(case when qc_precip >= 50.8 then 1 else 0 end) as pdays,
        sum(case when avg_loss > 0 then 1 else 0 end) as events
        from results_by_huc12 WHERE scenario = 0 and huc_12 = %s
        and valid >= '2008-01-01'
        GROUP by year ORDER by year ASC
    """, pgconn, params=(huc12, ), index_col='year')
    for year, row in df.iterrows():
        vals = [year]
        vals.extend(["%.2f" % (f, ) for f in list(row)[:-2]])
        vals.extend(["%.0f" % (f, ) for f in list(row)[-2:]])
        data.append(vals)
    data[-1][0] = "%s*" % (data[-1][0], )
    totals = df.iloc[:-1].mean()
    vals = ['Average']
    vals.extend(["%.2f" % (f, ) for f in list(totals)])
    data.append(vals)

    style = TableStyle(
        [('LINEBELOW', (1, 1), (-1, 1), 0.5, '#000000'),
         ('LINEAFTER', (0, 2), (0, -2), 0.5, '#000000'),
         ('LINEABOVE', (1, -1), (-1, -1), 0.5, '#000000'),
         ('ALIGN', (0, 0), (-1, -1), 'RIGHT')]
    )
    for rownum in range(3, len(data)+1, 2):
        style.add('LINEBELOW', (0, rownum), (-1, rownum), 0.25, '#EEEEEE')
    return Table(data, style=style)


def draw_header(canvas, doc, huc12):
    """Do our header stuff"""
    canvas.saveState()
    canvas.drawImage('../images/logo_horiz_white.png', inch * 1.,
                     PAGE_HEIGHT - 100)
    canvas.setFont('Times-Bold', 16)
    canvas.drawString(PAGE_WIDTH * 0.35, PAGE_HEIGHT - inch + 20,
                      'Daily Erosion Project HUC12 Summary Report')
    canvas.drawString(PAGE_WIDTH * 0.35, PAGE_HEIGHT - inch,
                      'HUC12: %s' % (huc12, ))
    canvas.drawString(PAGE_WIDTH * 0.35, PAGE_HEIGHT - inch - 20,
                      'Generated %s' % (GENTIME, ))
    canvas.setFont('Times-Roman', 9)
    canvas.drawCentredString(PAGE_WIDTH * 0.5, 0.75 * inch,
                             "Page %s" % (doc.page, ))
    canvas.restoreState()


def get_image_bytes(uri):
    """Return BytesIO object with web content."""
    req = requests.get(uri)
    image = BytesIO(req.content)
    image.seek(0)
    return image


def main():
    """See how we are called"""
    form = cgi.FieldStorage()
    huc12 = form.getfirst('huc12', '070801050306')[:12]
    bio = BytesIO()
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(bio, pagesize=letter, topMargin=(inch * 1.5))
    story = []
    story.append(Paragraph(INTROTEXT, styles['Normal']))
    story.append(Spacer(inch, inch * 0.25))
    story.append(Paragraph('Geographic Location', styles['Heading1']))
    story.append(Table([
        [[Image(get_image_bytes(
             ('http://dailyerosion.local/'
              'auto/map.wsgi?overview=1&huc=%s&zoom=250') % (huc12,)),
          width=3.6*inch, height=2.4*inch),
          Paragraph(('Figure 1: Regional View with HUC8 highlighted in tan'
                     ' and HUC12 in red.'), styles['Normal'])],
         [Image(get_image_bytes(
             ('http://dailyerosion.local/'
              'auto/map.wsgi?overview=1&huc=%s&zoom=11') % (huc12,)),
          width=3.6*inch, height=2.4*inch),
          Paragraph(('Figure 2: Local View with HUC8 highlighted in tan '
                     'and HUC8 in red'), styles['Normal'])]]
    ]))
    story.append(Spacer(inch, inch * 0.25))
    story.append(Paragraph('Yearly Summary', styles['Heading1']))
    story.append(generate_summary_table(huc12))
    story.append(Paragraph(('Table 1: Average value does not include the '
                            'current year. Events column are the number of '
                            'days with non-zero soil loss. '
                            '(* year to date total)'
                            ), styles['Normal']))
    story.append(PageBreak())
    story.append(Spacer(inch, inch * 0.25))
    story.append(Paragraph('Monthly Summary', styles['Heading1']))
    story.append(generate_monthly_summary_table(huc12))

    def pagecb(canvas, doc):
        """Proxy to our draw_header func"""
        draw_header(canvas, doc, huc12)

    doc.build(story, onFirstPage=pagecb, onLaterPages=pagecb)
    ssw('Content-type: application/pdf\n\n')
    ssw(bio.getvalue())


if __name__ == '__main__':
    main()
