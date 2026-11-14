#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""XXL STRIP BUS factory presets -> presets.json. Add at the END only. Meters are left out (the engine drives them)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_params as G
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
def c(thr, ratio, att, rel, mk, **kw):
    d = {"thr": thr, "ratio": ratio, "attack": att, "release": rel, "makeup": mk}; d.update(kw); return d
M = {"mode": "Modern"}
def m(thr, ratio, att, rel, mk, hpf=None, mix=100):
    d = c(thr, ratio, att, rel, mk, mode="Modern", mix=mix)
    if hpf: d.update(sc_hpf_in="In", sc_hpf=hpf)
    return d
PRESETS = [
    ("Default", {}),
    ("MIX Glue Gentle", c(2, "2:1", "30 ms", "Auto", 1)), ("MIX Glue Classic", c(0, "4:1", "10 ms", "Auto", 2)),
    ("MIX Glue Firm", c(-3, "4:1", "30 ms", "0.3 s", 3)), ("MIX Loud", c(-6, "4:1", "10 ms", "0.1 s", 5)),
    ("MIX Pump", c(-8, "4:1", "30 ms", "0.1 s", 5)), ("MIX Safe Peaks", c(4, "10:1", "1 ms", "0.3 s", 0)),
    ("MIX Low End Free", m(-2, "4:1", "30 ms", "Auto", 2, hpf=120)), ("MIX Parallel Punch", m(-12, "10:1", "3 ms", "0.1 s", 8, mix=40)),
    ("MIX Soft Touch", m(3, "1.5:1", "30 ms", "Auto", 1)), ("MIX Dense", m(-5, "2:1", "10 ms", "0.6 s", 4, hpf=60)),
    ("DRUMS Glue", c(-2, "4:1", "30 ms", "0.3 s", 2)), ("DRUMS Punch", c(-6, "4:1", "30 ms", "0.1 s", 4)),
    ("DRUMS Smash", c(-12, "10:1", "0.1 ms", "0.1 s", 9)), ("DRUMS Snap", c(-5, "4:1", "10 ms", "0.1 s", 3)),
    ("DRUMS Room Pump", c(-10, "10:1", "3 ms", "0.3 s", 7)), ("DRUMS Parallel", m(-14, "10:1", "1 ms", "0.1 s", 10, mix=35)),
    ("DRUMS Kick Safe", m(-6, "4:1", "30 ms", "0.1 s", 4, hpf=150)), ("DRUMS Tight", c(-4, "2:1", "3 ms", "0.3 s", 2)),
    ("BASS Hold", c(-4, "4:1", "10 ms", "0.6 s", 3)), ("BASS Level", c(-8, "10:1", "3 ms", "1.2 s", 5)),
    ("BASS Sub Free", m(-5, "4:1", "30 ms", "0.3 s", 3, hpf=100)),
    ("VOX Bus Smooth", c(-2, "2:1", "10 ms", "Auto", 2)), ("VOX Bus Forward", c(-5, "4:1", "3 ms", "0.3 s", 4)),
    ("VOX Bus Parallel", m(-12, "10:1", "1 ms", "0.3 s", 8, mix=50)),
    ("KEYS Bus Glue", c(0, "2:1", "30 ms", "Auto", 1)), ("SYNTH Bus Tight", c(-4, "4:1", "10 ms", "0.3 s", 3)),
    ("GTR Bus Even", c(-3, "4:1", "10 ms", "0.6 s", 2)), ("STRINGS Bus Soft", m(1, "1.5:1", "30 ms", "1.2 s", 1)),
    ("SAMPLE Loop Glue", c(-3, "4:1", "30 ms", "Auto", 2)), ("SAMPLE Loop Crush", c(-14, "10:1", "0.1 ms", "0.1 s", 10)),
    ("FX Hard Pump", c(-15, "10:1", "30 ms", "0.1 s", 10)), ("FX Limit", c(-6, "10:1", "0.1 ms", "0.3 s", 4)),
    ("INIT Classic", {}), ("INIT Modern", M),
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
