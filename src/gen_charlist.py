from fontTools.unicodedata import east_asian_width
from fontTools.ttLib import TTFont
from html import escape

FONT = TTFont("../dist/ttf/PixelCode.ttf")

def charWidth(c):
    ch = chr(c)
    east_asian_class = east_asian_width(ch)
    # For Full Width and Wide characters, return 2, otherwise return 1.
    if east_asian_class == "F" or east_asian_class == "W":
        return 2
    return 1

def printAllChars(font):
    chars = {0}
    for cmap in font['cmap'].tables:
        if cmap.isUnicode():
            for c in cmap.cmap:
                chars.add(c)
    listed = [c for c in chars]
    listed.sort()
    x = 0
    for c in listed:
        w = charWidth(c)
        print(f"{escape(chr(c))}{"" if w > 1 else " "}", end="")
        x += 2
        if x >= 64:
            print("")
            x = 0


printAllChars(FONT)
