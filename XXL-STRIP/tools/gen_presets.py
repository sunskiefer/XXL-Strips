#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""XXL STRIP's factory preset bank -> presets.json (the wrapper's own list, shown in MPC's PRESET menu).

    python3 tools/gen_presets.py

Every preset sets every user parameter (mpc-vst-plugins rule), starting from the defaults; the first is the default
sound. The display-only meters are left out: the engine drives them.
Options are given by label. Add presets at the END only: MPC stores the chosen program by position.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_params as G  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
IN, OUT, ON, OFF = "In", "Out", "On", "Off"


def comp(thr, ratio, rel, fast=False, makeup=True):
    return {"dyn_in": IN, "comp_thr": thr, "comp_ratio": ratio, "comp_release": rel,
            "comp_attack": "Fast" if fast else "Auto", "makeup": "Auto" if makeup else "Off"}


def gate(thr, rng, rel, hold=0.0, mode="Gate", fast=True):
    return {"dyn_in": IN, "gate_in": IN, "gate_mode": mode, "gate_thr": thr, "gate_range": rng, "gate_release": rel,
            "gate_hold": hold, "gate_fast": ON if fast else OFF}


def hpf(f):
    return {"hpf_in": IN, "hpf_freq": f}


def lpf(f):
    return {"lpf_in": IN, "lpf_freq": f}


def eq(lf=None, lmf=None, hmf=None, hf=None):
    d = {}
    if lf: d.update(lf_gain=lf[0], lf_freq=lf[1], lf_bell="Bell" if len(lf) > 2 and lf[2] else "Shelf")
    if lmf: d.update(lmf_gain=lmf[0], lmf_freq=lmf[1], lmf_q=lmf[2] if len(lmf) > 2 else 1.5)
    if hmf: d.update(hmf_gain=hmf[0], hmf_freq=hmf[1], hmf_q=hmf[2] if len(hmf) > 2 else 1.5)
    if hf: d.update(hf_gain=hf[0], hf_freq=hf[1], hf_bell="Bell" if len(hf) > 2 and hf[2] else "Shelf")
    return d


def mix(*parts, **kw):
    d = {}
    for p in parts:
        d.update(p)
    d.update(kw)
    return d


BROWN, BLACK, GM = {"model": "E Brown"}, {"model": "E Black"}, {"model": "G"}

PRESETS = [
    ("Default", {}),
    # ---- vocals
    ("VOX Lead Clean", mix(BLACK, hpf(90), eq(lmf=(-2.5, 300, 1.2), hmf=(2.5, 3500, 1.2), hf=(3, 10000)), comp(-4, 3, 0.3))),
    ("VOX Lead Bright", mix(BLACK, hpf(110), eq(lmf=(-3, 250, 1.0), hmf=(3, 4500, 1.0), hf=(5, 12000)), comp(-6, 4, 0.25))),
    ("VOX Lead Warm", mix(BROWN, hpf(80), eq(lf=(2, 180), lmf=(-2, 450, 1.0), hf=(2, 8000)), comp(-5, 3, 0.4), drive=20)),
    ("VOX Rap Upfront", mix(BLACK, hpf(100), eq(lmf=(-3, 280, 1.4), hmf=(4, 2800, 1.3), hf=(3, 9000)), comp(-9, 6, 0.15, fast=True))),
    ("VOX Backing Air", mix(BROWN, hpf(160), eq(lmf=(-4, 350, 1.0), hf=(6, 14000)), comp(-8, 4, 0.3))),
    ("VOX Telephone", mix(GM, hpf(390), lpf(3400), eq(hmf=(6, 1800, 2.5)), comp(-10, 8, 0.2), drive=45)),
    ("VOX De-Mud", mix(BLACK, hpf(120), eq(lmf=(-6, 320, 2.0)))),
    ("VOX Limit Hard", mix(BLACK, hpf(90), eq(hmf=(2, 4000, 1.0)), comp(-12, 20, 0.2, fast=True))),
    # ---- drums
    ("KICK Punch", mix(BLACK, eq(lf=(5, 60, True), lmf=(-6, 380, 1.8), hmf=(4, 3800, 1.5)), comp(-4, 4, 0.15), gate(-12, 30, 0.15))),
    ("KICK Sub 808", mix(BROWN, lpf(9000), eq(lf=(6, 50), lmf=(-4, 250, 1.5)), comp(-6, 3, 0.4), drive=30)),
    ("KICK Click", mix(GM, hpf(35), eq(lf=(3, 70, True), lmf=(-8, 420, 2.2), hmf=(7, 5000, 2.0)), gate(-10, 40, 0.1))),
    ("SNARE Crack", mix(BLACK, hpf(110), eq(lf=(3, 200, True), lmf=(-4, 500, 1.8), hmf=(5, 5000, 1.2), hf=(4, 10000)), comp(-6, 5, 0.12, fast=True))),
    ("SNARE Fat", mix(BROWN, hpf(80), eq(lf=(5, 180, True), hmf=(3, 3000, 1.0)), comp(-8, 4, 0.2), drive=25)),
    ("SNARE Gated", mix(BLACK, hpf(120), eq(lf=(4, 220, True), hf=(5, 9000)), comp(-6, 6, 0.1, fast=True), gate(-8, 40, 0.12, hold=0.08))),
    ("CLAP Wide Top", mix(BLACK, hpf(250), eq(hmf=(3, 2500, 1.0), hf=(6, 12000)), comp(-6, 4, 0.1, fast=True))),
    ("HAT Tight", mix(BLACK, hpf(390), eq(lmf=(-5, 800, 1.5), hf=(4, 12000)), gate(-14, 20, 0.1, mode="Expand"))),
    ("HAT Soft", mix(BROWN, hpf(300), lpf(14000), eq(hmf=(-3, 5000, 1.2)))),
    ("TOM Boom", mix(BLACK, hpf(50), eq(lf=(5, 100, True), lmf=(-6, 450, 1.8), hmf=(4, 4000, 1.5)), gate(-12, 40, 0.4, hold=0.1))),
    ("PERC Snap", mix(GM, hpf(180), eq(hmf=(5, 6000, 2.0), hf=(3, 12000)), comp(-5, 5, 0.1, fast=True))),
    ("OVERHEAD Sheen", mix(BROWN, hpf(200), eq(lmf=(-3, 400, 1.0), hf=(5, 12000)), comp(-2, 2, 0.6))),
    ("ROOM Smash", mix(BLACK, hpf(60), eq(lf=(4, 100), hf=(3, 8000)), comp(-16, 20, 0.1, fast=True), drive=40)),
    ("DRUM LOOP Glue", mix(BLACK, hpf(30), eq(lf=(2, 80), hf=(2, 10000)), comp(-6, 3, 0.3))),
    ("DRUM LOOP Dirt", mix(GM, eq(lf=(4, 90), hmf=(3, 2500, 1.0)), comp(-10, 8, 0.15, fast=True), drive=65)),
    ("BREAK Lo-Fi", mix(BROWN, hpf(120), lpf(6000), eq(lmf=(3, 700, 1.0)), comp(-10, 6, 0.2), drive=55)),
    # ---- bass
    ("BASS Solid", mix(BLACK, hpf(30), eq(lf=(3, 80), lmf=(-3, 300, 1.4), hmf=(3, 1200, 1.2)), comp(-6, 5, 0.3))),
    ("BASS Sub Clean", mix(BROWN, lpf(5000), eq(lf=(4, 60), lmf=(-4, 220, 1.5)), comp(-5, 4, 0.5))),
    ("BASS Growl", mix(GM, hpf(40), eq(lmf=(4, 800, 1.5), hmf=(5, 2200, 1.8)), comp(-8, 6, 0.2), drive=60)),
    ("BASS Pick Attack", mix(BLACK, hpf(40), eq(lf=(2, 90), hmf=(6, 3000, 1.5)), comp(-6, 4, 0.15, fast=True))),
    ("BASS 808 Level", mix(BLACK, eq(lf=(2, 55)), comp(-10, 20, 0.6))),
    ("BASS Reese Tame", mix(BROWN, hpf(35), lpf(8000), eq(lmf=(-4, 350, 1.2)), comp(-8, 5, 0.4))),
    # ---- guitars and keys
    ("GTR Acoustic", mix(BROWN, hpf(100), eq(lmf=(-4, 250, 1.3), hmf=(2, 5000, 1.0), hf=(4, 12000)), comp(-5, 3, 0.4))),
    ("GTR Electric Bite", mix(BLACK, hpf(110), lpf(10000), eq(lmf=(-3, 400, 1.5), hmf=(5, 3200, 1.5)), comp(-4, 3, 0.3))),
    ("GTR Clean Chime", mix(GM, hpf(120), eq(hmf=(3, 6000, 1.2), hf=(4, 12000)), comp(-6, 4, 0.25))),
    ("GTR Heavy Carve", mix(BLACK, hpf(90), lpf(9000), eq(lmf=(-6, 500, 2.0), hmf=(3, 2500, 1.2)))),
    ("KEYS Piano Open", mix(BROWN, hpf(50), eq(lmf=(-2, 300, 1.0), hf=(4, 10000)), comp(-4, 2.5, 0.5))),
    ("KEYS Rhodes Warm", mix(BROWN, hpf(60), lpf(12000), eq(lf=(2, 150), hmf=(2, 2000, 1.0)), comp(-5, 3, 0.4), drive=30)),
    ("KEYS Organ Body", mix(GM, hpf(70), eq(lmf=(3, 600, 1.0), hmf=(-2, 3000, 1.2)), drive=35)),
    ("SYNTH Lead Cut", mix(BLACK, hpf(150), eq(hmf=(4, 3500, 1.3), hf=(3, 10000)), comp(-5, 4, 0.2))),
    ("SYNTH Pad Space", mix(BROWN, hpf(180), eq(lmf=(-4, 400, 1.0), hf=(5, 14000)))),
    ("SYNTH Pluck Pop", mix(GM, hpf(120), eq(hmf=(5, 4500, 1.8)), comp(-6, 5, 0.1, fast=True))),
    ("SYNTH Bass Mono", mix(BLACK, hpf(30), eq(lf=(3, 70), hmf=(3, 1500, 1.2)), comp(-8, 6, 0.25))),
    ("STRINGS Silk", mix(BROWN, hpf(120), eq(lmf=(-2, 500, 1.0), hf=(4, 12000)), comp(-2, 2, 0.8))),
    ("BRASS Forward", mix(BLACK, hpf(100), eq(hmf=(4, 2500, 1.2), hf=(2, 9000)), comp(-6, 4, 0.3))),
    # ---- samples and effects
    ("SAMPLE Vinyl Tone", mix(BROWN, hpf(60), lpf(9000), eq(lf=(2, 120), hmf=(-2, 4000, 1.0)), drive=40)),
    ("SAMPLE Chop Level", mix(BLACK, hpf(40), comp(-8, 6, 0.2, fast=True))),
    ("SAMPLE Brighten", mix(GM, eq(hmf=(2, 5000, 1.0), hf=(6, 12000)))),
    ("SAMPLE Dark Dub", mix(BROWN, lpf(4500), eq(lf=(4, 90), lmf=(2, 500, 1.0)), drive=50)),
    ("FX Radio", mix(GM, hpf(390), lpf(3200), eq(hmf=(8, 2000, 3.0)), drive=70)),
    ("FX Thin Air", mix(BLACK, hpf(390), eq(hf=(8, 14000)))),
    ("FX Crush Limit", mix(BLACK, comp(-20, 20, 0.1, fast=True), drive=100)),
    ("FX Gate Chop", mix(BLACK, gate(-6, 40, 0.1, hold=0.0))),
    # ---- starting points per model
    ("INIT E Brown", mix(BROWN)),
    ("INIT E Black", mix(BLACK)),
    ("INIT G", mix(GM)),
    ("INIT Drive Only", mix(BROWN, drive=50)),
]


def main():
    by_key = {p["key"]: p for p in G.P}
    out = []
    for name, over in PRESETS:
        vals = {}
        for p in G.P:
            if p.get("readonly"):
                continue   # meters: the engine drives them, a preset must not claim a value
            vals[p["key"]] = p["options"][int(p["default"])] if "options" in p else p["default"]
        for k, v in over.items():
            p = by_key[k]   # KeyError = a typo in a preset
            if "options" in p:
                assert v in p["options"], (name, k, v)
            else:
                assert p["min"] <= v <= p["max"], (name, k, v)
            vals[k] = v
        out.append({"name": name, "values": vals})
    assert len({n for n, _ in PRESETS}) == len(PRESETS)
    with open(os.path.join(ROOT, "presets.json"), "w") as f:
        json.dump({"presets": out}, f, indent=1)
        f.write("\n")
    print("presets.json: %d factory presets" % len(out))


if __name__ == "__main__":
    main()
