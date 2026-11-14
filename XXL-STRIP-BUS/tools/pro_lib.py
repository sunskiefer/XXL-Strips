#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Turn the generated skin into the XXL Pro pages (first functional skin: no panel art yet).

    python3 tools/post_skin.py "<skin dir>/Plugin Skins" [--preview build/preview]

gen_vst.py builds a working skin from layout.conf (every page a when=pg_<view>:1 panel; knob and switch names and
values are MPC's own live text at the Meta4MPCXXL sizes). This script, in the built skin:
  - paints the plain background and each page's title;
  - draws the overview (a frame and a name per tile, the two level bars);
  - draws the patch bay: sockets and their names, one transparent cable picture per output / input pair (switched by
    the engine's cable parameters), the ring of the socket that waits for its other end, the dimmed sockets a cable
    cannot go to, and the CONNECTED page;
  - redraws every button (large Titillium captions) and turns the tiles and sockets into touch areas.
Everything injected goes right after the background, so every control stays on top and keeps its touches.
Text rule: nothing this script draws is under MIN_PX (26 px); it stops if something is.
The patch bay drawing and the skin handling are PhyXXL's.
"""
import json
import math
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec  # noqa: E402

W, H = 1280, 628
FONT = os.path.join(ROOT, "art", "fonts", "TitilliumWeb-Bold.ttf")
PANEL = (36, 34, 30)        # the knob render script's own background, so the knobs sit in it
HEADER = (12, 12, 12)
LINE = (108, 106, 102)
INK = (255, 255, 255)
RING = (255, 255, 255)
TAB = "XXL Pro|XXL Pro"
MIN_PX = 26
SS = 3
small = []   # text drawn under MIN_PX


def font(size):
    return ImageFont.truetype(FONT, int(size))


def load_param_keys():
    keys = []
    for line in open(os.path.join(ROOT, "build", "params.h")):
        m = re.match(r'\s*\{"([^"]+)",', line)
        if m:
            keys.append(m.group(1))
    return keys


class Skin:
    def __init__(self, folder):
        self.dir = folder
        self.path = os.path.join(folder, "TUI.json")
        self.tui = json.load(open(self.path))
        self.defs_list = self.tui["pageData"]["componentDefinitions"]["localComponentDefinitions"]
        self.defs = {d["key"]: d["value"] for d in self.defs_list}
        self.page = self.defs[TAB]
        self.keys = load_param_keys()
        self.index = {k: i for i, k in enumerate(self.keys)}
        self.params = {p["key"]: p for p in json.load(open(os.path.join(ROOT, "params.json")))["params"]}

    def param_of(self, inst):
        for m in inst["handle remapping"]["map"]:
            if m["key"] == "Data" and m["value"].startswith("Parameter "):
                return self.keys[int(m["value"].split()[1])]
        return None

    def save(self):
        for d in list(self.defs.values()) + self.page["componentsData"]:
            d.pop("_xk", None)
        with open(self.path, "w") as f:
            json.dump(self.tui, f, separators=(",", ":"))


def bounds(b):
    return [int(round(float(x))) for x in b.split()]


def bstr(x, y, w, h):
    return "%d %d %d %d" % (x, y, w, h)


def image_instance(name, img, x, y, w, h, handles):
    return {"version": 2,
            "componentData": {"version": 1, "name": name, "type": "Image",
                              "data": {"version": 2, "imageType": "Regular", "colour": "0", "image": img}},
            "handle remapping": {"version": 1, "map": []},
            "bounds": {"version": 2, "acceptsHWFocus": "No", "showWhenDataModelInvalid": "Show", "whenVisible": "Always",
                       "boundsType": "Absolute", "bounds": bstr(x, y, w, h),
                       "additionalInvalidatingHandles": handles}}


# ------------------------------------------------------------------------------------------------ drawing
def text_image(s, size, colour=INK):
    """a line of text on a transparent picture, cropped to the text"""
    if size / 0.75 < MIN_PX - 0.01:   # size is in picture px; the rule (26) is in MPC text height, which is size / 0.75
        small.append("'%s' at %g px" % (s, size / 0.75))
    f = font(size * SS)
    w = int(ImageDraw.Draw(Image.new("RGBA", (4, 4))).textlength(s, font=f) / SS) + 6
    h = int(size * 1.4)
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((3 * SS, h * SS // 2), s, font=f, fill=colour + (255,), anchor="lm")
    return im.resize((w, h), Image.LANCZOS)


def push_image(label, on, w, h):
    """a button: a dark rounded cap with a grey line; pressed it lightens"""
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], radius=8 * SS, fill=((96, 94, 90) if on else (16, 16, 17)) + (255,),
                        outline=LINE + (255,), width=2 * SS)
    size = 34 if label in ("<", ">") else 28
    while size > MIN_PX and d.textlength(label, font=font(size * SS)) > (w - 14) * SS:
        size -= 1
    if d.textlength(label, font=font(size * SS)) > (w - 6) * SS:
        small.append("button '%s' does not fit %d px at %d px text" % (label, w, size))
    d.text((w * SS / 2, h * SS / 2), label, font=font(size * SS), fill=INK + (255,), anchor="mm")
    return im.resize((w, h), Image.LANCZOS)


def hit_image(w, h):
    """a touch area that shows nothing: a fully transparent button picture can be ignored by the host's pixel hit
    test, so it carries a 16 % black the eye cannot see on the dark panel (PhyXXL)"""
    return Image.new("RGBA", (w, h), (0, 0, 0, 40))


def highlight(w, h, r=14):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([3, 3, w - 4, h - 4], radius=r, fill=(255, 255, 255, 40))
    return im


def tile_frame(w, h):
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([SS, SS, w * SS - SS - 1, h * SS - SS - 1], radius=12 * SS, fill=(16, 16, 17, 255),
                                         outline=LINE + (255,), width=2 * SS)
    return im.resize((w, h), Image.LANCZOS)


def socket_image(r=spec.JACK_R):
    s = 2 * r + 6
    im = Image.new("RGBA", (s * SS, s * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = s / 2.0
    pts = lambda rad: [((c + rad * math.cos(math.radians(60 * k + 30))) * SS, (c + rad * math.sin(math.radians(60 * k + 30))) * SS)
                       for k in range(6)]
    d.polygon(pts(r), fill=(170, 170, 170))
    d.polygon(pts(r - 3), outline=(60, 60, 60), width=SS)
    rr = r - 6
    d.ellipse([(c - rr) * SS, (c - rr) * SS, (c + rr) * SS, (c + rr) * SS], fill=(130, 130, 130))
    d.ellipse([(c - 6) * SS, (c - 6) * SS, (c + 6) * SS, (c + 6) * SS], fill=(4, 4, 4))
    return im.resize((s, s), Image.LANCZOS)


def ring_img(r=26, w=4):
    S = 4
    im = Image.new("RGBA", (2 * r * S + 8 * S, 2 * r * S + 8 * S), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([4 * S, 4 * S, (2 * r + 4) * S, (2 * r + 4) * S], outline=RING + (255,), width=w * S)
    return im.resize((2 * r + 8, 2 * r + 8), Image.LANCZOS)


def dim_img(r=22):
    S = 4
    im = Image.new("RGBA", (2 * r * S, 2 * r * S), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([0, 0, 2 * r * S - 1, 2 * r * S - 1], fill=PANEL + (205,))
    return im.resize((2 * r, 2 * r), Image.LANCZOS)


VU_N = 32      # needle positions of the VU dial (parameter m_vu)
VU_W, VU_H = 340, 166


VU_ART = (379, 185)                 # the user's VU face (art/user/vu_face_v2.png): no needle, used as it is
VU_PIVOT, VU_TIP, VU_BASE_Y = (190.3, 254.9), 205.0, 184.0   # measured from the art: its arc is r 208.3 about this pivot, -48..+48 degrees


def vu_face(w, h):
    """the user's VU dial art, as given (only scaled to the size asked)"""
    art = Image.open(os.path.join(ROOT, "art", "user", "vu_face_v2.png")).convert("RGBA")
    return art if (w, h) == art.size else art.resize((w, h), Image.LANCZOS)


def vu_needle(i, w, h):
    """needle picture i of VU_N (transparent, the size of the dial): position follows voltage like a real VU,
    -20 VU at -48 degrees, +3 VU at +48 degrees"""
    S = 4
    frac = i / float(VU_N - 1)
    ang = math.radians(-48.0 + 96.0 * frac)
    aw, ah = VU_ART
    im = Image.new("RGBA", (aw * S, ah * S), (0, 0, 0, 0))
    px, py = VU_PIVOT
    tip = (px + VU_TIP * math.sin(ang), py - VU_TIP * math.cos(ang))
    t0 = (py - VU_BASE_Y) / (py - tip[1])
    base = (px + (tip[0] - px) * t0, VU_BASE_Y)
    ImageDraw.Draw(im).line([(base[0] * S, base[1] * S), (tip[0] * S, tip[1] * S)], fill=(222, 236, 250, 255), width=int(2.2 * S))
    return im.resize((w, h), Image.LANCZOS)


def led_ladder(n, count=16, w=640, h=84):
    """the gain reduction lamps (XXL-DISS): `count` lamps, 1 dB each, the first n lit; the dB figures above them"""
    S = 3
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cw = w / float(count)
    f = font(26 * S)
    for i in range(count):
        cx = (i + 0.5) * cw
        if i % 2 == 1 or i == 0:
            d.text((cx * S, 16 * S), str(i + 1), font=f, fill=INK + (255,), anchor="mm")
        lit = i < n
        col = ((255, 120, 40) if i >= 12 else (255, 200, 60)) if lit else (70, 40, 20)
        d.ellipse([(cx - 11) * S, (h - 34) * S, (cx + 11) * S, (h - 12) * S], fill=(8, 8, 9, 255))
        d.ellipse([(cx - 8) * S, (h - 31) * S, (cx + 8) * S, (h - 15) * S], fill=col + (255,))
        if lit:
            d.ellipse([(cx - 4) * S, (h - 28) * S, (cx + 1) * S, (h - 23) * S], fill=(255, 245, 220, 255))
    return im.resize((w, h), Image.LANCZOS)


def led_bar(n, w=176, h=16):
    S = 3
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cw = w / 8.0
    for i in range(8):
        col = (60, 60, 60) if i >= n else ((255, 90, 70) if i == 7 else (240, 240, 240))
        d.rounded_rectangle([(i * cw + 2) * S, 2 * S, ((i + 1) * cw - 2) * S, (h - 2) * S], radius=3 * S, fill=col + (255,))
    return im.resize((w, h), Image.LANCZOS)


def cable_points(p1, p2, n=48, floor=1e9):
    (x1, y1), (x2, y2) = p1, p2
    dist = math.hypot(x2 - x1, y2 - y1)
    sag = 18 + 0.07 * dist
    low = min(max(y1, y2) + sag, floor)
    c1 = (x1 + (x2 - x1) * 0.2, low)
    c2 = (x2 - (x2 - x1) * 0.2, low)
    pts = []
    for i in range(n + 1):
        t = i / float(n)
        a, b, c, e = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        pts.append((a * x1 + b * c1[0] + c * c2[0] + e * x2, a * y1 + b * c1[1] + c * c2[1] + e * y2))
    return pts


def draw_cable(p1, p2, colour, scale=1.0, clip=(0, 0, W, H)):
    """-> (image, x, y) of the cable from p1 to p2 (page coordinates), cropped to what it covers (PhyXXL)"""
    width, outline, plug = 6.0 * scale, 9 * scale, 11 * scale
    pts = cable_points(p1, p2, floor=clip[3] - 2 * outline)
    m = outline + plug + 2
    x0 = max(clip[0], int(math.floor(min(p[0] for p in pts) - m)))
    y0 = max(clip[1], int(math.floor(min(p[1] for p in pts) - m)))
    x1 = min(clip[2], int(math.ceil(max(p[0] for p in pts) + m)))
    y1 = min(clip[3], int(math.ceil(max(p[1] for p in pts) + m)))
    S = 3
    im = Image.new("RGBA", ((x1 - x0) * S, (y1 - y0) * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    sp = [((x - x0) * S, (y - y0) * S) for x, y in pts]
    dark = tuple(int(v * 0.45) for v in colour)
    d.line(sp, fill=dark + (235,), width=max(1, int(outline * S)), joint="curve")
    d.line(sp, fill=colour + (240,), width=max(1, int(width * S)), joint="curve")
    hl = tuple(min(255, int(v * 1.25) + 30) for v in colour)
    d.line([(x, y - width * S * 0.22) for x, y in sp], fill=hl + (150,), width=max(1, int(width * S * 0.25)))
    for (x, y) in (sp[0], sp[-1]):
        r = plug * S
        d.ellipse([x - r, y - r, x + r, y + r], fill=(20, 20, 20, 255))
        d.ellipse([x - r * 0.72, y - r * 0.72, x + r * 0.72, y + r * 0.72], fill=colour + (255,))
    im = im.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    return im, x0, y0


def tile_pieces(im, x0, y0, T):
    a = im.split()[3]
    out = []
    for gy in range((y0 // T) * T, y0 + im.size[1], T):
        for gx in range((x0 // T) * T, x0 + im.size[0], T):
            bx0, by0 = max(gx, x0) - x0, max(gy, y0) - y0
            bx1, by1 = min(gx + T, x0 + im.size[0]) - x0, min(gy + T, y0 + im.size[1]) - y0
            if bx1 <= bx0 or by1 <= by0:
                continue
            bb = a.crop((bx0, by0, bx1, by1)).getbbox()
            if not bb:
                continue
            l, t, r, b = bx0 + bb[0], by0 + bb[1], bx0 + bb[2], by0 + bb[3]
            out.append((im.crop((l, t, r, b)), x0 + l, y0 + t))
    return out


def background():
    im = Image.new("RGB", (W, H), PANEL)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 55], fill=HEADER)
    d.line([0, 56, W, 56], fill=LINE, width=2)
    return im


def connected_panel():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 58, W, 560], fill=PANEL + (255,))
    t = text_image("CONNECTED", 44)
    im.alpha_composite(t, ((W - t.size[0]) // 2, 110))
    x1, x2, y = 300, W - 300, 290
    cab, cx0, cy0 = draw_cable((x1, y), (x2, y), spec.CABLE_COLOURS[2], 2.2, clip=(0, 58, W, 560))
    im.alpha_composite(cab, (cx0, cy0))
    sk = socket_image(40)
    for x, lab in ((x1, "OUTPUT"), (x2, "INPUT")):
        im.alpha_composite(sk, (x - sk.size[0] // 2, y - sk.size[1] // 2))
        t = text_image(lab, 28)
        im.alpha_composite(t, (x - t.size[0] // 2, y + 56))
    return im


# ------------------------------------------------------------------------------------------------ buttons
LABELS = {k: l for k, l, _, _ in spec.NAV}
LABELS.update({spec.BAY_BTN[0]: spec.BAY_BTN[1], spec.BAY_CLEAR[0]: spec.BAY_CLEAR[1], "pk_cancel": "CANCEL",
               "pk_done": "DONE", "pk_unplug": "UNPLUG"})


def rect_for(key):
    def around(x, y, w, h):
        return (int(x - w // 2), int(y - h // 2), int(w), int(h))
    if key in spec.NAV_SIZE:
        x, y = {k: (x, y) for k, _, x, y in spec.NAV}[key]
        return around(x, y, *spec.NAV_SIZE[key])
    for b in (spec.BAY_BTN, spec.BAY_CLEAR):
        if key == b[0]:
            return around(b[2], b[3], b[4], b[5])
    if key == "pk_cancel":
        return around(spec.PK_CANCEL[0], spec.PK_CANCEL[1], 170, 44)
    if key == "pk_done":
        return tuple(spec.PK_DONE)
    if key == "pk_unplug":
        return tuple(spec.PK_UNPLUG)
    if key.startswith("go_") and key[3:] in spec.TILES:
        return tuple(spec.TILES[key[3:]])
    m = re.match(r"tao_(\d+)$", key)
    if m:
        x, y = spec.aud_out_pos(int(m.group(1)))
        return (x + 30 - spec.PICK_AUD[0], y - spec.PICK_AUD[1] // 2, spec.PICK_AUD[0], spec.PICK_AUD[1])   # the name is part of the touch area
    m = re.match(r"tai_(\d+)$", key)
    if m:
        x, y = spec.aud_in_pos(int(m.group(1)))
        return (x - 30, y - spec.PICK_AUD[1] // 2, spec.PICK_AUD[0], spec.PICK_AUD[1])
    return None


def restyle_triggers(skin, folder):
    done = set()
    for inst in list(skin.page["componentsData"]):
        t = inst["componentData"]["type"]
        if not t.startswith("shTrig_"):
            continue
        key = skin.param_of(inst)
        rect = rect_for(key)
        assert rect, key
        inst["bounds"]["bounds"] = bstr(*rect)
        if t in done:
            continue
        done.add(t)
        d = skin.defs[t]
        d["componentsData"] = [s for s in d["componentsData"] if s["componentData"]["type"] != "Label"]
        w, h = rect[2], rect[3]
        for s2 in d["componentsData"]:
            s2["bounds"]["bounds"] = bstr(0, 0, w, h)
        data = next(s for s in d["componentsData"] if s["componentData"]["type"] == "Button")["componentData"]["data"]
        if key in LABELS:
            off, on = push_image(LABELS[key], False, w, h), push_image(LABELS[key], True, w, h)
        elif key.startswith("go_"):
            off, on = hit_image(w, h), highlight(w, h)
        else:   # sockets: nothing at rest, a ring while pressed
            off, on = hit_image(w, h), hit_image(w, h)
            r2 = ring_img(26, 4)
            cx = (w - 30) if key.startswith("tao_") else 30
            on.alpha_composite(r2, (cx - r2.size[0] // 2, (h - r2.size[1]) // 2))
        off.save(os.path.join(folder, data["offImage"]))
        on.save(os.path.join(folder, data["onImage"]))


# ------------------------------------------------------------------------------------------------ previews
class Composer:
    """Draws the page as MPC would for a given state, from the skin itself (previews; live text is drawn from the
    parameter names and a sample value so the sizes can be judged)."""

    def __init__(self, skin):
        self.skin = skin
        self.cache = {}

    def img(self, name):
        if name not in self.cache:
            self.cache[name] = Image.open(os.path.join(self.skin.dir, name)).convert("RGBA")
        return self.cache[name]

    def shown(self, inst, state):
        for h in inst["bounds"]["additionalInvalidatingHandles"]:
            m = re.match(r"IndexedEnabling/(\d+)/(\d+)/Parameter (\d+)", h)
            if m and state.get(self.skin.keys[int(m.group(3))], 0) != int(m.group(1)):
                return False
        return True

    def compose(self, state, texts):
        page = Image.new("RGBA", (W, H), PANEL + (255,))
        dr = ImageDraw.Draw(page)
        for inst in self.skin.page["componentsData"]:
            if not self.shown(inst, state):
                continue
            x, y, w, h = bounds(inst["bounds"]["bounds"])
            t = inst["componentData"]["type"]
            if t == "Image":
                name = inst["componentData"]["data"]["image"]
                if name:
                    im = self.img(name)
                    page.alpha_composite(im.resize((w, h)) if im.size != (w, h) else im, (x, y))
                continue
            d = self.skin.defs.get(t)
            if not d:
                continue
            key = self.skin.param_of(inst)
            p = self.skin.params.get(key, {})
            for sub in d["componentsData"]:
                st = sub["componentData"]["type"]
                sx, sy, sw, sh = bounds(sub["bounds"]["bounds"])
                data = sub["componentData"].get("data", {})
                if st == "Knob" and data.get("filmStrip"):
                    strip = self.img(data["filmStrip"])
                    F = strip.size[0]
                    square = t.startswith("shKnob")
                    nfr = 128 if square else data.get("numFrames", 128)
                    fh = F if square else strip.size[1] // nfr
                    lo, hi = p.get("min", 0), p.get("max", 1)
                    fr = int(round((p.get("default", 0) - lo) / (hi - lo) * (nfr - 1))) if hi > lo else 0
                    page.alpha_composite(strip.crop((0, fr * fh, F, fr * fh + fh)).resize((sw, sh)), (x + sx, y + sy))
                elif st == "Button":
                    if sub["bounds"].get("whenVisible") == "WhenFocussed":
                        continue
                    on = (int(p.get("default", 0)) == data.get("buttonId", 0)) if data.get("numButtonsInGroup", 1) > 1 else \
                        (bool(p.get("default", 0)) and not p.get("momentary"))
                    name = data.get("onImage") if on else data.get("offImage")
                    if name:
                        im = self.img(name)
                        page.alpha_composite(im.resize((sw, sh)) if im.size != (sw, sh) else im, (x + sx, y + sy))
                elif st == "Label":
                    ts = data.get("textStyle", {})
                    px = float(ts.get("font", {}).get("height", 20))
                    if data.get("type") == "Value":
                        s = texts.get(key) or (p["options"][int(p.get("default", 0))] if "options" in p else "%g" % p.get("default", 0))
                    else:
                        s = texts.get(key) or inst["componentData"]["name"] or p.get("name", "")
                    just = ts.get("justification", "")
                    ax = x + sx + (sw // 2 if "Centred" in just.split()[0] else (sw - 4 if "right" in just.lower() else 4))
                    anchor = ("m" if "Centred" in just.split()[0] else ("r" if "right" in just.lower() else "l")) + "m"
                    cc = ts.get("colour", "ffffffff")[-6:]
                    dr.text((ax, y + sy + sh // 2), s.upper(), font=font(px), fill=tuple(int(cc[i:i + 2], 16) for i in (0, 2, 4)) + (255,), anchor=anchor)
        return page


# ------------------------------------------------------------------------------------------------ knobs
DIAL_DROP = 22          # px the name and value move down to clear the dial
DIAL_INK = (232, 232, 228)   # the user's tick ring is black ink; on this dark panel it is recoloured light (colour only)


def align_keys(skin):
    """a key's name sits on the same line as the names of the knobs in its row (the key stands on that line)"""
    rows = {}
    for inst in skin.page["componentsData"]:
        t = inst["componentData"]["type"]
        key = skin.param_of(inst)
        if t.startswith("shKnob") and key in spec.CTRL and "Side" not in t and not spec.CTRL[key].get("side"):
            x, y, w, h = bounds(inst["bounds"]["bounds"])
            ly = min(bounds(s2["bounds"]["bounds"])[1] for s2 in skin.defs[t]["componentsData"] if s2["componentData"]["type"] == "Label")
            rows.setdefault(spec.CTRL[key]["view"], []).append((spec.CTRL[key]["cy"], y + ly))
    for inst in skin.page["componentsData"]:
        t = inst["componentData"]["type"]
        key = skin.param_of(inst)
        if not t.startswith("shToggle") or key not in spec.CTRL or key == "bypass":
            continue
        c = spec.CTRL[key]
        near = sorted(rows.get(c["view"], []), key=lambda r: abs(r[0] - c["cy"]))
        if near and abs(near[0][0] - c["cy"]) <= 60:
            x, y, w, h = bounds(inst["bounds"]["bounds"])
            inst["bounds"]["bounds"] = bstr(x, near[0][1] - (KEY_H - 8), w, h)


def faceplate(rgb):
    """a module's panel in its unit's colour: a soft top-to-bottom shade, fine grain and a dark edge line"""
    import numpy as np
    h = spec.FACE_Y[1] - spec.FACE_Y[0]
    rng = np.random.RandomState(7)
    shade = np.linspace(1.06, 0.92, h)[:, None, None]
    grain = 1.0 + rng.normal(0, 0.012, (h, W, 1))
    a = np.clip(np.asarray(rgb, np.float32)[None, None, :] * shade * grain, 0, 255).astype(np.uint8)
    im = Image.fromarray(a, "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W - 1, h - 1], outline=(0, 0, 0, 255), width=2)
    return im


def ink_controls(skin):
    """on a light faceplate the controls' names and values are printed in dark ink"""
    for inst in skin.page["componentsData"]:
        t = inst["componentData"]["type"]
        key = skin.param_of(inst)
        if key not in spec.CTRL or t.endswith("_ink") or t == "Image":
            continue
        face = spec.FACE.get(spec.CTRL[key]["view"])
        if not face or face[1] != spec._DARK:
            continue
        dk = t + "_ink"
        if dk not in skin.defs:
            d = json.loads(json.dumps(skin.defs[t]))
            for sub in d["componentsData"]:
                if sub["componentData"]["type"] == "Label":
                    sub["componentData"]["data"]["textStyle"]["colour"] = "ff%02x%02x%02x" % face[1]
            skin.defs_list.append({"key": dk, "value": d})
            skin.defs[dk] = d
        inst["componentData"]["type"] = dk


def dial_image(tile, ink=None):
    """the user's tick ring (art/user/tick_ring_4x.png, 163 x 151 around an 86 px knob) at this knob's scale"""
    src = Image.open(os.path.join(ROOT, "art", "user", "tick_ring_4x.png")).convert("RGBA")
    k = tile / 100.0
    im = src.resize((int(round(163 * k)), int(round(151 * k))), Image.LANCZOS)
    out = Image.new("RGBA", im.size, tuple(ink or DIAL_INK) + (0,))
    out.putalpha(im.split()[3])
    return out


KEY_W, KEY_H = 120, 157          # the key's picture on screen (the key itself is 95 x 130, the rest is its shadow)
KEY_CAPS = ("BLACK", "GREY", "RED", "GREEN", "BLUE", "BROWN")


def key_image(col, on, w=KEY_W, h=KEY_H):
    """An ON/OFF key: the DIN key (keycap with its lamp), rendered by tools/key_render.py with the knob script's light;
    lamp dim when off, lit when on; transparent background."""
    import key_render
    col = col if col in KEY_CAPS else "BLACK"
    return key_render.key_big(key_render.COL[col], bool(on)).resize((int(w), int(h)), Image.LANCZOS)


def key_files(folder, col, w=KEY_W, h=KEY_H):
    names = []
    for on in (True, False):
        name = "xk_%s_%dx%d_%s.png" % (col, w, h, "on" if on else "off")
        if not os.path.isfile(os.path.join(folder, name)):
            key_image(col, on, w, h).save(os.path.join(folder, name), optimize=True)
        names.append(name)
    return names   # on, off


def restyle_toggles(skin, folder):
    """every ON/OFF control becomes a DIN key with its lamp, the name under it; the key sits where the control's centre was"""
    on, off = key_files(folder, "BLACK")
    for key, d in skin.defs.items():
        if not key.startswith("shToggle") or d.get("_xk"):
            continue
        cw = max(bounds(s2["bounds"]["bounds"])[2] for s2 in d["componentsData"])
        nh = 48
        for s2 in d["componentsData"]:
            st = s2["componentData"]["type"]
            if st == "Button" and s2["bounds"].get("whenVisible") != "WhenFocussed":
                s2["bounds"]["bounds"] = bstr((cw - KEY_W) // 2, 0, KEY_W, KEY_H)
                s2["componentData"]["data"]["onImage"], s2["componentData"]["data"]["offImage"] = on, off
            elif st == "Label":
                nh = bounds(s2["bounds"]["bounds"])[3]
                s2["bounds"]["bounds"] = bstr(0, KEY_H - 8, cw, nh)
            else:
                s2["bounds"]["bounds"] = bstr(0, 0, cw, KEY_H - 8 + nh)
        d["_xk"] = KEY_H - 8 + nh
    for inst in skin.page["componentsData"]:
        t = inst["componentData"]["type"]
        if t.startswith("shToggle") and skin.defs[t].get("_xk") and not inst.get("_xk"):
            x, y, w, h = bounds(inst["bounds"]["bounds"])
            inst["bounds"]["bounds"] = bstr(x, y + h / 2.0 - KEY_H / 2.0, w, skin.defs[t]["_xk"])
            inst["_xk"] = 1
    for name in ("sh_pill_on.png", "sh_pill_off.png"):
        if os.path.isfile(os.path.join(folder, name)):
            os.remove(os.path.join(folder, name))


_KNOB_FRAMES = {}


KNOB_BG = (36, 34, 30)   # the render script's own panel colour (taken out again to make the knob transparent)
_SIX = ("RED", "GREEN", "BLUE", "BROWN", "BLACK", "GREY")
KNOB_STYLES = list(_SIX) + ["WHITE " + c for c in _SIX] + ["FLAT " + c for c in _SIX]   # black skirt, white skirt, the flat art


def knob_frames(style):
    """128 RGBA frames (400 px for the rendered knobs) of a knob style, transparent background.
    'RED' .. 'GREY': tools/knob_render.py's frames with their alpha; 'WHITE RED' ..: the same with the white skirt;
    'FLAT RED' ..: the user's flat knob art turned."""
    import numpy as np
    if style not in _KNOB_FRAMES:
        if style.startswith("FLAT "):
            art = Image.open(os.path.join(ROOT, "art", "user", "knob_flat_%s.png" % style[5:].lower())).convert("RGBA")
            tile = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
            tile.alpha_composite(art, (28, 28))   # 344 px knob in the 400 px tile: the same size as the rendered knob
            _KNOB_FRAMES[style] = [tile.rotate(-(-135.0 + 270.0 * i / 127.0), resample=Image.BICUBIC) for i in range(128)]
        else:
            rgb = np.load(os.path.join(ROOT, "build", "knobs", style.replace(" ", "_") + ".npy")).astype(np.float32) / 255.0
            a = np.load(os.path.join(ROOT, "build", "knobs", "ALPHA.npy"))[..., None]
            pre = np.clip(rgb - np.asarray(KNOB_BG, np.float32)[None, None, None, :] / 255.0 * (1.0 - a), 0, 1)
            out = np.concatenate([np.clip(pre / np.maximum(a, 1e-3), 0, 1), a], axis=3)
            _KNOB_FRAMES[style] = [Image.fromarray((f * 255 + 0.5).astype(np.uint8), "RGBA") for f in out]
    return _KNOB_FRAMES[style]


def knob_strip(folder, col, size):
    """the filmstrip of a knob style at a size (px), made once: 128 frames, transparent background"""
    size = int(max(40, min(126, size)))   # 128 frames: MPC garbles strips taller than 16384 px
    col = col if col in KNOB_STYLES else "GREY"
    name = "xk_%s_%d.png" % (col.replace(" ", "_"), size)
    if not os.path.isfile(os.path.join(folder, name)):
        fr = knob_frames(col)
        strip = Image.new("RGBA", (size, size * len(fr)), (0, 0, 0, 0))
        for i in range(len(fr)):
            strip.paste(fr[i].resize((size, size), Image.LANCZOS), (0, i * size))
        strip.save(os.path.join(folder, name), optimize=True)
    return name


CAP_X = {"RED": 131, "GREEN": 390, "BLUE": 649, "BROWN": 908, "BLACK": 1167, "GREY": 1426}   # cap centres in the user's sheet
_CAPS = {}


def slider_cap(col):
    """a slider cap cut out of the user's sheet (art/user/slider_caps_sheet.png: six 202 x 120 caps), with a
    transparent background: the cap itself as given, its soft shadow kept as transparent black"""
    import numpy as np
    col = col if col in CAP_X else "GREY"
    if col not in _CAPS:
        sheet = np.asarray(Image.open(os.path.join(ROOT, "art", "user", "slider_caps_sheet.png")).convert("RGB")).astype(np.float32)
        x0, y0, w, h = CAP_X[col] - 125, 50, 250, 170
        px = sheet[y0:y0 + h, x0:x0 + w]
        mask = Image.new("L", (w * 4, h * 4), 0)
        ImageDraw.Draw(mask).rounded_rectangle([24 * 4, 20 * 4, 226 * 4 - 1, 140 * 4 - 1], radius=13 * 4, fill=255)   # the cap: 202 x 120
        inside = np.asarray(mask.resize((w, h), Image.LANCZOS)).astype(np.float32) / 255.0
        bg = np.asarray(KNOB_BG, np.float32)
        shadow = np.clip(1.0 - px.mean(axis=2) / bg.mean(), 0, 1) * (1.0 - inside)   # darker than the panel = shadow
        rgba = np.zeros((h, w, 4), np.float32)
        rgba[..., :3] = px * inside[..., None]
        rgba[..., 3] = (inside + shadow) * 255.0
        _CAPS[col] = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA")
    return _CAPS[col]


def fader_strip(folder, col, w, h, frames):
    """a fader's filmstrip: a slot with the user's slider cap riding it, `frames` pictures of w x h, transparent"""
    name = "xf_%s_%dx%d_f%d.png" % (col, w, h, frames)
    if not os.path.isfile(os.path.join(folder, name)):
        k = w / 202.0                                    # the cap fills the fader's width
        cw, chh = int(round(250 * k)), int(round(170 * k))
        cap = slider_cap(col).resize((cw, chh), Image.LANCZOS)
        cap_h = 120 * k
        strip = Image.new("RGBA", (w, h * frames), (0, 0, 0, 0))
        for i in range(frames):
            fr = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            d = ImageDraw.Draw(fr)
            d.rounded_rectangle([w // 2 - 5, 4, w // 2 + 4, h - 5], radius=4, fill=(8, 8, 9, 255), outline=LINE + (255,))
            y = (h - cap_h) * (1.0 - i / float(frames - 1))   # frame 0 = lowest value = cap at the bottom
            fr.alpha_composite(cap, (int(round((w - cw) / 2.0)), int(round(y - 20 * k))))
            strip.paste(fr, (0, i * h))
        strip.save(os.path.join(folder, name), optimize=True)
    return name


def recolour_faders(skin, folder):
    for inst in skin.page["componentsData"]:
        t = inst["componentData"]["type"]
        key = skin.param_of(inst)
        if not t.startswith("shSlider_v") or key not in spec.CTRL or t.endswith(tuple("_" + c for c in CAP_X)):
            continue
        col = spec.CTRL[key]["colour"]
        dk = t + "_" + col
        if dk not in skin.defs:
            d = json.loads(json.dumps(skin.defs[t]))
            for sub in d["componentsData"]:
                if sub["componentData"]["type"] == "Knob":
                    _, _, w, h = bounds(sub["bounds"]["bounds"])
                    sub["componentData"]["data"]["filmStrip"] = fader_strip(folder, col, w, h, sub["componentData"]["data"]["numFrames"])
            skin.defs_list.append({"key": dk, "value": d})
            skin.defs[dk] = d
        inst["componentData"]["type"] = dk
    for name in os.listdir(folder):
        if name.startswith("sh_slider_v_"):
            os.remove(os.path.join(folder, name))


def recolour_knobs(skin, folder):
    """every knob gets the rendered filmstrip of its colour (tools/render_knobs.py -> build/knobs/<COLOUR>.npy,
    frames made by tools/knob_render.py as it is), scaled to the knob's size; 128 frames, turning in place"""
    done = {}
    for inst in skin.page["componentsData"]:
        t = inst["componentData"]["type"]
        key = skin.param_of(inst)
        if not t.startswith("shKnob") or key not in spec.CTRL:
            continue
        col = spec.CTRL[key]["colour"]
        dk = t + "_" + col
        if t.endswith(tuple("_" + c.replace(" ", "_") for c in KNOB_STYLES)) or t.startswith("xpL_"):
            continue   # already done (a page handled earlier)
        dk = dk.replace(" ", "_")
        if dk not in skin.defs:
            d = json.loads(json.dumps(skin.defs[t]))
            for sub in d["componentsData"]:
                if sub["componentData"]["type"] != "Knob":
                    continue
                sub["componentData"]["data"]["filmStrip"] = knob_strip(folder, col, bounds(sub["bounds"]["bounds"])[2])
            if "Side" not in t:   # name and value sit under the dial, not under the knob picture
                for sub in d["componentsData"]:
                    x, y, w, h = bounds(sub["bounds"]["bounds"])
                    if sub["componentData"]["type"] == "Label":
                        sub["bounds"]["bounds"] = bstr(x, y + DIAL_DROP, w, h)
                    elif sub["componentData"]["type"] == "Focus":
                        sub["bounds"]["bounds"] = bstr(x, y, w, h + DIAL_DROP)
            skin.defs_list.append({"key": dk, "value": d})
            skin.defs[dk] = d
        inst["componentData"]["type"] = dk
        if "Side" not in t:
            x, y, w, h = bounds(inst["bounds"]["bounds"])
            inst["bounds"]["bounds"] = bstr(x, y, w, h + DIAL_DROP)
    for name in os.listdir(folder):
        if name.startswith("sh_knob_r"):
            os.remove(os.path.join(folder, name))


# ------------------------------------------------------------------------------------------------ Panel Editor
# Every movable part has an id: "<parameter key>:<part>" for controls (body / name / value / bg / t0) and "txt<n>:t" /
# "img<n>:bg" for the drawn texts and pictures. tools/make_editor.py turns build/editor_data.json into the editor page;
# its exported layout (layout.json next to build.sh) is applied here. Sockets and cables are not movable yet.
CSS = 0.75   # MPC font "height" x 0.75 = the same text in CSS px (the editor's "build size" is the MPC height)
WEIGHT = {"Regular": 400, "SemiBold": 600, "Bold": 700}
MIN_BUILD = {"name": 35.7, "value": 37.4, "text": 26.0}
SAMPLE = {"touch_info": "PEAK RED  30.0", "mod_info": "IN PATH   GAIN RED 3.2 dB", "cpu_info": "LOAD 12%  COST 9",
          "patch_info": "Tap a socket, then the other end of the cable."}


def views_of(skin, inst):
    mods = [m[0] for m in spec.MODULES]
    for h in inst["bounds"]["additionalInvalidatingHandles"]:
        m = re.match(r"IndexedEnabling/(\d+)/(\d+)/Parameter (\d+)", h)
        if not m:
            continue
        k = skin.keys[int(m.group(3))]
        if k.startswith("pg_"):
            return [k[3:]]
        if k == "in_sec":
            return mods + ["bay"]
        if k in ("in_mod", "hdr_ti"):
            return mods
        if k in ("in_bay", "pk_ta", "pk_c", "pk"):
            return ["bay"]
    return []


def control_parts(skin, inst):
    """the movable parts of a control instance: [(pid, role, sub component, kind 'img'/'txt')]"""
    out = []
    t = inst["componentData"]["type"]
    for sub in skin.defs[t]["componentsData"]:
        st = sub["componentData"]["type"]
        data = sub["componentData"].get("data", {})
        if st == "Knob":
            out.append(("body", "body", sub, "img"))
        elif st == "Button" and sub["bounds"].get("whenVisible") != "WhenFocussed":
            out.append(("bg", "bg", sub, "img"))
        elif st == "Label":
            if t.startswith("shReadout"):
                out.append(("t0", "text", sub, "txt"))
            elif data.get("type") == "Value":
                out.append(("value", "value", sub, "txt"))
            else:
                out.append(("name", "name", sub, "txt"))
    return out


def editor_model(skin, comps, art_items):
    imgs, views = {}, {v[0]: [] for v in spec.VIEWS}

    def uri(name, crop=None, frames=None):
        key = name + (":%d" % crop if crop is not None else "")
        if key not in imgs:
            import base64, io
            im = Image.open(os.path.join(skin.dir, name)).convert("RGBA")
            if crop is not None and frames:
                fh = im.size[1] // frames
                i = min(crop, frames - 1)
                im = im.crop((0, i * fh, im.size[0], i * fh + fh))
            b = io.BytesIO()
            im.save(b, "PNG")
            imgs[key] = "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
        return key

    for inst in comps:
        t = inst["componentData"]["type"]
        key = skin.param_of(inst)
        if t == "Image" or not key or key.startswith(("tao_", "tai_")):
            continue
        x, y, w, h = bounds(inst["bounds"]["bounds"])
        p = skin.params.get(key, {})
        parts = []
        for pid, role, sub, kind in control_parts(skin, inst):
            sx, sy, sw, sh = bounds(sub["bounds"]["bounds"])
            data = sub["componentData"].get("data", {})
            if kind == "img":
                if role == "body":
                    square = t.startswith("shKnob")
                    nfr = 128 if square else data["numFrames"]
                    src = uri(data["filmStrip"], nfr // 2, nfr)
                else:
                    src = uri(data["offImage"])
                part = {"id": pid, "k": "img", "role": role, "src": src, "x": sx, "y": sy, "w": sw, "h": sh}
                if role == "body" and t.startswith("shToggle"):   # the three key caps
                    part["alts"] = {c: uri(key_files(skin.dir, c)[1]) for c in KEY_CAPS}
                if role == "body" and t.startswith("shSlider_v") and key in spec.CTRL:   # the six cap colours of this fader
                    part["alts"] = {c: uri(fader_strip(skin.dir, c, sw, sh, data["numFrames"]), data["numFrames"] // 2, data["numFrames"]) for c in CAP_X}
                parts.append(part)
            else:
                ts = data.get("textStyle", {})
                txt = (inst["componentData"]["name"] or p.get("name", "")).upper() if role == "name" else \
                    (SAMPLE.get(key) or ("NOT PATCHED" if key.startswith("ts_") else "0.0"))
                parts.append({"id": pid, "k": "txt", "role": role, "t": txt, "x": sx, "y": sy, "w": sw, "h": sh,
                              "size": round(float(ts.get("font", {}).get("height", 30)) * CSS, 2),
                              "wt": WEIGHT.get(ts.get("font", {}).get("style", "SemiBold"), 600), "c": "#" + ts.get("colour", "ffffffff")[2:]})
        kind = "knob" if t.startswith("shKnob") else ("fader" if t.startswith("shSlider_v") else "x") if t.startswith(("shKnob", "shSlider_v")) else ("toggle" if t.startswith("shToggle") else ("readout" if t.startswith("shReadout") else "tile"))
        c = {"id": key, "name": (LABELS.get(key) or p.get("name", key)).upper(), "kind": kind, "x": x, "y": y, "w": w, "h": h, "parts": parts}
        for v in views_of(skin, inst):
            views[v].append(c)
    for it in art_items:
        x, y, w, h = bounds(it["inst"]["bounds"]["bounds"])
        if it["kind"] == "txt":
            part = {"id": "t", "k": "txt", "role": "text", "t": it["text"], "x": 0, "y": 0, "w": w, "h": h, "size": it["size"], "wt": 700, "c": it["colour"]}
        else:
            part = {"id": "bg", "k": "img", "role": "bg", "src": uri(it.get("editor_src") or it["inst"]["componentData"]["data"]["image"]), "x": 0, "y": 0, "w": w, "h": h}
        c = {"id": it["id"], "name": it.get("text", "picture"), "kind": "art", "x": x, "y": y, "w": w, "h": h, "parts": [part]}
        for v in views_of(skin, it["inst"]):
            views[v].append(c)
    import base64, io
    import numpy as np
    knobs = {}
    for col in KNOB_STYLES:   # the knob styles, to swap in the editor
        b = io.BytesIO()
        knob_frames(col)[63].resize((126, 126), Image.LANCZOS).save(b, "PNG")
        knobs[col] = "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
    return {"knobs": knobs, "knob_colour": {c["key"]: c["colour"] for c in spec.CONTROLS if c["kind"] == "knob"},
            "names": [v[2] or "Overview" for v in spec.VIEWS], "views": [views[v[0]] for v in spec.VIEWS], "imgs": imgs,
            "faces": {str(i): "data:image/png;base64," + base64.b64encode(open(os.path.join(skin.dir, "xp_face_%s.png" % spec.FACE[v[0]][2]), "rb").read()).decode()
                      for i, v in enumerate(spec.VIEWS) if v[0] in getattr(spec, "FACE", {})},
            "face_y": list(getattr(spec, "FACE_Y", (0, 0))),
            "bg": "data:image/png;base64," + base64.b64encode(open(os.path.join(skin.dir, "sh_bg_0.png"), "rb").read()).decode()}


def apply_layout(skin, folder, comps, art_items, layout):
    over = {o["id"]: o for o in layout.get("parts", [])}
    if not over:
        return 0
    moved = 0
    for it in art_items:   # drawn texts and pictures
        o = over.get(it["id"] + (":t" if it["kind"] == "txt" else ":bg"))
        if not o:
            continue
        inst = it["inst"]
        if it["kind"] == "txt":
            build = max(MIN_BUILD["text"], float(o.get("size", it["size"] / CSS)))
            text, col = str(o.get("text", it["text"])), str(o.get("colour", it["colour"]))
            if text != it["text"] or abs(build * CSS - it["size"]) > 0.3 or col != it["colour"]:
                im = text_image(text, build * CSS, tuple(int(col[i:i + 2], 16) for i in (1, 3, 5)))
                name = "xpl_%s.png" % it["id"]
                im.save(os.path.join(folder, name), optimize=True)
                inst["componentData"]["data"]["image"] = name
                inst["bounds"]["bounds"] = bstr(o["x"], o["y"] + (o["h"] - im.size[1]) / 2, im.size[0], im.size[1])
            else:
                x, y, w, h = bounds(inst["bounds"]["bounds"])
                inst["bounds"]["bounds"] = bstr(o["x"], o["y"], w, h)
        else:
            inst["bounds"]["bounds"] = bstr(o["x"], o["y"], o["w"], o["h"])
        moved += 1
    for inst in comps:     # controls: each gets its own copy of its definition, with its parts where the layout puts them
        t = inst["componentData"]["type"]
        key = skin.param_of(inst)
        if t == "Image" or not key or key.startswith(("tao_", "tai_")):
            continue
        parts = control_parts(skin, inst)
        if not any((key + ":" + pid) in over for pid, _, _, _ in parts):
            continue
        x, y, w, h = bounds(inst["bounds"]["bounds"])
        rects = {}
        for pid, role, sub, kind in parts:
            sx, sy, sw, sh = bounds(sub["bounds"]["bounds"])
            o = over.get(key + ":" + pid)
            rects[pid] = (o["x"], o["y"], o["w"], o["h"]) if o else (x + sx, y + sy, sw, sh)
            moved += 1 if o else 0
        x0, y0 = min(r[0] for r in rects.values()), min(r[1] for r in rects.values())
        x1, y1 = max(r[0] + r[2] for r in rects.values()), max(r[1] + r[3] for r in rects.values())
        d = json.loads(json.dumps(skin.defs[t]))
        dk = "xpL_" + key
        for sub in d["componentsData"]:
            st = sub["componentData"]["type"]
            if st == "Focus" or (st == "Button" and sub["bounds"].get("whenVisible") == "WhenFocussed"):
                sub["bounds"]["bounds"] = bstr(0, 0, x1 - x0, y1 - y0)
        for (pid, role, _, kind), sub in zip(parts, [s2 for s2 in d["componentsData"] if any(s2["componentData"] == q[2]["componentData"] for q in parts)]):
            r = rects[pid]
            sub["bounds"]["bounds"] = bstr(r[0] - x0, r[1] - y0, r[2], r[3])
            o = over.get(key + ":" + pid)
            if kind == "txt" and o:
                ts = sub["componentData"]["data"]["textStyle"]
                ts["font"]["height"] = max(MIN_BUILD[role], float(o.get("size", ts["font"]["height"])))
                ts["font"]["style"] = {400: "Regular", 500: "Regular", 600: "SemiBold", 700: "Bold"}.get(int(o.get("weight", 600)), "SemiBold")
                if re.fullmatch(r"#[0-9a-fA-F]{6}", str(o.get("colour", ""))):
                    ts["colour"] = "ff" + o["colour"][1:]
                if role == "name" and o.get("text"):
                    inst["componentData"]["name"] = str(o["text"])
            if kind == "img" and o and role == "body" and key in spec.CTRL and t.startswith("shKnob"):   # a knob at a new size: its own sharp filmstrip
                side = int(max(40, min(126, r[2])))
                sub["bounds"]["bounds"] = bstr(r[0] - x0, r[1] - y0, side, side)
                sub["componentData"]["data"]["filmStrip"] = knob_strip(folder, str(o.get("knob", spec.CTRL[key]["colour"])).upper(), side)
            if kind == "img" and o and role == "body" and key in spec.CTRL and t.startswith("shSlider_v"):   # a fader: its strip at this size and cap colour
                fw, fh = int(max(40, r[2])), int(max(60, min(400, r[3])))
                nfr = min(128, 12288 // fh)
                sub["bounds"]["bounds"] = bstr(r[0] - x0, r[1] - y0, fw, fh)
                col = str(o.get("knob", spec.CTRL[key]["colour"])).upper().replace("WHITE ", "").replace("FLAT ", "")
                sub["componentData"]["data"].update(filmStrip=fader_strip(folder, col, fw, fh, nfr), numFrames=nfr)
            if kind == "img" and o and role == "body" and t.startswith("shToggle"):   # a key at a new size or cap colour
                col = str(o.get("knob", "BLACK")).upper().replace("WHITE ", "").replace("FLAT ", "")
                data = sub["componentData"]["data"]
                data["onImage"], data["offImage"] = key_files(folder, col if col in KEY_CAPS else "BLACK", int(max(40, r[2])), int(max(40, r[3])))
            if kind == "img" and o and t.startswith("shTrig_"):   # a button at a new size: its pictures are redrawn
                w2, h2 = int(r[2]), int(r[3])
                data = sub["componentData"]["data"]
                if key in LABELS:
                    off, on = push_image(LABELS[key], False, w2, h2), push_image(LABELS[key], True, w2, h2)
                else:
                    off, on = hit_image(w2, h2), highlight(w2, h2)
                data["offImage"], data["onImage"] = "xpl_%s_off.png" % key, "xpl_%s_on.png" % key
                off.save(os.path.join(folder, data["offImage"]))
                on.save(os.path.join(folder, data["onImage"]))
        skin.defs_list.append({"key": dk, "value": d})
        skin.defs[dk] = d
        inst["componentData"]["type"] = dk
        inst["bounds"]["bounds"] = bstr(x0, y0, x1 - x0, y1 - y0)
    return moved


# ================================================================================================ main
def main():
    folder = sys.argv[1]
    preview = sys.argv[sys.argv.index("--preview") + 1] if "--preview" in sys.argv else None
    skin = Skin(folder)
    comps = skin.page["componentsData"]
    idx = skin.index

    def pg(vkey):
        return "IndexedEnabling/1/2/Parameter %d" % idx["pg_" + vkey]

    # 1) the framework's mode backgrounds go; a plain panel is the base
    comps[:] = [c for c in comps if not (c["componentData"]["type"] == "Image" and
                                         c["componentData"]["data"].get("image", "").startswith("sh_mode_"))]
    for name in os.listdir(folder):
        if name.startswith("sh_mode_"):
            os.remove(os.path.join(folder, name))
    background().save(os.path.join(folder, "sh_bg_0.png"))
    restyle_triggers(skin, folder)
    recolour_knobs(skin, folder)
    recolour_faders(skin, folder)
    restyle_toggles(skin, folder)
    align_keys(skin)
    ink_controls(skin)
    for inst in comps:   # BYPASS sits in the 80 px bottom strip: a small key with its name beside it
        if skin.param_of(inst) == "bypass" and inst["componentData"]["type"].startswith("shToggle"):
            d = json.loads(json.dumps(skin.defs[inst["componentData"]["type"]]))
            d.pop("_xk", None)
            kw, kh, cw = 58, 76, 230
            on, off = key_files(folder, "BLACK", kw, kh)
            for s2 in d["componentsData"]:
                st = s2["componentData"]["type"]
                if st == "Button" and s2["bounds"].get("whenVisible") != "WhenFocussed":
                    s2["bounds"]["bounds"] = bstr(cw - kw, 0, kw, kh)
                    s2["componentData"]["data"]["onImage"], s2["componentData"]["data"]["offImage"] = on, off
                elif st == "Label":
                    s2["bounds"]["bounds"] = bstr(0, (kh - 48) // 2, cw - kw - 6, 48)
                else:
                    s2["bounds"]["bounds"] = bstr(0, 0, cw, kh)
            skin.defs_list.append({"key": "xpBypass", "value": d})
            skin.defs["xpBypass"] = d
            inst["componentData"]["type"] = "xpBypass"
            inst["bounds"]["bounds"] = bstr(W - cw - 10, H - kh - 1, cw, kh)
    for key, d in skin.defs.items():   # readout text in the panel's white ink (the framework's default is the line grey)
        if key.startswith("shReadout"):
            for sub in d["componentsData"]:
                if sub["componentData"]["type"] == "Label":
                    sub["componentData"]["data"]["textStyle"]["colour"] = "ffffffff"

    injected = []
    n_img = [0]

    art_items = []   # what the Panel Editor can move: {id, inst, kind, text, size}

    def put(im, x, y, handles, name="Art", fname=None, edit=None):
        if fname is None:
            fname = "xp_%d.png" % n_img[0]
            n_img[0] += 1
            im.save(os.path.join(folder, fname), optimize=True)
        injected.append(image_instance(name, fname, int(x), int(y), im.size[0], im.size[1], handles))
        if edit is not None or name in ("Tile", "Group", "Dial"):
            it = {"id": "%s%d" % ("txt" if edit else "img", len(art_items)), "inst": injected[-1], "kind": "txt" if edit else "img"}
            it.update(edit or {})
            art_items.append(it)

    def put_text(s, size, x, y, handles, align="l", fixed=False):
        im = text_image(s, size)
        x0 = x if align == "l" else (x - im.size[0] if align == "r" else x - im.size[0] // 2)
        put(im, x0, y - im.size[1] // 2, handles, "Text", edit=None if fixed else {"text": s, "size": size, "colour": "#ffffff"})

    # 1b) the Panel Editor's page pictures and text labels (layout.json)
    for vkey, fname in spec.PAGE_ART.items():
        src = os.path.join(ROOT, "art", "panels", fname)
        if vkey in spec.VIEW_KEYS and os.path.isfile(src):
            art = Image.open(src).convert("RGBA").resize((W, H - 58), Image.LANCZOS)
            put(art, 0, 58, [pg(vkey)], "Panel")
    for lb in spec.EXTRA_LABELS:
        if lb.get("view") in spec.VIEW_KEYS and lb.get("text"):
            put_text(str(lb["text"]), max(MIN_PX, float(lb.get("size", 30))), int(lb["x"]), int(lb["y"]), [pg(lb["view"])])

    # 1b2) the faceplates
    for vkey, (rgb, ink, fname) in spec.FACE.items():
        fn = "xp_face_%s.png" % fname
        im = faceplate(rgb)
        if not os.path.isfile(os.path.join(folder, fn)):
            im.save(os.path.join(folder, fn), optimize=True)
        put(im, 0, spec.FACE_Y[0], [pg(vkey)], "Panel", fn)

    # 1c) the dial (tick ring) around every knob
    dials = {}
    for c in spec.CONTROLS:
        if c["kind"] != "knob" or c.get("side") or c.get("widget") == "fader" or c["view"] not in spec.MODULE_COLS:
            continue
        tile = c.get("tile", 126)
        dark = spec.FACE.get(c["view"], (0, 0))[1] == spec._DARK
        dn = "xp_dial_%d%s.png" % (tile, "_k" if dark else "")
        if dn not in dials:
            dials[dn] = dial_image(tile, spec._DARK if dark else None)
            dials[dn].save(os.path.join(folder, dn), optimize=True)
        k = tile / 100.0
        put(dials[dn], c["cx"] - 81 * k, c["cy"] - 80.8 * k, [pg(c["view"])], "Dial", dn)

    # 2) titles
    for v in spec.VIEWS:
        if v[0] == "overview":
            put_text("XXL Pro", 36, 24, 28, [pg(v[0])])
            put_text("PROCESS", 28, 180, 30, [pg(v[0])])
        else:
            put_text(v[1], 30, spec.TITLE_X if v[0] != "bay" else 310, 28, [pg(v[0])])

    # 3) the overview: tile frames, names, level bars
    x, y, tw, th = spec.TILES[spec.TILE_VIEWS[0]]
    frame = tile_frame(tw, th)
    frame.save(os.path.join(folder, "xp_tile.png"), optimize=True)
    names = {m[0]: m[1] for m in spec.MODULES}
    names["bay"] = "PATCH BAY"
    for k in spec.TILE_VIEWS:
        x, y, tw, th = spec.TILES[k]
        put(frame, x, y, [pg("overview")], "Tile", "xp_tile.png")
        put_text(names[k], 36, x + 14, y + 32, [pg("overview")])
    for k in range(9):
        led_bar(k).save(os.path.join(folder, "xp_bar_%d.png" % k))
    for key, lab, bx in (("m_in", "IN", 70), ("m_out", "OUT", 330)):
        put_text(lab, 28, bx - 8, spec.STRIP_Y + 40, [pg("overview")], "r")
        put(led_bar(0), bx, spec.STRIP_Y + 32, [pg("overview")], "Bar", "xp_bar_0.png")
        for k in range(1, 9):
            put(led_bar(k), bx, spec.STRIP_Y + 32, [pg("overview"), "IndexedEnabling/%d/9/Parameter %d" % (k, idx[key])], "Bar", "xp_bar_%d.png" % k)
    put_text("OUTPUT", 28, 872, spec.STRIP_Y + 40, [pg("overview")], "r")

    # 3b) the meters on the module pages: the VU dial (gain reduction on the compressors, level on the tape machines) and
    # the gain reduction lamps of XXL-DISS; all follow the parameter m_vu. The dial / the unlit lamps are pieces of the
    # Panel Editor; the needle and lit-lamp pictures follow wherever that piece is put.
    followers = []   # (base instance, [overlay instances], kind, view key)
    edir = os.path.join(ROOT, "build", "editor_only")
    os.makedirs(edir, exist_ok=True)
    for vkey, (kind, mx, my, mw) in spec.METERS.items():
        over_insts = []
        if kind == "vu":
            mh = int(round(mw * VU_ART[1] / float(VU_ART[0])))
            fn = "xp_vu_%d.png" % mw
            face = vu_face(mw, mh)
            if not os.path.isfile(os.path.join(folder, fn)):
                face.save(os.path.join(folder, fn), optimize=True)
            put(face, mx - mw // 2, my - mh // 2, [pg(vkey)], "Group", fn)
            shown = face.copy()
            shown.alpha_composite(vu_needle(21, mw, mh))
            shown.save(os.path.join(edir, "vu_%d.png" % mw))
            art_items[-1]["editor_src"] = os.path.join(edir, "vu_%d.png" % mw)
            art_items[-1]["text"] = "VU meter"
            for k in range(VU_N):
                nn = "xp_vun_%d_%d.png" % (mw, k)
                nd = vu_needle(k, mw, mh)
                if not os.path.isfile(os.path.join(folder, nn)):
                    nd.save(os.path.join(folder, nn), optimize=True)
                over_insts.append(image_instance("Needle", nn, mx - mw // 2, my - mh // 2, nd.size[0], nd.size[1],
                                                 [pg(vkey), "IndexedEnabling/%d/%d/Parameter %d" % (k, VU_N, idx["m_vu"])]))
        else:
            ld = led_ladder(0)
            if not os.path.isfile(os.path.join(folder, "xp_gr_0.png")):
                ld.save(os.path.join(folder, "xp_gr_0.png"), optimize=True)
            put(ld, mx - ld.size[0] // 2, my - ld.size[1] // 2, [pg(vkey)], "Group", "xp_gr_0.png")
            led_ladder(6).save(os.path.join(edir, "lamps.png"))
            art_items[-1]["editor_src"] = os.path.join(edir, "lamps.png")
            art_items[-1]["text"] = "GR lamps"
            for k in range(1, 17):
                nn = "xp_gr_%d.png" % k
                if not os.path.isfile(os.path.join(folder, nn)):
                    led_ladder(k).save(os.path.join(folder, nn), optimize=True)
                over_insts.append(image_instance("Lamps", nn, mx - ld.size[0] // 2, my - ld.size[1] // 2, ld.size[0], ld.size[1],
                                                 [pg(vkey), "IndexedEnabling/%d/%d/Parameter %d" % (k, VU_N, idx["m_vu"])]))
            put_text("GAIN REDUCTION  dB", 26, mx, my + 64, [pg(vkey)], "c")
        followers.append((injected[-1] if kind == "vu" else injected[-2], over_insts, kind))
        injected.extend(over_insts)

    # 4) the patch bay: sockets and names, the CONNECTED page
    sk = socket_image()
    sk.save(os.path.join(folder, "xp_socket.png"))
    put_text("OUTPUTS", 26, 520, spec.BAY_Y0 + 6, [pg("bay")])
    put_text("INPUTS", 26, W - 520, spec.BAY_Y0 + 6, [pg("bay")], "r")
    for col, row, head in spec.BAY_GROUPS:   # group headings, the same on both sides
        gy = spec.BAY_Y0 + row * spec.BAY_DY + 6
        hi = text_image(head, 26, (176, 174, 168))
        for gx, right in ((spec.AO_X[col] + 20, True), (spec.AI_X[col] - 20, False)):
            put(hi, gx - hi.size[0] if right else gx, gy - hi.size[1] // 2, [pg("bay")], "Text", edit={"text": head, "size": 26, "colour": "#b0aea8"})
            ln = Image.new("RGBA", (150, 2), LINE + (255,))
            put(ln, gx - 150 if right else gx, gy + 20, [pg("bay")], "Group")
    for i, a in enumerate(spec.AUDIO_OUTS):
        x, y = spec.aud_out_pos(i)
        put(sk, x - sk.size[0] // 2, y - sk.size[1] // 2, [pg("bay")], "Socket", "xp_socket.png")
        put_text(a[1], 28, x - 28, y, [pg("bay")], "r", fixed=True)
    for i, b in enumerate(spec.AUDIO_INS):
        x, y = spec.aud_in_pos(i)
        put(sk, x - sk.size[0] // 2, y - sk.size[1] // 2, [pg("bay")], "Socket", "xp_socket.png")
        put_text(b[1], 28, x + 28, y, [pg("bay")], fixed=True)
    put_text("DRY LEVEL", 28, 992, 592, [pg("bay")], "r")
    conn = connected_panel()
    conn.save(os.path.join(folder, "xp_conn.png"), optimize=True)
    injected.append(image_instance("Panel", "xp_conn.png", 0, 0, W, H,
                                   [pg("bay"), "IndexedEnabling/4/%d/Parameter %d" % (len(spec.PK_STEPS), idx["pk"])]))

    # 5) cables: one picture (in pieces) per output / input pair
    cable_insts, pieces, total_px = [], 0, 0
    for a in range(spec.N_AO):
        for b in range(spec.N_AI):
            if spec.a_blocked(a, b):
                continue
            im, x0, y0 = draw_cable(spec.aud_out_pos(a), spec.aud_in_pos(b), spec.CABLE_COLOURS[(a * 3 + b) % len(spec.CABLE_COLOURS)],
                                    1.0, clip=(0, 60, W, 566))
            handles = ["IndexedEnabling/1/2/Parameter %d" % idx["ac_%s_%s" % (spec.AUDIO_OUTS[a][0], spec.AUDIO_INS[b][0])],
                       "IndexedEnabling/1/2/Parameter %d" % idx["pk_ta"]]
            for k, (piece, px, py) in enumerate(tile_pieces(im, x0, y0, spec.CABLE_TILE)):
                name = "xp_cab_%d_%d_%d.png" % (a, b, k)
                piece.save(os.path.join(folder, name), optimize=True)
                total_px += piece.size[0] * piece.size[1]
                pieces += 1
                cable_insts.append(image_instance("Cable", name, px, py, piece.size[0], piece.size[1], handles))

    # 6) the ring of the socket that waits, sockets that fit or are blocked
    over = []
    ring = ring_img(26, 4)
    ring.save(os.path.join(folder, "xp_ring.png"))
    dim = dim_img(22)
    dim.save(os.path.join(folder, "xp_dim.png"))
    R = ring.size[0]
    for prefix, n, pos in (("hao", spec.N_AO, spec.aud_out_pos), ("hai", spec.N_AI, spec.aud_in_pos)):
        for k in range(n):
            g, p = divmod(k, spec.JACK_GROUP)
            gsize = min(spec.JACK_GROUP, n - g * spec.JACK_GROUP)
            x, y = pos(k)
            over.append(image_instance("Ring", "xp_ring.png", x - R // 2, y - R // 2, R, R,
                                       ["IndexedEnabling/%d/%d/Parameter %d" % (p + 1, gsize + 1, idx["%s_%d" % (prefix, g)])]))
    for kind, n, pos in (("fao", spec.N_AO, spec.aud_out_pos), ("fai", spec.N_AI, spec.aud_in_pos)):
        for k in range(n):
            x, y = pos(k)
            over.append(image_instance("Ring", "xp_ring.png", x - R // 2, y - R // 2, R, R,
                                       ["IndexedEnabling/1/3/Parameter %d" % idx["%s_%d" % (kind, k)]]))
            over.append(image_instance("Dim", "xp_dim.png", x - 22, y - 22, 44, 44,
                                       ["IndexedEnabling/2/3/Parameter %d" % idx["%s_%d" % (kind, k)]]))

    # 7) the Panel Editor: write what it can move (the layout as generated), then apply layout.json (the user's layout)
    model = editor_model(skin, comps, art_items)
    with open(os.path.join(ROOT, "build", "editor_data.json"), "w") as f:
        json.dump(model, f)
    lay = os.path.join(ROOT, "layout.json")
    layout = json.load(open(lay)) if os.path.isfile(lay) else {}
    n_moved = apply_layout(skin, folder, comps, art_items, layout)
    for base, overs, kind in followers:   # needles and lit lamps go where their dial / lamp row was put
        bx, by, bw_, bh_ = bounds(base["bounds"]["bounds"])
        for k, o in enumerate(overs):
            ox, oy, ow, oh = bounds(o["bounds"]["bounds"])
            if kind == "vu" and abs(bw_ - ow) > 1:   # the dial was resized: needles at the new size
                nd = vu_needle(k, int(bw_), int(bh_))
                nn = "xp_vun_%dx%d_%d.png" % (int(bw_), int(bh_), k)
                nd.save(os.path.join(folder, nn), optimize=True)
                o["componentData"]["data"]["image"] = nn
                ow, oh = nd.size
            o["bounds"]["bounds"] = bstr(bx, by, ow, oh)
    names = [v[2] or "Overview" for v in spec.VIEWS]
    for k, o in enumerate(layout.get("parts", [])):   # texts and pictures added in the editor
        if not o.get("added") or o.get("page") not in names:
            continue
        vkey = spec.VIEWS[names.index(o["page"])][0]
        if o["added"] == "text":
            col = str(o.get("colour", "#ffffff"))
            im = text_image(str(o.get("text", "")), max(MIN_BUILD["text"], float(o.get("size", 30))) * CSS, tuple(int(col[i:i + 2], 16) for i in (1, 3, 5)))
            name = "xpa_%d.png" % k
            im.save(os.path.join(folder, name), optimize=True)
            injected.append(image_instance("Added", name, int(o["x"]), int(o["y"] + (o["h"] - im.size[1]) / 2), im.size[0], im.size[1], [pg(vkey)]))
        elif o["added"] == "image" and str(o.get("data", "")).startswith("data:image"):
            import base64, io
            im = Image.open(io.BytesIO(base64.b64decode(o["data"].split(",", 1)[1]))).convert("RGBA").resize((max(1, int(o["w"])), max(1, int(o["h"]))), Image.LANCZOS)
            name = "xpa_%d.png" % k
            im.save(os.path.join(folder, name), optimize=True)
            injected.append(image_instance("Added", name, int(o["x"]), int(o["y"]), im.size[0], im.size[1], [pg(vkey)]))
        n_moved += 1
    print("post_skin: Panel Editor data written; layout.json moved %d parts" % n_moved)

    comps[1:1] = injected + cable_insts + over
    skin.save()
    print("post_skin: %d views, %d drawn pictures, %d cable pieces (%.1f MB decoded), %d components" % (
        len(spec.VIEWS), n_img[0], pieces, total_px * 4 / 1e6, len(comps)))
    if small:
        sys.exit("post_skin: text below %d px:\n  " % MIN_PX + "\n  ".join(small))

    # every live text of the page: nothing under MIN_PX
    low = set()
    for key, d in skin.defs.items():
        for sub in d.get("componentsData", []):
            if sub["componentData"]["type"] == "Label":
                px = float(sub["componentData"]["data"].get("textStyle", {}).get("font", {}).get("height", 99))
                if px < MIN_PX:
                    low.add("%s: %g px" % (key, px))
    if low:
        sys.exit("post_skin: live text below %d px:\n  " % MIN_PX + "\n  ".join(sorted(low)))

    if preview:
        os.makedirs(preview, exist_ok=True)
        comp = Composer(skin)
        texts = {"ts_" + k: "NOT PATCHED" for k in spec.TILE_VIEWS}
        texts.update({"ts_bay": "1 CABLE  DRY ON", "cpu_info": "LOAD 12%  COST 9", "patch_info": "Tap a socket, then the other end of the cable.",
                      "touch_info": "PEAK RED  30.0", "mod_info": "IN PATH   GAIN RED 3.2 dB"})
        for i, v in enumerate(spec.VIEWS):
            st = {"pg_" + v[0]: 1, "in_sec": 1 if i else 0, "in_mod": 1 if 1 <= i <= spec.N_MOD else 0,
                  "in_bay": 1 if v[0] == "bay" else 0, "hdr_ti": 1 if 1 <= i <= spec.N_MOD else 0, "m_in": 5, "m_out": 4, "m_vu": 21 if 1 <= i <= spec.N_MOD and v[0] != "mds" else 6}
            if v[0] == "bay":
                st.update({"ac_in_out": 1, "ac_in_m76": 1, "ac_m76_m2a": 1, "ac_m2a_out": 1, "ac_in_m48": 1, "ac_m48_out": 1,
                           "pk_ta": 1, "pk": 1})
            comp.compose(st, texts).convert("RGB").save(os.path.join(preview, "view_%02d_%s.png" % (i, v[0])))
        st = {"pg_bay": 1, "in_sec": 1, "in_bay": 1, "pk": 2, "pk_ta": 1, "pk_c": 1, "ac_in_out": 1, "hao_0": 4, "fai_0": 1, "fai_1": 1,
              "fai_2": 2, "fai_5": 1, "fai_15": 1, "fao_0": 2, "fao_1": 2}
        comp.compose(st, dict(texts, patch_info="76: now tap an input")).convert("RGB").save(os.path.join(preview, "view_17_bay_pick.png"))
        st = {"pg_bay": 1, "in_sec": 1, "in_bay": 1, "pk": 4}
        comp.compose(st, dict(texts, patch_info="76  >  2A")).convert("RGB").save(os.path.join(preview, "view_18_bay_connected.png"))


if __name__ == "__main__":
    main()
