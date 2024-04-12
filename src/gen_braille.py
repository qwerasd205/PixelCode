from PIL import Image, ImageDraw

CELL_WIDTH = 6
CELL_HEIGHT = 12

IMAGE_WIDTH = 16 * CELL_WIDTH
IMAGE_HEIGHT = 16 * CELL_HEIGHT

canvas = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), 'black')
draw   = ImageDraw.Draw(canvas)

def drawPattern(i, x, y):
    if i & 0b00000001:
        draw.point((x + 1, y + 4), 'white')
    if i & 0b00000010:
        draw.point((x + 1, y + 6), 'white')
    if i & 0b00000100:
        draw.point((x + 1, y + 8), 'white')
    if i & 0b00001000:
        draw.point((x + 3, y + 4), 'white')
    if i & 0b00010000:
        draw.point((x + 3, y + 6), 'white')
    if i & 0b00100000:
        draw.point((x + 3, y + 8), 'white')
    if i & 0b01000000:
        draw.point((x + 1, y + 10), 'white')
    if i & 0b10000000:
        draw.point((x + 3, y + 10), 'white')

x = 0
y = 0
for i in range(256):
    drawPattern(i, x, y)
    x += CELL_WIDTH
    if x >= IMAGE_WIDTH:
        x = 0
        y += CELL_HEIGHT

canvas.save("./glyphs/2800-28FF.png")
