#!/usr/bin/env python
"""Generate a PDF Report for a given HUC12."""
from io import BytesIO
import datetime
import cgi

import requests
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                Table)
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


def generate_summary_table(huc12):
    """Make a table summarizing our results, please."""
    data = []
    data.append(['YEAR', 'PRECIP', "LOSS", "RUNOFF", "DELIVERY"])
    pgconn = get_dbconn('idep')
    cursor = pgconn.cursor()
    cursor.execute("""
        SELECT extract(year from valid) as year, sum(qc_precip),
        sum(avg_loss), sum(avg_runoff), sum(avg_delivery)
        from results_by_huc12 WHERE scenario = 0 and huc_12 = %s
        GROUP by year ORDER by year ASC
    """, (huc12, ))
    for row in cursor:
        data.append(row)

    return Table(data)


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
    # get map
    uri = ('http://dailyerosion.local/'
           'auto/map.wsgi?overview=1&huc=%s&zoom=10'
           ) % (huc12,)
    req = requests.get(uri)
    image = BytesIO(req.content)
    image.seek(0)
    # get map
    uri = ('http://dailyerosion.local/'
           'auto/map.wsgi?overview=1&huc=%s&zoom=300'
           ) % (huc12,)
    req = requests.get(uri)
    image2 = BytesIO(req.content)
    image2.seek(0)
    story.append(Table([
        [Image(image2, width=3.6*inch, height=2.4*inch),
         Image(image, width=3.6*inch, height=2.4*inch)]
    ]))
    story.append(Spacer(inch, inch * 0.25))
    story.append(Paragraph('Yearly Summary', styles['Heading1']))
    story.append(generate_summary_table(huc12))
    story.append(Spacer(inch, inch))
    for i in range(100):
        bogustext = ("This is Paragraph number %s. " % i) * 20
        p = Paragraph(bogustext, styles['Normal'])
        story.append(p)

    def pagecb(canvas, doc):
        """Proxy to our draw_header func"""
        draw_header(canvas, doc, huc12)

    doc.build(story, onFirstPage=pagecb, onLaterPages=pagecb)
    ssw('Content-type: application/pdf\n\n')
    ssw(bio.getvalue())


if __name__ == '__main__':
    main()
