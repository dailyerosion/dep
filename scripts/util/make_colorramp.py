from PIL import Image, ImageDraw, ImageFont
import numpy

FPATH = "/home/akrherz/projects/pyVBCam/lib/veramono.ttf"
font = ImageFont.truetype(FPATH, 16)
sfont = ImageFont.truetype(FPATH, 14)

units = "tons/acre"
#vals = [0.1, 0.25, 0.5, 1, 1.5, 2, 3, 5, 6,7, 8, '']
vals = [0.05, 0.1, 0.25, 0.5, 0.75, 1, 1.5, 2, 3, 5, '7+', '']

data = """
        COLOR 0 0 255
        COLOR 0 102 255
        COLOR 0 212 255
        COLOR 24 255 255
        COLOR 102 255 153
        COLOR 51 255 0
        COLOR 204 255 0
        COLOR 255 255 0
        COLOR 255 232 0
        COLOR 255 204 0
        COLOR 255 153 0
        COLOR 255 102 0
"""
rgb = []
for line in data.split("\n"):
    if line.strip() == "":
        continue
    tokens = line.strip().split()
    rgb.append((int(tokens[1]), int(tokens[2]), int(tokens[3])))

width = 350
boxsize = 25
borderx = 10
bordery = 20
vertoffset = 10
height = 65

png = Image.new('RGB', (width, height), color=(255, 255, 255))
draw = ImageDraw.Draw(png)

# Draw the empty one!
draw.rectangle([borderx, bordery, borderx+boxsize,
                bordery+boxsize], fill=(0, 0, 0))
draw.rectangle([borderx+1, bordery+1, borderx+boxsize-1,
                bordery+boxsize-1], fill=(255, 255, 255))
(w, h) = draw.textsize('0', font=font)
draw.text((borderx+(boxsize)-(w/2), bordery-h-5), '0',
          fill='black', font=font)

for i, (c, v) in enumerate(zip(rgb, vals)):
    s = ("%s" % (v,)).replace("0.", ".")
    (w, h) = draw.textsize(s, font=font)
    uly = bordery
    ulx = borderx+(boxsize*(i+1))
    lry = bordery + boxsize
    lrx = ulx + boxsize
    draw.rectangle([ulx, uly, lrx, lry], fill=c, outline='black')
    if i % 2 == 0:
        uly = lry + h + 5
    else:
        uly -= 5
    draw.text([lrx-(w/2), uly-h], s, fill='black', font=font)

"""
(w, h) = draw.textsize(units, font=font)
if w >= width:
    (w, h) = draw.textsize(units, font=sfont)
    draw.text([(width/2)-(w/2), height-bordery+(h/2)], units, fill='black',
              font=sfont)
else:
    draw.text([(width/2)-(w/2), height-bordery+(h/2)], units, fill='black',
              font=font)
"""
png.save("test.png")
