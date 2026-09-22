"""One-off: turn club crest artwork into trimmed, transparent PNGs for the cards.

Not part of the weekly update — run it only when adding or replacing a club.
Needs Pillow:  python3 -m pip install Pillow
Usage:         python3 scripts/prep_crests.py [source-folder]
"""
from PIL import Image
from collections import deque
import os
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Documents/Premier League Crests")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "crests")
MAP = {"Arsenal.png":"arsenal", "Bournemouth.jpg":"bournemouth", "Chelsea.jpeg":"chelsea",
       "Liverpool.jpg":"liverpool", "Manchester United.webp":"manutd"}
SIZE, PAD = 240, 4

# (lightness floor, max saturation) for "this is background".
# Man United's source sits on a grey grid whose lines run down to ~157, so it
# needs a looser floor; the flood fill still protects white inside each crest.
TOL = {"manutd": (138, 22)}
# Crests whose enclosed interior shows the source page through it: repaint those
# pockets solid white rather than leaving the texture behind the artwork.
FLATTEN = {"manutd"}
DEFAULT_TOL = (198, 34)

def is_bg(px, tol):
    r, g, b, a = px
    if a < 24:
        return True
    return min(r, g, b) > tol[0] and (max(r, g, b) - min(r, g, b)) < tol[1]

def process(src, name):
    tol = TOL.get(name, DEFAULT_TOL)
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    px = im.load()

    # Flood fill background from every border pixel, so white *inside* the crest survives.
    seen = bytearray(w * h)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            q.append((x, y))

    while q:
        x, y = q.popleft()
        i = y * w + x
        if seen[i] or not (0 <= x < w and 0 <= y < h):
            continue
        if not is_bg(px[x, y], tol):
            continue
        seen[i] = 1
        px[x, y] = (255, 255, 255, 0)
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
                q.append((nx, ny))

    # De-fringe: pale leftovers touching transparency are anti-aliasing halo.
    edge = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0:
                continue
            if is_bg(px[x, y], tol):
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] == 0:
                        edge.append((x, y)); break
    for x, y in edge:
        px[x, y] = (255, 255, 255, 0)

    if name in FLATTEN:
        for y in range(h):
            for x in range(w):
                if px[x, y][3] and is_bg(px[x, y], tol):
                    px[x, y] = (255, 255, 255, 255)

    im = im.crop(im.getbbox())                      # trim to the crest
    im.thumbnail((SIZE - PAD * 2, SIZE - PAD * 2), Image.LANCZOS)
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.paste(im, ((SIZE - im.width) // 2, (SIZE - im.height) // 2))
    # Palette PNG keeps the set at ~55KB total instead of ~300KB.
    canvas.quantize(colors=128, method=Image.FASTOCTREE).save(
        os.path.join(OUT, name + ".png"), optimize=True)
    return im.size

os.makedirs(OUT, exist_ok=True)
for f, name in MAP.items():
    print("%-12s %s" % (name, process(os.path.join(SRC, f), name)))
