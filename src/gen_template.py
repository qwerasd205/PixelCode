import sys
from PIL import Image, ImageFont, ImageDraw

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

GLYPH_COUNT = 1 + end - start

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
TEMPLATE_CELL_HEIGHT = int(TEMPLATE_CELL_SCALE * TOTAL_HEIGHT)

IMAGE_WIDTH  = TEMPLATE_CELL_WIDTH * min(columns, GLYPH_COUNT)
IMAGE_HEIGHT = TEMPLATE_CELL_HEIGHT * max(1, int(GLYPH_COUNT / columns))

canvas = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), 'black')
draw   = ImageDraw.Draw(canvas)

glyph_font = ImageFont.truetype("FiraCode-VF.ttf", int((CAP_HEIGHT + DESCENT + LEADING) * TEMPLATE_CELL_SCALE))
label_font = ImageFont.truetype("Arial.ttf", int(TEMPLATE_CELL_WIDTH / 15))

for i in range(GLYPH_COUNT):
    cp = start + i
    x = i % columns
    y = int(i / columns)
    x *= ADVANCE
    y *= TOTAL_HEIGHT
    x += LEFT_BEARING + NON_SPACE_WIDTH / 2
    y += BASELINE
    x *= TEMPLATE_CELL_SCALE
    y *= TEMPLATE_CELL_SCALE
    draw.text((x, y), chr(cp), '#9a9a9a', font = glyph_font, anchor = 'ms')

for i in range(min(GLYPH_COUNT, columns)):
    x = i * ADVANCE
    draw.line([(x * TEMPLATE_CELL_SCALE, 0), (x * TEMPLATE_CELL_SCALE, IMAGE_HEIGHT)], fill = 'white', width = 2)

    x += LEFT_BEARING
    # draw.line([(x * TEMPLATE_CELL_SCALE, 0), (x * TEMPLATE_CELL_SCALE, IMAGE_HEIGHT)], fill = 'blue', width = 2)

    x += NON_SPACE_WIDTH
    draw.line([(x * TEMPLATE_CELL_SCALE, 0), (x * TEMPLATE_CELL_SCALE, IMAGE_HEIGHT)], fill = 'blue', width = 2)

    x += RIGHT_BEARING
    draw.line([(x * TEMPLATE_CELL_SCALE, 0), (x * TEMPLATE_CELL_SCALE, IMAGE_HEIGHT)], fill = 'white', width = 2)

for i in range(max(1, int(GLYPH_COUNT / columns))):
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
img = Image.new('RGB', (min(columns, GLYPH_COUNT) * ADVANCE, max(1, int(GLYPH_COUNT / columns)) * TOTAL_HEIGHT), 'black')
img.save(f"./{start:04X}-{end:04X}.png")



