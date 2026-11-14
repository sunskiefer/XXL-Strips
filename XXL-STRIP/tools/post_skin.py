#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Finish the built skin: every baked word in Titillium Web Bold, large (the Meta4MPCXXL text standard).

    python3 tools/post_skin.py "<skin dir>/Plugin Skins" layout.conf

MPC draws live text only in Titillium Web or Roboto; shadow_art bakes static text in a small bitmap font. So this
script draws, into the skin's images:
  - the `#@text tab=<n> cx= cy= size= label="..."` lines of layout.conf (group captions: option rows, meters) into
    that tab's page background (sh_bg_<n>.png). cx/cy are Force Shadow pixels (skin y = cy - 86). No caption is ever
    smaller than MIN_PX.
  - the option captions of every option row (sh_seg_<key>_<n>_<on|off>.png), as large as the box allows.
Adapted from Meta4MPCXXL's tools/post_skin.py. Titillium Web is SIL OFL 1.1 (art/fonts/OFL-*.txt).
"""
import json
import os
import re
import shlex
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SANS = os.path.join(ROOT, "art", "fonts", "TitilliumWeb-Bold.ttf")
INK = (255, 255, 255)
SEG_OFF = (16, 16, 17)
SEG_ON = (255, 255, 255)
SEG_ON_INK = (17, 17, 17)
MIN_PX = 26
SS = 4


def font(px):
    return ImageFont.truetype(SANS, int(px * SS))


def draw_text(im, x, y, size, colour, text):
    f = font(size)
    d0 = ImageDraw.Draw(im)
    w = int(d0.textlength(text, font=f) / SS) + 8
    h = int(size * 1.6) + 8
    layer = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((w * SS // 2, h * SS // 2), text, font=f, fill=colour + (255,), anchor="mm")
    layer = layer.resize((w, h), Image.LANCZOS)
    im.alpha_composite(layer, (int(x - w // 2), int(y - h // 2)))
    return w


def caption(path, text, fill, ink):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    plate = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(plate)
    d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), radius=6 * SS, fill=fill + (255,))
    size = min(h * 0.58, 38)
    while d.textlength(text, font=font(size)) > (w - 12) * SS and size > 12:
        size -= 1
    d.text((w * SS // 2, h * SS // 2), text, font=font(size), fill=ink + (255,), anchor="mm")
    base = Image.new("RGBA", (w, h), im.getpixel((0, 0))[:3] + (255,))
    base.alpha_composite(plate.resize((w, h), Image.LANCZOS))
    base.convert("RGB").save(path)
    return size


def texts(layout):
    out = {}
    for line in open(layout):
        line = line.strip()
        if not line.startswith("#@text "):
            continue
        a = {}
        for tok in shlex.split(line[7:]):
            if "=" in tok:
                k, v = tok.split("=", 1)
                a[k] = v
        out.setdefault(int(a["tab"]), []).append((int(a["cx"]), int(a["cy"]) - 86, float(a.get("size", 30)), a["label"]))
    return out


def main():
    skin, layout = sys.argv[1], sys.argv[2]
    params = {p["key"]: p for p in json.load(open(os.path.join(ROOT, "params.json")))["params"]}
    files = sorted(os.listdir(skin))
    tx = texts(layout)
    small = []
    n_text = 0
    for f in files:
        m = re.fullmatch(r"sh_bg_(\d+)\.png", f)
        if not m:
            continue
        p = os.path.join(skin, f)
        im = Image.open(p).convert("RGBA")
        for (x, y, size, label) in ([] if os.environ.get("XXL_TEXT_PIECES") else tx.get(int(m.group(1)), [])):   # strip_skin.py draws them as separate pieces
            if size < MIN_PX:
                small.append("%s: '%s' at %g px" % (f, label, size))
            draw_text(im, x, y, size, INK, label)
            n_text += 1
        im.convert("RGB").save(p)
    segs = 0
    for f in files:
        m = re.fullmatch(r"sh_seg_(.+)_(\d+)_(on|off)\.png", f)
        if m and m.group(1) in params:
            opts = params[m.group(1)].get("options") or []
            i = int(m.group(2))
            if i < len(opts):
                on = m.group(3) == "on"
                size = caption(os.path.join(skin, f), opts[i].upper(), SEG_ON if on else SEG_OFF, SEG_ON_INK if on else INK)
                if size < MIN_PX:
                    small.append("%s: '%s' at %g px" % (f, opts[i], size))
                segs += 1
    print("post_skin: %d captions on the pages, %d option captions" % (n_text, segs))
    if small:
        sys.exit("post_skin: text below %d px (widen the box or shorten the word):\n  " % MIN_PX + "\n  ".join(small))


if __name__ == "__main__":
    main()
