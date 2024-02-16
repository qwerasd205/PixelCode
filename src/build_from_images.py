import os
import sys
import math
from math import sqrt
# from fontTools.designspaceLib import DesignSpaceDocument
from fontTools.pens.areaPen import AreaPen
from fontTools.agl import UV2AGL, AGL2UV
from ufoLib2.objects import Contour, Glyph, Info, Features, Point
from ufoLib2 import Font
from PIL import Image
from typing import Dict, List, Any

WEIGHT_NAMES = {
    100: 'Thin',
    200: 'ExtraLight',
    300: 'Light',
    400: 'Regular',
    500: 'Medium',
    600: 'DemiBold',
    700: 'Bold',
    800: 'ExtraBold',
    900: 'Black',
    950: 'ExtraBlack',
}

BASELINE = 10
ASCENT   = 8
DESCENT  = 1
ADVANCE  = 6
X_HEIGHT   = 5
CAP_HEIGHT = 7
SCALE = 112

def adjustCoords(x, y):
    return (x * SCALE, (BASELINE - y) * SCALE)

def makeGlyph(name: str, img: Image.Image):
    # glyphPen = TTGlyphPen(None)
    glyph = Glyph(name)
    pen = glyph.getPen() #TransformPen(glyphPen, (1.1, 0, 0, 1.0, 0, 0))
    vectors: List[List[Any]] = [[list([0, 0]) for _ in range(img.height + 1)] for _ in range(img.width + 1)]
    for y in range(0, img.height):
        for x in range(0, img.width):
            if not img.getpixel((x, y)) == 0:
                vectors[x][y][0] -= 1
                vectors[x][y][1] += 1
                vectors[x][y+1][0] += 1
                vectors[x+1][y][1] -= 1

    def getMag(x, y, vert):
        if x >= len(vectors):
            return None
        if y >= len(vectors[x]):
            return None
        return vectors[x][y][vert]

    def next(x, y, vert):
        if vert:
            offset = vectors[x][y][1]
            n = 0 if offset == -1 else 1
            s = 0 if offset == 1 else 1
            if getMag(x, y+offset, 1) == offset:
                return (x, y+offset, True)
            if getMag(x-n, y+n, 0) == -offset:
                return (x-n, y+n, False)
            if getMag(x-s, y+n, 0) == offset:
                return (x-s, y+n, False)
        else:
            offset = vectors[x][y][0]
            n = 0 if offset == -1 else 1
            s = 0 if offset == 1 else 1
            if getMag(x+offset, y, 0) == offset:
                return (x+offset, y, False)
            if getMag(x+n, y-s, 1) == offset:
                return (x+n, y-s, True)
            if getMag(x+n, y-n, 1) == -offset:
                return (x+n, y-n, True)
        return None

    def follow(x, y, vert):
        nextPosition = next(x, y, vert)
        if vert:
            vectors[x][y][1] = 0
        else:
            vectors[x][y][0] = 0
        if nextPosition is not None:
            (nx, ny, nv) = nextPosition
            px = x
            py = y
            if nv:
                if (px != nx):
                    px = nx
                    pen.lineTo(adjustCoords(px, py))
                if (py != ny):
                    py = ny
                    pen.lineTo(adjustCoords(px, py))
            else:
                if (py != ny):
                    py = ny
                    pen.lineTo(adjustCoords(px, py))
                if (px != nx):
                    px = nx
                    pen.lineTo(adjustCoords(px, py))

            follow(nx, ny, nv)

    for y in range(0, img.height):
        for x in range(0, img.width):
            if vectors[x][y][0] != 0:
                pen.moveTo(adjustCoords(x, y))
                follow(x, y, False)
                pen.closePath()
                continue
            if vectors[x][y][1] != 0:
                pen.moveTo(adjustCoords(x, y))
                follow(x, y, True)
                pen.closePath()
                continue

    return glyph
    # return glyphPen.glyph(
    #     dropImpliedOnCurves = True,
    # )

def isClockwise(g: Contour):
    area = AreaPen()
    g.draw(area)
    return area.value < 0

def dot(ax, ay, bx, by):
    return ax*bx + ay*by

def sign(n):
    return n / abs(n)

def thicken(g: Glyph, amount: int):
    factor = amount / 2500
    xfactor = 1
    yfactor = 0.5 if amount > 0 else 1
    for contour in g.contours:
        clockwise = isClockwise(contour)
        s = factor * (0.5 if amount > 0 and clockwise else 1)
        ln = len(contour.points)
        px = contour.points[ln - 1].x
        py = contour.points[ln - 1].y
        sx = contour.points[0].x
        sy = contour.points[0].y
        for i in range(ln):
            point = contour.points[i]
            next  = contour.points[i + 1] if i < ln - 1 else Point(sx, sy)
            pnx = next.x - point.x
            pny = next.y - point.y
            ppx = px - point.x
            ppy = py - point.y
            lnp = sqrt(ppx*ppx + ppy*ppy)
            lnn = sqrt(pnx*pnx + pny*pny)
            d = dot(ppx/lnp, ppy/lnp, pnx/lnn, pny/lnn)
            xo = s * (next.y - py) * (2 if d == 0 else 1) * xfactor
            yo = s * (px - next.x) * (2 if d == 0 else 1) * yfactor
            px = point.x
            py = point.y
            # Keep ligature parts touching the edge correctly:
            if amount > 0 or (g.name is not None and "_" not in g.name) or point.x != 0 and point.x != ADVANCE * SCALE:
                point.x += xo
            point.y += yo

    # Re-align the so the glyph to have a pixel-perfect
    # left side bearing and baseline placement.
    g.move((2 * SCALE * factor * xfactor, 2 * SCALE * factor * yfactor))
    return g

def thin(g: Glyph, amount: int):
    thicken(g, -amount)
    return g

def italicize(g: Glyph, slope: float):
    for contour in g.contours:
        # We skew the x coordinate of points
        # from the baseline to italicize.
        for point in contour.points:
            point.x += point.y * slope
    return g

def glyphName(c):
    return UV2AGL[c] if c in UV2AGL else f"uni{c:02X}"

STRIDE_X = 6
STRIDE_Y = 12

WHITESPACE_GLYPHS = [ord(' ')]

glyphs: Dict[str, Glyph] = {}
ligaGlyphOrder = []
characterMap = {}
altCharacterMap = {}
advanceWidths = {}

features = {}
ligatures = []

def getOrd(c):
    if len(c) == 1:
        return ord(c)
    return AGL2UV[c]

def addLigature(parts, path, suffix, lazy = False):
    names = [glyphName(getOrd(c)) for c in parts]
    ligaName = "_".join(names)
    if suffix:
        ligaName = f"{ligaName}{suffix}"
    partNames = [f"{ligaName}.{i}" for i in range(len(parts))]
    with Image.open(path) as atlas:
        print(f"\"{"".join([chr(getOrd(c)) for c in parts])}\": {atlas.width}x{atlas.height}")
        atlas = atlas.convert("1")

        i = 0
        for x in range(0, atlas.width, STRIDE_X):
            glyph = atlas.crop((x, 0, x + STRIDE_X, STRIDE_Y))
            name = partNames[i]
            glyphs[name] = makeGlyph(name, glyph)
            ligaGlyphOrder.append(name)
            advanceWidths[name] = ADVANCE * SCALE
            i += 1

        glyphs[ligaName] = makeGlyph(ligaName, atlas.crop((0, 0, 0, 0)))
        ligaGlyphOrder.append(ligaName)
        advanceWidths[ligaName] = ADVANCE * SCALE

        ligatures.append({
            "name": ligaName,
            "from": names,
            "to": partNames,
            "lazy": lazy,
        })

def addGlyphsFromDir(dir, suffix = ""):
    for file in os.listdir(dir):
        fullPath = f"{dir}/{file}"
        if os.path.isdir(fullPath):
            if file.startswith("+"):
                addGlyphsFromDir(fullPath, suffix = f"{suffix}.{file[1:]}")
            else:
                addGlyphsFromDir(fullPath, suffix = suffix)
            continue
        if file.endswith(".fea"):
            with open(fullPath) as file:
                features[fullPath] = "\n".join(file.readlines())
            continue
        if file.endswith(".png"):
            name = file.rsplit(".", 1)[0]
            if name.startswith('"'):
                if name.endswith("?"):
                    addLigature(name[1:-2], fullPath, suffix, True)
                else:
                    addLigature(name[1:-1], fullPath, suffix)
                continue
            if "_" in name and not name.startswith("_"):
                if name.endswith("?"):
                    addLigature(name[:-1].split("_"), fullPath, suffix, True)
                else:
                    addLigature(name.split("_"), fullPath, suffix)
                continue
            if "-" in name:
                (start, end) = name.split("-")
                start = ord(start[1]) if start.startswith("'") else int(start, 16)
                end   = ord(end[1]) if end.startswith("'") else int(end, 16)
                with Image.open(fullPath) as atlas:
                    print(f"{file}: {atlas.width}x{atlas.height}, {start}-{end}")
                    atlas = atlas.convert("1")

                    c = start
                    for y in range(0, atlas.height, STRIDE_Y):
                        for x in range(0, atlas.width, STRIDE_X):
                            glyph = atlas.crop((x, y, x + STRIDE_X, y + STRIDE_Y))
                            if c in WHITESPACE_GLYPHS or len(glyph.getcolors()) > 1:
                                name = glyphName(c)
                                if suffix:
                                    name = f"{name}{suffix}"
                                glyphs[name] = makeGlyph(name, glyph)
                                advanceWidths[name] = ADVANCE * SCALE
                                if not suffix:
                                    characterMap[c] = name
                                else:
                                    altCharacterMap[c] = name
                            c += 1
                            if c > end:
                                break
                        if c > end:
                            break
                continue
            continue

with Image.open("./glyphs/_.notdef.png") as notdef:
    print(f"_.notdef.png: {notdef.width}x{notdef.height}")
    glyphs[".notdef"] = makeGlyph(".notdef", notdef)
    advanceWidths[".notdef"] = ADVANCE * SCALE
    characterMap[0] = ".notdef"

addGlyphsFromDir("./glyphs")

def getFamilyName():
    return "Pixel Code"

def getStyleName(weight: int = 400, italicAngle: float = 0.0):
    return f"{WEIGHT_NAMES[weight]}{" Italic" if italicAngle > 0.0 else ""}"

def getStyleNameShort(weight: int = 400, italicAngle: float = 0.0):
    return f"{"Italic" if italicAngle > 0.0 else ""}" if weight == 400 else getStyleName(weight, italicAngle)

def getFullNameShort(weight: int = 400, italicAngle: float = 0.0):
    return f"{getFamilyName().replace(" ", "")} {getStyleNameShort(weight, italicAngle)}".rstrip().replace(" ", "-")

def writeUFO(weight: int = 400, italicAngle: float = 0.0):
    ufo = Font()
    ufo.glyphOrder = (
        [name for _, name in characterMap.items()] +
        [name for _, name in altCharacterMap.items()] +
        ligaGlyphOrder
    )
    for name, glyph in glyphs.items():
        g = Glyph(name)
        g.copyDataFromGlyph(glyph)
        if weight > 400:
            thicken(g, weight - 400)
        elif weight < 400:
            thin(g, 400 - weight)
        if italicAngle > 0:
            italicize(g, math.tan((math.pi / 180) * italicAngle))
        g.width = advanceWidths[name]
        ufo.addGlyph(g)
    for c, name in characterMap.items():
        ufo[name].unicodes = [c]

    isItalic = italicAngle > 0

    familyName     = getFamilyName()
    styleName      = getStyleName(weight, italicAngle)
    styleNameShort = getStyleNameShort(weight, italicAngle)
    fullName       = f"{familyName} {styleNameShort}".strip()
    majorVersion   = 1
    minorVersion   = 22

    ufo.info = Info(
        versionMajor = majorVersion,
        versionMinor = minorVersion,

        # Names
        familyName           = familyName,
        styleName            = styleName,
        postscriptFullName   = fullName,

        # Copyright
        copyright = "Copyright (c) Qwerasd 2024",

        # Name Table (name)
        openTypeNameCompatibleFullName = fullName,
        openTypeNameDescription        = "A pixel font that's actually good for programming.",
        openTypeNameVersion            = f"Version {majorVersion}.{minorVersion}",
        openTypeNameDesigner           = "Qwerasd",

        # Metrics
        unitsPerEm  = 1008,
        descender   = DESCENT * SCALE,
        ascender    = BASELINE * SCALE,
        xHeight     = X_HEIGHT * SCALE,
        capHeight   = CAP_HEIGHT * SCALE,
        # Italic angle in counter-clockwise degrees from the vertical.
        # Zero for upright text, negative for text that leans to the right (forward).
        italicAngle = -italicAngle,

        # Horizontal Header (hhea)
        openTypeHheaAscender  = BASELINE * SCALE,
        openTypeHheaDescender = -(2 * DESCENT) * SCALE,
        openTypeHheaLineGap   = DESCENT * SCALE,

        # OS/2
        openTypeOS2TypoAscender  = ASCENT * SCALE,
        openTypeOS2TypoDescender = -DESCENT * SCALE,
        openTypeOS2TypoLineGap   = DESCENT * SCALE,
        openTypeOS2WinAscent     = (2 * DESCENT + BASELINE) * SCALE,
        openTypeOS2WinDescent    = (2 * DESCENT) * SCALE,
        openTypeOS2Panose        = [
            # https://monotype.github.io/panose/pan2.htm
            # Family Kind
            # (2 = Latin Text)
            2,
            # Serif Style Classification
            # (0 = Any)
            0,
            # Weight
            # (0 = Any)
            0,
            # Proportion
            # (9 = Monospaced)
            9,
            # Contrast
            # (0 = Any)
            0,
            # Stroke Variation
            # (0 = Any)
            0,
            # Arm Style
            # (0 = Any)
            0,
            # Letterform
            # (5 = Oblique/Square, 8 = Normal/Square)
            5 if isItalic else 8,
            # Midline
            # (0 = Any)
            0,
            # X-height
            # (3 = Constant/Standard)
            3
        ],
        openTypeOS2WeightClass   = weight,
        openTypeOS2VendorID      = "qwer",

        # Postscript (post)
        postscriptUnderlinePosition  = int(-(DESCENT / 2) * SCALE),
        postscriptUnderlineThickness = int(SCALE),
        postscriptIsFixedPitch       = True,
    )

    combinedFea = ""
    afterLiga = ""

    for file, fea in features.items():
        if fea.startswith("# AFTER_LIGATURES"):
            afterLiga += f"# {file}\n"
            afterLiga += f"{fea}\n"
            continue
        combinedFea += f"# {file}\n"
        combinedFea += f"{fea}\n"

    ligaFea = "# GENERATED/LIGATURES\n"
    ligaFea += "feature liga {\n"
    ligatures.sort(key = lambda liga: len(liga["from"]), reverse = True)
    for ligature in ligatures:
        if ligature["lazy"]:
            ligaFea += f"sub space {" ".join([f"{c}'" for c in ligature["from"]])} space by {ligature["name"]};\n"
        else:
            ligaFea += f"sub {" ".join(ligature["from"])} by {ligature["name"]};\n"
    for ligature in ligatures:
        ligaFea += f"sub {ligature["name"]} by {" ".join(ligature["to"])};\n"
    ligaFea += "} liga;\n"
    combinedFea += ligaFea
    combinedFea += afterLiga

    ufo.features = Features(combinedFea)

    ufoPath = os.path.abspath(f"../build/{getFullNameShort(weight, italicAngle)}.ufo")

    ufo.save(ufoPath, overwrite = True)

    return ufoPath

# Ensure the build directory exists.
if not os.path.exists("../build"):
    os.mkdir("../build")

if not os.path.exists("../build/instances"):
    os.mkdir("../build/instances")

# doc = DesignSpaceDocument()
# doc.addAxisDescriptor(
#     maximum = 950,
#     minimum = 100,
#     default = 400,
#     name    = "weight",
#     tag     = "wght",
# )
# doc.addAxisDescriptor(
#     maximum = 14,
#     minimum = 0,
#     default = 0,
#     name    = "slant",
#     tag     = "slnt",
# )

MASTER_WEIGHTS = [100, 400, 950]

genWeights = WEIGHT_NAMES.keys() if len(sys.argv) < 2 else map(int, sys.argv[1:])

for weight in genWeights:
    regularPath = writeUFO(weight)
    italicPath  = writeUFO(weight, 14)
    #
    # if weight in MASTER_WEIGHTS:
    #     doc.addSourceDescriptor(
    #         path = regularPath,
    #         name = f"master.PixelCode.{getStyleName(weight)}",
    #         familyName = getFamilyName(),
    #         styleName  = getStyleName(weight),
    #         location = dict(weight = weight, slant = 0),
    #         copyLib = True,
    #         copyInfo = True,
    #         copyGroups = True,
    #         copyFeatures = True,
    #     )
    #     doc.addSourceDescriptor(
    #         path = italicPath,
    #         name = f"master.PixelCode.{getStyleName(weight, 14)}",
    #         familyName = getFamilyName(),
    #         styleName  = getStyleName(weight, 14),
    #         location = dict(weight = weight, slant = 14),
    #         copyLib = True,
    #         copyInfo = True,
    #         copyGroups = True,
    #         copyFeatures = True,
    #     )
    #
    # doc.addInstanceDescriptor(
    #     name = f"instance_{getStyleName(weight)}",
    #     familyName = getFamilyName(),
    #     styleName  = getStyleName(weight),
    #     path       = os.path.abspath(f"../build/instances/{getFullNameShort(weight)}.ufo"),
    #     location   = dict(weight = weight, slant = 0),
    #     kerning    = False,
    #     info       = True,
    #     postScriptFontName = getFullNameShort(weight),
    #     styleMapFamilyName = getFamilyName(),
    #     styleMapStyleName  = getStyleName(weight),
    # )
    # doc.addInstanceDescriptor(
    #     name = f"instance_{getStyleName(weight, 14)}",
    #     familyName = getFamilyName(),
    #     styleName  = getStyleName(weight, 14),
    #     path       = os.path.abspath(f"../build/instances/{getFullNameShort(weight, 14)}.ufo"),
    #     location   = dict(weight = weight, slant = 14),
    #     kerning    = False,
    #     info       = True,
    #     postScriptFontName = getFullNameShort(weight, 14),
    #     styleMapFamilyName = getFamilyName(),
    #     styleMapStyleName  = getStyleName(weight, 14),
    # )
#
# doc.addInstanceDescriptor(
#     name = "instance_Italic",
#     familyName = getFamilyName(),
#     styleName  = "Italic",
#     path       = os.path.abspath(f"../build/instances/{getFamilyName().replace(" ", "")}-Italic.ufo"),
#     location   = dict(weight = 400, slant = 14),
#     kerning    = False,
#     info       = True,
#     postScriptFontName = f"{getFamilyName().replace(" ", "")}-Italic",
#     styleMapFamilyName = getFamilyName(),
#     styleMapStyleName  = "Italic",
# )
#
# doc.write("../build/PixelCode.designspace")


