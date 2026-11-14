#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""The single source of XXL STRIP's parameter list: writes params.json (for mpc-vst-plugins' gen_vst.py) and
src/param_ids.h (P_<KEY> index constants).

    python3 tools/gen_params.py

MPC stores automation and saved values by parameter INDEX, so this list is append-only: never reorder, rename a key
or remove a parameter once a release has shipped.

Control set and ranges: the E-series card control list published in chijenpeng/classic-channel-strip's README
(names and ranges only, no code), plus the model switch, gate/expander and meters.
"""
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

OUT_IN = ["Out", "In"]
OFF_ON = ["Off", "On"]

# value lists shared by name (one list, many params)
LISTS = {
    "outIn": OUT_IN,
    "offOn": OFF_ON,
    "model": ["E Brown", "E Black", "G"],
    "shape": ["Shelf", "Bell"],
    "attack": ["Auto", "Fast"],
    "makeup": ["Off", "Auto"],
    "position": ["Pre EQ", "Post EQ"],
    "sidechain": ["Input", "Filters", "EQ"],
    "gateMode": ["Expand", "Gate"],
    "oversampling": ["1x", "2x"],
    "vuSource": ["Output", "Input", "Gain Red"],
}


def knob(key, name, lo, hi, default, region, **kw):
    p = {"key": key, "name": name, "min": lo, "max": hi, "default": default, "dynamic_display": True,
         "region": region}
    p.update(kw)
    return p


def opts(key, name, lst, default, region, **kw):
    p = {"key": key, "name": name, "options": LISTS[lst], "default": default, "region": region, "valuelist": lst}
    p.update(kw)
    return p


def meter(key, name, region):
    # display-only: the engine sets it, the wrapper reports it (HAS_DISPLAY_REV)
    return {"key": key, "name": name, "min": 0.0, "max": 1.0, "default": 0.0, "region": region, "readonly": True,
            "dynamic_display": True}


P = []
# ---- 0.1.0 ---------------------------------------------------------------------------------------------------------
P += [
    # input
    knob("in_gain", "INPUT", -20.0, 20.0, 0.0, "input"),
    opts("phase", "PHASE", "offOn", 0, "input"),
    opts("model", "MODEL", "model", 1, "input", refresh_display=True),
    knob("drive", "DRIVE", 0.0, 100.0, 0.0, "input"),
    opts("os", "OVERSMP", "oversampling", 0, "input"),
    # filters
    opts("hpf_in", "HPF", "outIn", 0, "filters"),
    knob("hpf_freq", "HPF FRQ", 16.0, 390.0, 16.0, "filters"),
    opts("lpf_in", "LPF", "outIn", 0, "filters"),
    knob("lpf_freq", "LPF FRQ", 3200.0, 22000.0, 22000.0, "filters"),
    # equaliser
    opts("eq_in", "EQ", "outIn", 1, "eq"),
    knob("hf_gain", "HF GAIN", -18.0, 18.0, 0.0, "eq_hf"),
    knob("hf_freq", "HF FRQ", 1300.0, 19000.0, 8000.0, "eq_hf"),
    opts("hf_bell", "HF SHAPE", "shape", 0, "eq_hf"),
    knob("hmf_gain", "HMF GAIN", -18.0, 18.0, 0.0, "eq_hmf"),
    knob("hmf_freq", "HMF FRQ", 640.0, 9400.0, 3000.0, "eq_hmf"),
    knob("hmf_q", "HMF Q", 0.5, 4.1, 1.5, "eq_hmf"),
    opts("hmf_x3", "HMF x3", "offOn", 0, "eq_hmf"),
    knob("lmf_gain", "LMF GAIN", -18.0, 18.0, 0.0, "eq_lmf"),
    knob("lmf_freq", "LMF FRQ", 140.0, 2000.0, 600.0, "eq_lmf"),
    knob("lmf_q", "LMF Q", 0.5, 4.2, 1.5, "eq_lmf"),
    opts("lmf_d3", "LMF /3", "offOn", 0, "eq_lmf"),
    knob("lf_gain", "LF GAIN", -18.0, 18.0, 0.0, "eq_lf"),
    knob("lf_freq", "LF FRQ", 37.0, 420.0, 100.0, "eq_lf"),
    opts("lf_bell", "LF SHAPE", "shape", 0, "eq_lf"),
    # compressor
    opts("dyn_in", "DYNAMICS", "outIn", 1, "comp"),
    knob("comp_thr", "THRESH", -20.0, 10.0, 10.0, "comp"),
    knob("comp_ratio", "RATIO", 1.0, 20.0, 5.0, "comp"),
    opts("comp_attack", "ATTACK", "attack", 0, "comp"),
    knob("comp_release", "RELEASE", 0.1, 4.0, 0.1, "comp"),
    opts("makeup", "MAKE-UP", "makeup", 0, "comp"),
    opts("dyn_pos", "POSITION", "position", 0, "comp"),
    opts("sc_src", "SIDECHN", "sidechain", 0, "comp"),
    # gate / expander
    opts("gate_in", "GATE", "outIn", 0, "gate"),
    opts("gate_mode", "MODE", "gateMode", 0, "gate"),
    knob("gate_thr", "THRESH", -30.0, 10.0, -30.0, "gate"),
    knob("gate_range", "RANGE", 0.0, 40.0, 20.0, "gate"),
    knob("gate_hold", "HOLD", 0.0, 4.0, 0.0, "gate"),
    knob("gate_release", "RELEASE", 0.1, 4.0, 0.3, "gate"),
    opts("gate_fast", "FAST ATT", "offOn", 0, "gate"),
    # output and meters
    knob("out_gain", "OUTPUT", -20.0, 20.0, 0.0, "output"),
    opts("vu_src", "VU SHOWS", "vuSource", 0, "output"),
    meter("vu", "VU", "meters"),
    meter("gr", "GAIN RED", "meters"),
    meter("gate_gr", "GATE RED", "meters"),
]
assert len(P) == 44

REGIONS = {}
for p in P:
    REGIONS.setdefault(p["region"], []).append(p["key"])


def main():
    out = []
    for p in P:
        q = {k: v for k, v in p.items() if k not in ("region", "valuelist", "readonly")}
        out.append(q)
    with open(os.path.join(ROOT, "params.json"), "w") as f:
        json.dump({"name": "XXL STRIP", "params": out}, f, indent=1)
        f.write("\n")
    with open(os.path.join(ROOT, "src", "param_ids.h"), "w") as f:
        f.write("// Generated by tools/gen_params.py -- do not edit. Parameter index constants (VST index = order).\n")
        f.write("#pragma once\n\nenum {\n")
        for i, p in enumerate(P):
            f.write("  P_%s = %d,\n" % (p["key"].upper(), i))
        f.write("  P_COUNT = %d\n};\n\n" % len(P))
        f.write("static const char* const kParamKeys[P_COUNT] = {\n")
        for p in P:
            f.write('  "%s",\n' % p["key"])
        f.write("};\n\nstatic const float kParamMin[P_COUNT] = {")
        f.write(", ".join(repr(float(p.get("min", 0.0))) + "f" for p in P))
        f.write("};\nstatic const float kParamMax[P_COUNT] = {")
        f.write(", ".join(repr(float(p["max"] if "max" in p else len(p["options"]) - 1)) + "f" for p in P))
        f.write("};\nstatic const float kParamDef[P_COUNT] = {")
        f.write(", ".join(repr(float(p["default"])) + "f" for p in P))
        f.write("};\nstatic const unsigned char kParamIsOption[P_COUNT] = {")
        f.write(", ".join("1" if "options" in p else "0" for p in P))
        f.write("};\nstatic const unsigned char kParamReadOnly[P_COUNT] = {")
        f.write(", ".join("1" if p.get("readonly") else "0" for p in P))
        f.write("};\n")
    with open(os.path.join(ROOT, "docs", "regions.json"), "w") as f:
        json.dump({"valuelists": LISTS, "regions": REGIONS}, f, indent=1)
        f.write("\n")
    print("params.json + src/param_ids.h: %d parameters" % len(P))


if __name__ == "__main__":
    main()
