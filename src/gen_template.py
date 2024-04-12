import sys
import os
from PIL import Image, ImageFont, ImageDraw
from fontTools.unicodedata import east_asian_width
from fontTools.ttLib import TTFont
from math import ceil

def printUsage():
    print("gen_template: Creates a (high resolution) reference template image for a codepoint range.")
    print("Usage: gen_template <start> <end> [columns]")
    print("Example: gen_template 0000 007F 16")
    exit(1)

if len(sys.argv) < 3:
    printUsage()

start   = 0
end     = 0
columns = 0

try:
    start   = int(sys.argv[1], 16)
    end     = int(sys.argv[2], 16)
    columns = int(sys.argv[3]) if len(sys.argv) >= 4 else 16
except Exception:
    printUsage()

def charWidth(c):
    ch = chr(c)
    east_asian_class = east_asian_width(ch)
    # For Full Width and Wide characters, return 2, otherwise return 1.
    if east_asian_class == "F" or east_asian_class == "W":
        return 2
    return 1

GLYPH_COUNT = 1 + end - start

COLS = 0
ROWS = 1

x = 0
for c in range(GLYPH_COUNT):
    cp = c + start
    w = charWidth(cp)
    if w > 1 and x == columns - 1:
        ROWS += 1
        x = 0
    x += w
    if x > columns:
        x -= columns
        ROWS += 1
    COLS = max(x, COLS)

LEFT_BEARING  = 0
RIGHT_BEARING = 1
ADVANCE       = 6
NON_SPACE_WIDTH = ADVANCE - RIGHT_BEARING - LEFT_BEARING

BASELINE = 10
DESCENT  = 1
LEADING  = 1
TOTAL_HEIGHT = BASELINE + DESCENT + LEADING

X_HEIGHT   = 5
CAP_HEIGHT = 7

TEMPLATE_CELL_WIDTH  = 128
TEMPLATE_CELL_SCALE  = (TEMPLATE_CELL_WIDTH / ADVANCE)
TEMPLATE_CELL_HEIGHT = ceil(TEMPLATE_CELL_SCALE * TOTAL_HEIGHT)

IMAGE_WIDTH  = TEMPLATE_CELL_WIDTH * COLS
IMAGE_HEIGHT = TEMPLATE_CELL_HEIGHT * ROWS

canvas = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), 'black')
draw   = ImageDraw.Draw(canvas)

FONT_DIRS = []
if sys.platform == "linux":
    FONT_DIRS = ['/usr/share/fonts', '/usr/local/share/fonts', os.path.expanduser('~/.fonts')]
elif sys.platform == "darwin":
    FONT_DIRS = ['/System/Library/Fonts', '/System/Library/Fonts/Supplemental', '/Library/Fonts', os.path.expanduser('~/Library/Fonts')]

def findFont(name):
    for fdir in FONT_DIRS:
        fpath = os.path.join(fdir, name)
        if os.path.isfile(fpath):
            return fpath

# Replace this list with one tuned to your system.
FONTS = [p for p in [findFont(f) for f in [
    "FiraCode-VF.ttf",
    "FiraCodeNerdFont-Regular.ttf",
    "Apple Symbols.ttf",
    "ZapfDingbats.ttf",
    "NotoEmoji-Regular.ttf",
    "NotoSans-Regular.ttf",
    "Times New Roman.ttf",
    "Arial Unicode.ttf",
    # Last ditch effort
    "unifont-15.1.05.otf",
    "unifont_upper-15.1.05.otf",
    "unifont_csur-15.1.05.otf"
]] if p is not None]

TT_FONTS = dict()
for f in FONTS:
    TT_FONTS[f] = TTFont(f)

print("Using fonts:")
print(FONTS)

def charInFont(unicode_char, font):
    for cmap in font['cmap'].tables:
        if cmap.isUnicode():
            if ord(unicode_char) in cmap.cmap:
                return True
    return False

def getFontFor(char):
    for fontpath in FONTS:
        font = TT_FONTS[fontpath]
        if 'cmap' in font and charInFont(char, font):
            return fontpath
    # Fallback to default font
    return FONTS[0]

IMAGE_FONTS = dict()
for font in FONTS:
    IMAGE_FONTS[font] = ImageFont.truetype(font, int((CAP_HEIGHT + DESCENT + LEADING) * TEMPLATE_CELL_SCALE))

def glyphFontFor(char):
    return IMAGE_FONTS[getFontFor(char)]

label_font = ImageFont.truetype("Arial.ttf", int(TEMPLATE_CELL_WIDTH / 15))

wide_i = 0
for i in range(GLYPH_COUNT):
    cp = start + i
    if charWidth(cp) > 1 and wide_i % columns == columns - 1:
        wide_i += 1
    x = wide_i % columns
    y = int(wide_i / columns)
    x *= ADVANCE
    y *= TOTAL_HEIGHT
    if charWidth(cp) > 1:
        draw.rectangle([(x * TEMPLATE_CELL_SCALE, y * TEMPLATE_CELL_SCALE), ((x + ADVANCE * 2) * TEMPLATE_CELL_SCALE, (y + TOTAL_HEIGHT) * TEMPLATE_CELL_SCALE)], '#331212')
        x += ADVANCE / 2
    x += LEFT_BEARING + NON_SPACE_WIDTH / 2
    y += BASELINE
    x *= TEMPLATE_CELL_SCALE
    y *= TEMPLATE_CELL_SCALE
    draw.text((x, y), chr(cp), '#9a9a9a', font = glyphFontFor(chr(cp)), anchor = 'ms')
    wide_i += charWidth(cp)

for i in range(COLS):
    x = i * ADVANCE
    draw.line([(x * TEMPLATE_CELL_SCALE, 0), (x * TEMPLATE_CELL_SCALE, IMAGE_HEIGHT)], fill = 'white', width = 2)

    x += LEFT_BEARING
    # draw.line([(x * TEMPLATE_CELL_SCALE, 0), (x * TEMPLATE_CELL_SCALE, IMAGE_HEIGHT)], fill = 'blue', width = 2)

    x += NON_SPACE_WIDTH
    draw.line([(x * TEMPLATE_CELL_SCALE, 0), (x * TEMPLATE_CELL_SCALE, IMAGE_HEIGHT)], fill = 'blue', width = 2)

    x += RIGHT_BEARING
    draw.line([(x * TEMPLATE_CELL_SCALE, 0), (x * TEMPLATE_CELL_SCALE, IMAGE_HEIGHT)], fill = 'white', width = 2)

for i in range(ROWS):
    y = i * TOTAL_HEIGHT
    draw.line([(0, y * TEMPLATE_CELL_SCALE), (IMAGE_WIDTH, y * TEMPLATE_CELL_SCALE)], fill = 'white', width = 2)

    y += BASELINE - CAP_HEIGHT
    draw.line([(0, y * TEMPLATE_CELL_SCALE), (IMAGE_WIDTH, y * TEMPLATE_CELL_SCALE)], fill = 'magenta', width = 2)

    y += CAP_HEIGHT - X_HEIGHT
    draw.line([(0, y * TEMPLATE_CELL_SCALE), (IMAGE_WIDTH, y * TEMPLATE_CELL_SCALE)], fill = 'darkgray', width = 2)

    y += X_HEIGHT
    draw.line([(0, y * TEMPLATE_CELL_SCALE), (IMAGE_WIDTH, y * TEMPLATE_CELL_SCALE)], fill = 'orange', width = 2)

    y += DESCENT
    draw.line([(0, y * TEMPLATE_CELL_SCALE), (IMAGE_WIDTH, y * TEMPLATE_CELL_SCALE)], fill = 'darkgray', width = 2)

    y += LEADING
    draw.line([(0, y * TEMPLATE_CELL_SCALE), (IMAGE_WIDTH, y * TEMPLATE_CELL_SCALE)], fill = 'white', width = 2)

canvas.save(f"./TEMPLATE_{start:04X}-{end:04X}.png")
img = Image.new('RGB', (COLS * ADVANCE, ROWS * TOTAL_HEIGHT), 'black')
img.save(f"./{start:04X}-{end:04X}.png")



