#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""XXL STRIP MASTER factory presets -> presets.json. Add at the END only. Meters are left out."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_params as G
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
def drv(d, den=5): return {"drive_in": "In", "drive": d, "density": den}
def eq(lf=0, lff="50", hf=0, hff="12k"): return {"eq_in": "In", "lf_gain": lf, "lf_freq": lff, "hf_gain": hf, "hf_freq": hff}
def hfc(thr, x=8000): return {"hfc_in": "In", "hfc_thr": thr, "hfc_xover": x}
def img(w, s=0): return {"img_in": "In", "width": w, "space": s}
T = {"trafo": "In"}
def mix(*p, **kw):
    d = {}
    for x in p: d.update(x)
    d.update(kw); return d
PRESETS = [
    ("Default", {}),
    ("MASTER Sweeten", mix(eq(1.5, "50", 2, "16k"), T)), ("MASTER Warm Glue", mix(drv(3, 6), eq(1, "70", 0.5, "12k"), T)),
    ("MASTER Open Top", mix(eq(0, "50", 3, "20k"), hfc(-2, 9000))), ("MASTER Wide", mix(img(2, 1), eq(0.5, "50", 1, "16k"))),
    ("MASTER Loud Ready", mix(drv(4, 7), eq(1.5, "50", 1.5, "12k"), hfc(-3, 7000), T)), ("MASTER Tame Harsh", mix(hfc(-6, 5000), eq(0, "50", -1, "8k"))),
    ("MASTER Sub Clean", mix(eq(2, "30", 0, "12k"), hpf="30 Hz")), ("MASTER Vinyl Feel", mix(drv(5, 8), eq(1, "90", -2, "12k"), img(-1, 0), T)),
    ("MASTER Club Low", mix(eq(3, "50", 1, "16k"), img(1, 2), T)), ("MASTER Mono Safe", mix(img(-3, -2), hpf="40 Hz")),
    ("MASTER Air Lift", mix(eq(0, "50", 4, "20k"), hfc(-1, 12000), img(1, 0))), ("MASTER Thick", mix(drv(6, 9), eq(2, "70", 0, "12k"), T)),
    ("MASTER Clean Wide", mix(img(3, 0), eq(0.5, "30", 1.5, "20k"))), ("MASTER Transformer", T),
    ("HIPHOP Bump", mix(drv(4, 6), eq(3.5, "70", 1, "12k"), T)), ("HIPHOP Dusty", mix(drv(6, 8), eq(2, "90", -3, "8k"), hfc(-5, 5000), T)),
    ("HOUSE Punch", mix(drv(3, 4), eq(2, "50", 2, "16k"), img(1.5, 1))), ("TECHNO Weight", mix(drv(5, 7), eq(3, "50", 0, "12k"), hpf="30 Hz", **T)),
    ("DNB Sheen", mix(eq(1, "50", 3, "16k"), hfc(-3, 8000), img(1, 0))), ("TRAP Sub Hold", mix(eq(4, "30", 1.5, "16k"), hfc(-2, 9000))),
    ("LOFI Soft", mix(drv(7, 9), eq(1, "90", -5, "8k"), img(-2, 0), T)), ("AMBIENT Wide", mix(img(4, 3), eq(0, "50", 2, "20k"))),
    ("ROCK Bite", mix(drv(5, 5), eq(1, "70", 2.5, "8k"), T)), ("POP Polish", mix(drv(2, 5), eq(1, "50", 3, "16k"), hfc(-3, 9000), img(1, 0))),
    ("DRUM BUS Crunch", mix(drv(8, 7), eq(2, "70", 2, "8k"), T)), ("DRUM BUS Tame Cymbals", mix(hfc(-7, 6000))),
    ("VOX BUS Silk", mix(eq(0, "50", 3, "16k"), hfc(-4, 7000), hpf="50 Hz")), ("SYNTH BUS Width", mix(img(3, 2), drv(2, 4))),
    ("BASS BUS Harmonics", mix(drv(7, 10), eq(1, "50", 0, "12k"), img(-4, -4), T)),
    ("FX Drive Max", mix(drv(10, 10), T)), ("FX Narrow Dark", mix(img(-4, 0), eq(0, "50", -9, "8k"))),
    ("INIT All In Flat", mix({"drive_in": "In", "drive": 0}, eq(), {"hfc_in": "In", "hfc_thr": 2}, img(0, 0))),
]
def main():
    by = {p["key"]: p for p in G.P}; out = []
    for name, over in PRESETS:
        vals = {p["key"]: (p["options"][int(p["default"])] if "options" in p else p["default"]) for p in G.P if not p.get("readonly")}
        for k, v in over.items():
            p = by[k]
            assert (v in p["options"]) if "options" in p else (p["min"] <= v <= p["max"]), (name, k, v)
            vals[k] = v
        out.append({"name": name, "values": vals})
    assert len({n for n, _ in PRESETS}) == len(PRESETS)
    json.dump({"presets": out}, open(os.path.join(ROOT, "presets.json"), "w"), indent=1)
    print("presets.json: %d factory presets" % len(out))
if __name__ == "__main__": main()
