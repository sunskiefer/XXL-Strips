#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""The XXL strips' panel pieces, after gen_vst.py and tools/post_skin.py:

    python3 tools/strip_skin.py "<skin dir>/Plugin Skins" layout.conf [--preview build/preview]

  - every knob is the rendered knob (tools/knob_render.py as it is, transparent background, turning in place) in the
    style tools/knob_styles.json gives it, with the tick-ring dial around it and its name and value under the dial;
  - the small pill switches become large ON / OFF buttons;
  - the VU meter is the VU dial art (art/user/vu_face.png) with a moving needle, driven by the engine;
  - the page captions are separate text pieces;
  - build/editor_data.json is written for the Panel Editor (tools/make_editor.py), and layout.json, the editor's
    export, is applied: every piece where the user put it, in the knob style the user chose.
The shared skin code is tools/pro_lib.py (XXL Pro's skin script).
"""
import json, math, os, re, shlex, sys, types

from PIL import Image, ImageDraw

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
folder, layout_conf = sys.argv[1], sys.argv[2]
preview = sys.argv[sys.argv.index("--preview") + 1] if "--preview" in sys.argv else None
tui = json.load(open(os.path.join(folder, "TUI.json")))
PAGES = [t["componentName"] for t in tui["pageData"]["tabs"]]
TABS = [t["tabName"] for t in tui["pageData"]["tabs"]]
STYLES = json.load(open(os.path.join(ROOT, "tools", "knob_styles.json")))
PARAMS = json.load(open(os.path.join(ROOT, "params.json")))["params"]

# pro_lib was written against XXL Pro's spec: give it this plugin's pages and controls in that shape
spec = types.ModuleType("spec")
spec.VIEWS = [(n, n, n) for n in TABS]
spec.VIEW_KEYS = TABS
spec.MODULES, spec.MODULE_COLS, spec.NAV, spec.JACK_R = [], {}, [], 17
spec.BAY_BTN = spec.BAY_CLEAR = ("", "", 0, 0, 0, 0)
spec.CONTROLS = [{"key": p["key"], "kind": "toggle" if "options" in p else "knob", "colour": STYLES.get(p["key"], STYLES.get("*", "GREY"))} for p in PARAMS]
spec.CTRL = {c["key"]: c for c in spec.CONTROLS}
sys.modules["spec"] = spec
import pro_lib as L  # noqa: E402

L.ROOT = ROOT
L.TAB = PAGES[0]
skin = L.Skin(folder)
bounds, bstr = L.bounds, L.bstr
VU_FRAMES = 64


def vu_face_and_needles(w, h):
    """the user's VU dial art (art/user/vu_face_v2.png, no needle, used as it is) with VU_FRAMES needle positions drawn
    on it (w x h px). Geometry measured from the art: see pro_lib.VU_PIVOT."""
    art = Image.open(os.path.join(ROOT, "art", "user", "vu_face_v2.png")).convert("RGB")
    aw, ah = art.size
    S = 4
    big = art.resize((aw * S, ah * S), Image.LANCZOS)
    frames = []
    for i in range(VU_FRAMES):
        db = -20.0 + 23.0 * i / (VU_FRAMES - 1)
        frac = (10 ** (db / 20.0) - 0.1) / (10 ** (3 / 20.0) - 0.1)
        ang = math.radians(-48.0 + 96.0 * frac)
        im = big.copy()
        px, py = L.VU_PIVOT
        tip = (px + L.VU_TIP * math.sin(ang), py - L.VU_TIP * math.cos(ang))
        t0 = (py - L.VU_BASE_Y) / (py - tip[1])
        base = (px + (tip[0] - px) * t0, L.VU_BASE_Y)
        ImageDraw.Draw(im).line([(base[0] * S, base[1] * S), (tip[0] * S, tip[1] * S)], fill=(222, 236, 250), width=int(2.2 * S))
        frames.append(im.resize((w, h), Image.LANCZOS))
    return frames, 0.0


def vu_strip(w, h):
    name = "xv_vu_%dx%d.png" % (w, h)
    if not os.path.isfile(os.path.join(folder, name)):
        frames, changed = vu_face_and_needles(w, h)
        strip = Image.new("RGB", (w, h * VU_FRAMES))
        for i, f in enumerate(frames):
            strip.paste(f, (0, i * h))
        strip.save(os.path.join(folder, name), optimize=True)
        print("strip_skin: VU dial %dx%d, %d needle frames (your VU face as given)" % (w, h, VU_FRAMES))
    return name


def texts(path):
    out = {}
    for line in open(path):
        line = line.strip()
        if not line.startswith("#@text "):
            continue
        a = dict(tok.split("=", 1) for tok in shlex.split(line[7:]) if "=" in tok)
        out.setdefault(int(a["tab"]), []).append((int(a["cx"]), int(a["cy"]) - 86, float(a.get("size", 30)), a["label"]))
    return out


def main():
    TX = texts(layout_conf)
    over = json.load(open(os.path.join(ROOT, "layout.json"))) if os.path.isfile(os.path.join(ROOT, "layout.json")) else {}
    model = {"names": TABS, "views": [], "imgs": {}, "knobs": None, "knob_colour": {}, "bgs": []}
    moved = 0
    n_img = [0]
    for p, pkey in enumerate(PAGES):
        skin.page = skin.defs[pkey]
        comps = skin.page["componentsData"]
        L.views_of = lambda s, inst, _n=TABS[p]: [_n]
        L.recolour_knobs(skin, folder)
        L.restyle_toggles(skin, folder)
        injected, art_items = [], []

        def put(im, x, y, name, fname=None, edit=None):
            if fname is None:
                fname = "xs_%d.png" % n_img[0]
                n_img[0] += 1
                im.save(os.path.join(folder, fname), optimize=True)
            injected.append(L.image_instance(name, fname, int(x), int(y), im.size[0], im.size[1], []))
            it = {"id": "%s%d_%d" % ("txt" if edit else "img", p, len(art_items)), "inst": injected[-1], "kind": "txt" if edit else "img"}
            it.update(edit or {})
            art_items.append(it)

        # the dial around every knob
        for inst in comps:
            t = inst["componentData"]["type"]
            if not t.startswith("shKnob") or "Side" in t:
                continue
            x, y, w, h = bounds(inst["bounds"]["bounds"])
            ks = next(s for s in skin.defs[t]["componentsData"] if s["componentData"]["type"] == "Knob")
            kx, ky, tile, _ = bounds(ks["bounds"]["bounds"])
            k = tile / 100.0
            dial = L.dial_image(tile)
            dn = "xs_dial_%d.png" % tile
            dial.save(os.path.join(folder, dn), optimize=True)
            put(dial, x + kx + tile / 2.0 - 81 * k, y + ky + tile / 2.0 - 80.8 * k, "Dial", dn)
        # captions
        for (cx, cy, size, label) in TX.get(p, []):
            im = L.text_image(label, size)
            put(im, cx - im.size[0] // 2, cy - im.size[1] // 2, "Text", edit={"text": label, "size": size, "colour": "#ffffff"})
        # the VU dial in place of the VU slider; other meter sliders lose their small value text
        for inst in comps:
            key = skin.param_of(inst)
            t = inst["componentData"]["type"]
            if not t.startswith("shSlider"):
                continue
            x, y, w, h = bounds(inst["bounds"]["bounds"])
            if key == "vu":
                vw, vh = 298, 145
                o = next((q for q in over.get("parts", []) if q["id"] == "vu:body"), None)
                if o:
                    vw, vh = int(o["w"]), int(o["h"])
                d = json.loads(json.dumps(skin.defs[t]))
                d["actions"], d["ignoreMousePresses"] = [], True
                knob = next(s for s in d["componentsData"] if s["componentData"]["type"] == "Knob")
                knob["componentData"]["data"].update(filmStrip=vu_strip(vw, vh), numFrames=VU_FRAMES)
                knob["bounds"]["bounds"] = bstr(0, 0, vw, vh)
                d["componentsData"] = [knob]
                skin.defs_list.append({"key": "xsVu", "value": d})
                skin.defs["xsVu"] = d
                inst["componentData"]["type"] = "xsVu"
                inst["bounds"]["bounds"] = bstr(x + (w - vw) // 2, min(y, 628 - vh - 6), vw, vh)
                inst["bounds"]["acceptsHWFocus"] = "No"
            elif not t.startswith("xsLed"):   # the other meters: a row of lamps instead of the plain bar
                d = json.loads(json.dumps(skin.defs[t]))
                d["actions"], d["ignoreMousePresses"] = [], True
                knob = next(s2 for s2 in d["componentsData"] if s2["componentData"]["type"] == "Knob")
                kx, ky, kw, kh = bounds(knob["bounds"]["bounds"])
                count = 20 if kw >= 600 else 10
                name = "xs_led_%dx%d.png" % (kw, kh)
                if not os.path.isfile(os.path.join(folder, name)):
                    strip = Image.new("RGBA", (kw, kh * (count + 1)), (0, 0, 0, 0))
                    S = 3
                    for i in range(count + 1):
                        fr = Image.new("RGBA", (kw * S, kh * S), (0, 0, 0, 0))
                        dr = ImageDraw.Draw(fr)
                        cw = kw / float(count)
                        r = min(cw * 0.36, kh * 0.36)
                        for j in range(count):
                            cx, cy = (j + 0.5) * cw, kh / 2.0
                            lit = j < i
                            col = ((255, 120, 40) if j >= count * 0.75 else (255, 200, 60)) if lit else (70, 40, 20)
                            dr.ellipse([(cx - r - 3) * S, (cy - r - 3) * S, (cx + r + 3) * S, (cy + r + 3) * S], fill=(8, 8, 9, 255))
                            dr.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=col + (255,))
                            if lit:
                                dr.ellipse([(cx - r * 0.5) * S, (cy - r * 0.6) * S, (cx + r * 0.1) * S, (cy - r * 0.05) * S], fill=(255, 245, 220, 255))
                        strip.paste(fr.resize((kw, kh), Image.LANCZOS), (0, i * kh))
                    strip.save(os.path.join(folder, name), optimize=True)
                knob["componentData"]["data"].update(filmStrip=name, numFrames=count + 1)
                d["componentsData"] = [knob]
                dk = "xsLed_%dx%d" % (kw, kh)
                skin.defs_list.append({"key": dk, "value": d})
                skin.defs[dk] = d
                inst["componentData"]["type"] = dk
                inst["bounds"]["acceptsHWFocus"] = "No"
        # Panel Editor: this page's pieces, then the user's layout
        m = L.editor_model(skin, comps, art_items)
        model["views"].append(m["views"][p])
        model["imgs"].update(m["imgs"])
        model["knobs"] = m["knobs"]
        model["knob_colour"].update({k: v for k, v in m["knob_colour"].items()})
        model["bgs"].append(m["bg"] if p == 0 else None)
        moved += L.apply_layout(skin, folder, comps, art_items, over)
        for k, o in enumerate(over.get("parts", [])):
            if not o.get("added") or o.get("page") != TABS[p]:
                continue
            if o["added"] == "text":
                col = str(o.get("colour", "#ffffff"))
                im = L.text_image(str(o.get("text", "")), max(26.0, float(o.get("size", 30))) * 0.75, tuple(int(col[i:i + 2], 16) for i in (1, 3, 5)))
                im.save(os.path.join(folder, "xsa_%d.png" % k), optimize=True)
                injected.append(L.image_instance("Added", "xsa_%d.png" % k, int(o["x"]), int(o["y"] + (o["h"] - im.size[1]) / 2), im.size[0], im.size[1], []))
            elif o["added"] == "image" and str(o.get("data", "")).startswith("data:image"):
                import base64, io
                im = Image.open(io.BytesIO(base64.b64decode(o["data"].split(",", 1)[1]))).convert("RGBA").resize((max(1, int(o["w"])), max(1, int(o["h"]))), Image.LANCZOS)
                im.save(os.path.join(folder, "xsa_%d.png" % k), optimize=True)
                injected.append(L.image_instance("Added", "xsa_%d.png" % k, int(o["x"]), int(o["y"]), im.size[0], im.size[1], []))
            moved += 1
        comps[1:1] = injected
    for key, d in skin.defs.items():   # meter sliders carry no small value text (also the ones the VU dial replaced)
        if key.startswith("shSlider"):
            d["componentsData"] = [s2 for s2 in d["componentsData"] if s2["componentData"]["type"] != "Label"]
    model["bg"] = model.pop("bgs")[0]
    with open(os.path.join(ROOT, "build", "editor_data.json"), "w") as f:
        json.dump(model, f)
    skin.save()
    if L.small:
        sys.exit("strip_skin: text below 26 px:\n  " + "\n  ".join(L.small))
    low = set()
    for key, d in skin.defs.items():
        for sub in d.get("componentsData", []):
            if sub["componentData"]["type"] == "Label":
                px = float(sub["componentData"]["data"].get("textStyle", {}).get("font", {}).get("height", 99))
                if px < 26:
                    low.add("%s: %g px" % (key, px))
    if low:
        sys.exit("strip_skin: live text below 26 px:\n  " + "\n  ".join(sorted(low)))
    print("strip_skin: %d pages, layout.json moved %d parts" % (len(PAGES), moved))
    if preview:
        os.makedirs(preview, exist_ok=True)
        comp = L.Composer(skin)
        for p, pkey in enumerate(PAGES):
            skin.page = skin.defs[pkey]
            comp.compose({}, {}).convert("RGB").save(os.path.join(preview, "page_%d.png" % p))


if __name__ == "__main__":
    main()
