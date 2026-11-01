#!/usr/bin/env python3
"""Draw og.png — the card WhatsApp shows when the link is pasted in the group.

Also rewrites the og: block in index.html, because the image URL carries the
gameweek: WhatsApp caches a preview per URL, so without that changing nobody
would ever see a new week's table.

Needs Pillow:  python3 -m pip install Pillow
"""
import html
import json
import os
import re
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "standings.json")
PAGE = os.path.join(ROOT, "index.html")
OUT = os.path.join(ROOT, "og.png")
SITE = "https://samstephenfields.github.io/goals-21/"

W, H = 1200, 630
BG, CARD, LINE = "#0a0e14", "#141b26", "#232e3f"
TEXT, DIM, FAINT = "#e8edf5", "#8a97ab", "#5c6878"
ACCENT, GOLD, BUST = "#2fe08a", "#ffc93c", "#ff4d6a"

# Whatever the host has: GitHub runners carry DejaVu, macOS carries Helvetica.
FONTS = [
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ("/System/Library/Fonts/Supplemental/Arial Bold.ttf",
     "/System/Library/Fonts/Supplemental/Arial.ttf"),
    ("/Library/Fonts/Arial Bold.ttf", "/Library/Fonts/Arial.ttf"),
]


def fonts():
    for bold, regular in FONTS:
        if os.path.exists(bold) and os.path.exists(regular):
            return bold, regular
    sys.exit("No usable TrueType font found; tried:\n  " +
             "\n  ".join(b for b, _ in FONTS))


def main():
    d = json.load(open(DATA))
    bold_path, reg_path = fonts()
    B = lambda s: ImageFont.truetype(bold_path, s)
    R = lambda s: ImageFont.truetype(reg_path, s)

    im = Image.new("RGB", (W, H), BG)
    g = ImageDraw.Draw(im)

    g.text((60, 44), "RACE TO 21", font=B(58), fill=TEXT)
    g.text((60, 116), "Premier League %s  ·  Gameweek %d of %d  ·  target %d goals"
           % (d["season"], d["gameweeksPlayed"], d["totalGameweeks"], d["target"]),
           font=R(23), fill=DIM)

    # column headers
    top = 176
    g.text((770, top), "GOALS", font=B(17), fill=FAINT, anchor="ra")
    g.text((1010, top), "ON PACE", font=B(17), fill=FAINT, anchor="ra")

    y = top + 32
    row_h = 50
    for p in d["people"]:
        bust = p["projected"] is not None and p["projected"] > d["target"]
        g.rounded_rectangle([60, y, 1140, y + row_h - 8], 10,
                            fill=CARD, outline=BUST if bust else LINE, width=1)
        mid = y + (row_h - 8) // 2

        g.rounded_rectangle([76, mid - 14, 104, mid + 14], 7,
                            fill=GOLD if p["rank"] == 1 else "#1a2331")
        g.text((90, mid), str(p["rank"]), font=B(16),
               fill="#3d2600" if p["rank"] == 1 else DIM, anchor="mm")

        g.text((126, mid), p["name"], font=B(25), fill=TEXT, anchor="lm")
        g.text((770, mid), str(p["total"]), font=B(28),
               fill=ACCENT if p["total"] else FAINT, anchor="rm")
        g.text((1010, mid), str(p["projected"] if p["projected"] is not None else "–"),
               font=B(26), fill=BUST if bust else DIM, anchor="rm")
        if bust:
            g.text((1124, mid), "BUST", font=B(16), fill=BUST, anchor="rm")
        y += row_h

    g.text((60, H - 44), SITE.replace("https://", ""), font=R(20), fill=FAINT)
    g.text((1140, H - 44), "updates every Sunday evening", font=R(20), fill=FAINT, anchor="ra")
    im.save(OUT, optimize=True)

    # Point the page at this week's image and refresh the summary text.
    lead = sorted(d["people"], key=lambda p: -p["total"])[0]
    desc = ("Gameweek %d — %s leads on %d, on pace for %s. Four players each, target %d."
            % (d["gameweeksPlayed"], lead["name"], lead["total"], lead["projected"], d["target"]))
    block = "\n".join([
        '<!-- og:start --><!-- rewritten by scripts/make_og.py; edit there, not here -->',
        '<meta property="og:title" content="Race to 21">',
        '<meta property="og:description" content="%s">' % html.escape(desc, quote=True),
        '<meta property="og:type" content="website">',
        '<meta property="og:url" content="%s">' % SITE,
        '<meta property="og:image" content="%sog.png?gw=%d">' % (SITE, d["gameweek"]),
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<!-- og:end -->',
    ])
    page = open(PAGE).read()
    new = re.sub(r"<!-- og:start -->.*?<!-- og:end -->", lambda _: block, page, flags=re.S)
    if new == page and block not in page:
        sys.exit("Could not find the og: marker block in index.html")
    open(PAGE, "w").write(new)

    print("Wrote %s (%.0f KB) and refreshed the og: block" % (OUT, os.path.getsize(OUT) / 1024))
    print("  %s" % desc)


if __name__ == "__main__":
    main()
