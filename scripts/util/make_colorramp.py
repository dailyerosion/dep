from PIL import Image, ImageDraw, ImageFont
import numpy

font = ImageFont.truetype("/home/akrherz/projects/pyVBCam/lib/veramono.ttf", 16)
sfont = ImageFont.truetype("/home/akrherz/projects/pyVBCam/lib/veramono.ttf", 14)

units = "tons/acre"
#vals = [0.1, 0.25, 0.5, 1, 1.5, 2, 3, 5, 6,7, 8, '']
vals = [0.05, 0.1, 0.25, 0.5, 0.75, 1, 1.5, 2, 3, 5, 7, '']

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

width = 80
boxsize = 20
borderx = 10
bordery = 30
vertoffset = 10
height = 320

png = Image.new('RGB', (width, height))
draw = ImageDraw.Draw(png)

draw.rectangle([borderx, height-bordery-boxsize, borderx+boxsize, height-bordery], fill=(180,180,180))
draw.text( (borderx+boxsize+5, height-bordery-boxsize), '0', fill='white', font=font)

for i, (c,v) in enumerate(zip(rgb, vals)):
    s = "%s" % (v,)
    (w,h) = draw.textsize(s, font=font)
    ulx = borderx
    uly = height-bordery-(boxsize*(i+2)) - vertoffset
    lrx = borderx + boxsize
    lry = uly + boxsize
    draw.rectangle([ulx, uly, lrx, lry], fill=c, outline='black')
    draw.text([lrx+5, uly-(h/2)], '%s' % (v,), fill='white', font=font)

(w,h) = draw.textsize(units, font=font)
if w >= width:
    (w,h) = draw.textsize(units, font=sfont)
    draw.text([(width/2)-(w/2), height-bordery+(h/2)], units, fill='white', font=sfont)
else:
    draw.text([(width/2)-(w/2), height-bordery+(h/2)], units, fill='white', font=font)

png.save("test.png")
