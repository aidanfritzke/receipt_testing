"""Renders the Gregg alphabet to ESC/POS raster blobs -> alphabet_strokes.json.

Run once (needs fonttools + pillow, neither of which the morning script needs):

    py gregg_practice/build_alphabet.py

Each stroke is drawn from Grascii-Regular.otf by glyph name, so no OpenType
shaping engine is involved - the letters you type in Grascii ("K") map to empty
placeholder glyphs, and the real strokes live under lowercase names ("k").
Every glyph is scaled by ONE factor: in Gregg, K and G are the same curve and
differ only in length, so per-glyph normalisation would destroy the alphabet.
"""

import base64
import json
import pathlib

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from PIL import Image, ImageChops, ImageDraw

HERE = pathlib.Path(__file__).parent
FONT_PATH = HERE / "Grascii-Regular.otf"
OUT_PATH = HERE / "alphabet_strokes.json"

LONGEST_STROKE_DOTS = 150   # at 180 dpi this makes the longest stroke ~21 mm
PAD = 4

# letter, glyph name, and how the manual describes the stroke
ALPHABET = [
    ("K",  "k",       "shallow forward curve"),
    ("G",  "g",       "same curve as K, twice as long"),
    ("R",  "r",       "forward curve, deep part at the start"),
    ("L",  "l",       "same curve as R, twice as long"),
    ("N",  "n",       "short forward straight line"),
    ("M",  "m",       "same line as N, longer"),
    ("T",  "t",       "short line struck upward"),
    ("D",  "d",       "same line as T, twice as long"),
    ("P",  "p",       "downward curve"),
    ("B",  "b",       "same curve as P, twice as long"),
    ("F",  "f",       "downward curve, opposite of P"),
    ("V",  "v",       "same curve as F, twice as long"),
    ("CH", "ch",      "upward curve"),
    ("J",  "j",       "same curve as CH, twice as long"),
    ("S",  "s.right", "small downward hook"),
    ("SH", "sh",      "short downward straight line"),
    ("TH", "th.over", "slanted curve over the line"),
    ("NG", "ng",      "straight line below the line of writing"),
    ("NK", "nk",      "same as NG, longer"),
    ("A",  "a",       "large circle"),
    ("E",  "e",       "small circle"),
    ("I",  "i",       "large circle, marked"),
    ("O",  "o",       "small hook, on its side"),
    ("U",  "u",       "small hook, opposite of O"),
]


class ContourPen(BasePen):
    """Collects glyph contours as flattened point lists."""

    def __init__(self, glyph_set):
        super().__init__(glyph_set)
        self.contours, self._points = [], []

    def _moveTo(self, point):
        self.flush()
        self._points = [point]

    def _lineTo(self, point):
        self._points.append(point)

    def _curveToOne(self, control1, control2, point):
        start = self._points[-1]
        for step in range(1, 13):           # flatten the cubic
            t = step / 12
            u = 1 - t
            self._points.append((
                u*u*u*start[0] + 3*u*u*t*control1[0] + 3*u*t*t*control2[0] + t*t*t*point[0],
                u*u*u*start[1] + 3*u*u*t*control1[1] + 3*u*t*t*control2[1] + t*t*t*point[1],
            ))

    def _closePath(self):
        self.flush()

    def flush(self):
        if len(self._points) > 2:
            self.contours.append(self._points)
        self._points = []


def glyph_contours(font, glyph_name):
    glyph_set = font.getGlyphSet()
    pen = ContourPen(glyph_set)
    glyph_set[glyph_name].draw(pen)
    pen.flush()
    if not pen.contours:
        raise SystemExit(f"glyph {glyph_name!r} has no outline")
    return pen.contours


def render(contours, scale):
    """1-bit image of one stroke, even-odd filled so circles stay rings."""
    xs = [x for contour in contours for x, _ in contour]
    ys = [y for contour in contours for _, y in contour]
    left, bottom = min(xs), min(ys)
    width = max(int((max(xs) - left) * scale) + PAD * 2, 8)
    height = max(int((max(ys) - bottom) * scale) + PAD * 2, 8)

    image = Image.new("1", (width, height), 0)
    for contour in contours:
        layer = Image.new("1", (width, height), 0)
        ImageDraw.Draw(layer).polygon(
            [((x - left) * scale + PAD, height - PAD - (y - bottom) * scale)
             for x, y in contour], fill=1)
        # XOR, not OR: an inner contour has to cut a hole, not fill it in
        image = ImageChops.logical_xor(image, layer)
    return image


def escpos_raster(image):
    """GS v 0 - print raster bit image. 1 bit per dot, MSB first, 1 = black."""
    width_bytes = (image.width + 7) // 8
    pixels = image.load()
    data = bytearray()
    for y in range(image.height):
        for byte_index in range(width_bytes):
            byte = 0
            for bit in range(8):
                x = byte_index * 8 + bit
                if x < image.width and pixels[x, y]:
                    byte |= 0x80 >> bit
            data.append(byte)
    header = bytes([0x1D, 0x76, 0x30, 0,
                    width_bytes & 0xFF, width_bytes >> 8,
                    image.height & 0xFF, image.height >> 8])
    return header + bytes(data)


def main():
    font = TTFont(FONT_PATH)
    contours = {letter: glyph_contours(font, name) for letter, name, _ in ALPHABET}
    widest = max(max(x for c in cs for x, _ in c) - min(x for c in cs for x, _ in c)
                 for cs in contours.values())
    scale = LONGEST_STROKE_DOTS / widest

    strokes = []
    for letter, glyph_name, description in ALPHABET:
        image = render(contours[letter], scale)
        strokes.append({
            "letter": letter,
            "glyph": glyph_name,
            "description": description,
            "width": image.width,
            "height": image.height,
            "escpos": base64.b64encode(escpos_raster(image)).decode("ascii"),
        })

    OUT_PATH.write_text(
        json.dumps({"source": "Grascii-Regular.otf", "dots_per_inch": 180,
                    "strokes": strokes}, indent=1) + "\n", encoding="utf-8")
    total = sum(len(s["escpos"]) for s in strokes)
    print(f"wrote {OUT_PATH.name}: {len(strokes)} strokes, "
          f"{total // 1024} KB of base64, scale {scale:.4f}")
    print("  " + ", ".join(f'{s["letter"]}={s["width"]}x{s["height"]}'
                           for s in strokes[:8]))


if __name__ == "__main__":
    main()
