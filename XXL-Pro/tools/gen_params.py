#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Writes everything that follows from tools/spec.py:

    python3 tools/gen_params.py

  params.json        the VST parameter list for mpc-vst-plugins' gen_vst.py (index = order, append-only once shipped)
  src/param_ids.h    P_<KEY> indices and the tables for the engine
  layout.conf        the skin layout (one tab; every page is a when=pg_<view>:1 panel)
  presets.json       the factory presets, cables included (tools/presets.py)
  docs/INVENTORY.md  every control and socket
The generator structure is PhyXXL's.
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec  # noqa: E402
import presets as PRESETS  # noqa: E402

Y0 = 86   # Force Shadow y of the plugin page's top
ENGINE_FAMILIES = ("pg", "fao", "fai", "hao", "hai", "ac")


def trigger(key, name, refresh=True):
    p = {"key": key, "name": name, "min": 0.0, "max": 1.0, "default": 0.0, "momentary": True, "type": "trigger"}
    if refresh:
        p["refresh_display"] = True
    return p


def string_param(key, name):
    return {"key": key, "name": name, "min": 0.0, "max": 0.0, "default": 0.0, "display": "string"}


def opt_param(key, name, options, default=0, **kw):
    p = {"key": key, "name": name, "options": options, "default": default}
    p.update(kw)
    return p


def param_of(c):
    if c["kind"] == "knob":
        p = {"key": c["key"], "name": c["name"], "min": float(c["min"]), "max": float(c["max"]),
             "default": float(c["default"]), "dynamic_display": True}
        if c.get("int"):
            p["display"] = "int"
        if c.get("unit"):
            p["unit"] = c["unit"]
        return p
    return {"key": c["key"], "name": c["name"], "options": c["options"], "default": c["default"]}


def build_params():
    S = spec
    P = [param_of(c) for c in S.CONTROLS]
    fam = {}

    def family(name, items):
        fam[name] = (len(P), len(items))
        P.extend(items)

    P.append(opt_param("view", "View", [v[2] or v[1] for v in S.VIEWS], 0))
    P += [trigger(k, lbl) for k, lbl, _, _ in S.NAV]
    family("go", [trigger("go_" + v[0], "Go " + (v[2] or v[0])) for v in S.VIEWS[1:]])
    P += [trigger("fm_bay", "Patch Bay"), trigger("bay_clear", "Clear All")]
    # page switches: one two-way picture switch per page
    family("pg", [opt_param("pg_" + v[0], "Page " + v[0], S.OFF_ON, 0) for v in S.VIEWS])
    P.append(opt_param("in_sec", "In Section", ["Overview", "Section"], 0))
    P.append(opt_param("in_mod", "In Module", S.OFF_ON, 0))
    P.append(opt_param("in_bay", "In Bay", S.OFF_ON, 0))
    P.append(opt_param("hdr_ti", "Header Value", S.OFF_ON, 0))
    # audio cables: ac_<out>_<in> 1 = patched. The default patch is IN > OUT (the dry cable), so a freshly loaded
    # plugin passes sound; unplug it and the dry signal is gone.
    family("ac", [opt_param("ac_%s_%s" % (a[0], b[0]), "Cable %s to %s" % (a[1], b[1]), S.OFF_ON,
                            1 if (a[0], b[0]) == ("in", "out") else 0, poll=False)
                  for a in S.AUDIO_OUTS for b in S.AUDIO_INS])
    # sockets: 0 plain, 1 fits (ring), 2 blocked (dim)
    family("fao", [opt_param("fao_%d" % i, "Out Socket %d" % i, ["-", "Fits", "Blocked"], 0) for i in range(S.N_AO)])
    family("fai", [opt_param("fai_%d" % i, "In Socket %d" % i, ["-", "Fits", "Blocked"], 0) for i in range(S.N_AI)])

    def ring(prefix, labels):
        return [opt_param("%s_%d" % (prefix, g // S.JACK_GROUP), "Held %s %d" % (prefix, g // S.JACK_GROUP + 1),
                          ["-"] + labels[g:g + S.JACK_GROUP], 0) for g in range(0, len(labels), S.JACK_GROUP)]
    family("hao", ring("hao", [a[1] for a in S.AUDIO_OUTS]))
    family("hai", ring("hai", [b[1] for b in S.AUDIO_INS]))
    P.append(opt_param("pk", "Patch Step", S.PK_STEPS, 0))
    P.append(opt_param("pk_ta", "Socket Taps", S.OFF_ON, 0))
    P.append(opt_param("pk_c", "Patch Cancel Shown", S.OFF_ON, 0))
    P += [trigger(k, n) for k, n in (("pk_cancel", "Patch Cancel"), ("pk_done", "Patch Done"), ("pk_unplug", "Patch Unplug"))]
    family("tao", [trigger("tao_%d" % i, "Socket Out %s" % a[1]) for i, a in enumerate(S.AUDIO_OUTS)])
    family("tai", [trigger("tai_%d" % i, "Socket In %s" % b[1]) for i, b in enumerate(S.AUDIO_INS)])
    for k, n in (("patch_info", "Patch Info"), ("touch_info", "Touch Info"), ("mod_info", "Module Info"), ("cpu_info", "Load")):
        P.append(string_param(k, n))
    family("ts", [string_param("ts_" + k, "Tile " + k) for k in S.TILE_VIEWS])
    P.append(opt_param("m_in", "In Meter", [str(i) for i in range(9)], 0))
    P.append(opt_param("m_out", "Out Meter", [str(i) for i in range(9)], 0))
    P.append(opt_param("m_vu", "Module Meter", [str(i) for i in range(32)], 0))
    P += [{"key": "ql%d" % (i + 1), "name": "Q-Link %d" % (i + 1), "min": 0.0, "max": 1.0, "default": 0.0,
           "dynamic_name": True, "dynamic_display": True} for i in range(16)]
    keys = [p["key"] for p in P]
    assert len(keys) == len(set(keys)), "duplicate keys"
    for name in ("pg", "fao", "fai", "hao", "hai"):
        first, n = fam[name]
        assert all(len(p.get("options", [])) <= 11 for p in P[first:first + n]), name
    return P, fam


def write_params(P):
    secs = []
    for v in spec.VIEWS[1:]:
        ks = [c["key"] for c in spec.CONTROLS if c["view"] == v[0]]
        if ks:
            secs.append({"label": (v[2] or v[0])[:20], "keys": ks})
    with open(os.path.join(ROOT, "params.json"), "w") as f:
        json.dump({"name": "XXL Pro", "params": P, "sections": secs}, f, indent=1)
        f.write("\n")


def cid(k):
    return "P_" + k.upper()


def view_qlinks(v):
    S = spec
    if v[0] == "overview":
        keys = ["out_level", "bypass"]
    elif v[0] == "bay":
        keys = ["dry_level"]
    else:
        keys = [c["key"] for c in S.CONTROLS if c["view"] == v[0]]
    return keys + ["-"] * (16 - len(keys))


def write_header(P, fam):
    S = spec
    L = ["// Generated by tools/gen_params.py from tools/spec.py -- do not edit.", "#pragma once", ""]
    for i, p in enumerate(P):
        L.append("#define %s %d" % (cid(p["key"]), i))
    L.append("#define P_COUNT %d" % len(P))

    def num(p, k, d):
        t = "%.6g" % float(p.get(k, d))
        return t + (".0f" if "." not in t and "e" not in t else "f")
    L.append("static const char *const P_KEY[P_COUNT] = {%s};" % ", ".join('"%s"' % p["key"] for p in P))
    L.append("static const char *const P_NAME[P_COUNT] = {%s};" % ", ".join('"%s"' % p["name"] for p in P))
    L.append("static const char *const P_UNIT[P_COUNT] = {%s};" % ", ".join('"%s"' % p.get("unit", "") for p in P))
    L.append("static const float P_MIN[P_COUNT] = {%s};" % ", ".join(num(p, "min", 0) for p in P))
    L.append("static const float P_MAX[P_COUNT] = {%s};" % ", ".join(
        ("%d.0f" % (len(p["options"]) - 1)) if "options" in p else num(p, "max", 1) for p in P))
    L.append("static const float P_DEF[P_COUNT] = {%s};" % ", ".join(num(p, "default", 0) for p in P))
    L.append("static const unsigned char P_NOPTS[P_COUNT] = {%s};" % ", ".join(str(len(p.get("options", []))) for p in P))
    L.append("static const unsigned char P_INT[P_COUNT] = {%s};" % ", ".join("1" if p.get("display") == "int" else "0" for p in P))
    L.append("#define N_CONTROLS %d   // the sound parameters come first: indices 0..N_CONTROLS-1" % len(S.CONTROLS))
    # the text of each control's steps (toggles: their two options; stepped knobs: their vals)
    for i, c in enumerate(S.CONTROLS):
        t = c.get("vals") or c.get("options")
        if t:
            L.append("static const char *const VALS_%d[] = {%s};" % (i, ", ".join('"%s"' % o for o in t)))
    L.append("static const char *const *const P_VALS[N_CONTROLS] = {%s};" % ", ".join(
        ("VALS_%d" % i) if (c.get("vals") or c.get("options")) else "0" for i, c in enumerate(S.CONTROLS)))
    L.append("")
    for name, (first, n) in fam.items():
        L.append("#define F_%s %d   // first index of the %d '%s' parameters" % (name.upper(), first, n, name))
        L.append("#define N_%s %d" % (name.upper(), n))
    L.append("")
    for i, v in enumerate(S.VIEWS):
        L.append("#define V_%s %d" % (v[0].upper(), i))
    L.append("#define N_VIEWS %d" % len(S.VIEWS))
    L.append("#define N_MOD %d" % S.N_MOD)
    L.append("#define N_AO %d" % S.N_AO)
    L.append("#define N_AI %d" % S.N_AI)
    L.append("#define JACK_GROUP %d" % S.JACK_GROUP)
    L.append("#define N_TILES %d" % len(S.TILE_VIEWS))
    L.append("#define COST_BUDGET %d" % S.COST_BUDGET)
    for i, m in enumerate(S.MODULES):
        L.append("#define M_%s %d" % (m[0][1:].upper(), i))
    L.append("static const char *const MOD_NAME[N_MOD] = {%s};" % ", ".join('"%s"' % m[1] for m in S.MODULES))
    L.append("static const unsigned char MOD_COST[N_MOD] = {%s};" % ", ".join(str(m[5]) for m in S.MODULES))
    L.append("static const unsigned char MOD_IS_REVERB[N_MOD] = {%s};" % ", ".join("1" if m[4] == "rev" else "0" for m in S.MODULES))
    L.append("static const unsigned char MOD_IS_TAPE[N_MOD] = {%s};" % ", ".join("1" if m[0] in ("ma8", "mat") else "0" for m in S.MODULES))
    L.append("static const unsigned char MOD_IS_COMP[N_MOD] = {%s};" % ", ".join("1" if m[4] == "comp" else "0" for m in S.MODULES))
    L.append("static const char *const AO_LABEL[N_AO] = {%s};" % ", ".join('"%s"' % a[1] for a in S.AUDIO_OUTS))
    L.append("static const char *const AI_LABEL[N_AI] = {%s};" % ", ".join('"%s"' % b[1] for b in S.AUDIO_INS))
    L.append("")
    L.append("// the views' controls in Q-Link order (reading order): up to 16 per view, -1 = none")
    L.append("static const short VIEW_QLINKS[N_VIEWS][16] = {")
    for v in S.VIEWS:
        L.append("    {%s}," % ", ".join(cid(k) if k != "-" else "-1" for k in view_qlinks(v)))
    L.append("};")
    L.append("")
    with open(os.path.join(ROOT, "src", "param_ids.h"), "w") as f:
        f.write("\n".join(L))


# ------------------------------------------------------------------------------------------------ layout.conf
# Text: the Meta4MPCXXL standard (scale_names=1, label_scale=1.7: control names and values about 36 px, nothing under 26).
THEME = """scale_names=1
label_scale=1.7
theme_bg=24221e
theme_panel=24221e
theme_line=6c6a66
theme_ink=ffffff
theme_ink_dim=ffffff
theme_ink_faint=ffffff
theme_accent=6c6a66
theme_accent_hi=ffffff
theme_knob_face=d9d9e3
theme_knob_ring=101011
theme_knob_dot=111111
theme_bar=24221e
theme_seg_active=ffffff
theme_seg_inactive=101011
theme_seg_active_tx=111111
theme_btn_text=ffffff
theme_tab_on=ffffff
theme_tab_on_tx=111111
theme_lcd=101011
theme_box=101011"""


def layout_line(c):
    v = "when=pg_%s:1" % c["view"]
    x, y = c["cx"], c["cy"] + Y0
    name = c.get("label", c["name"]).upper()
    if c.get("widget") == "fader":
        return 'slider_v cx=%d cy=%d w=%d h=%d label="%s" key=%s ns=36 vs=37 bw=%d %s' % (x, y, c["w"], c["h"], name, c["key"], c.get("bw", spec.COL_DX - 6), v)
    if c.get("side"):
        return 'knob cx=%d cy=%d r=%d lay=side bw=%d bh=%d vs=30 label="%s" key=%s %s' % (
            x, y, c["side"][2], c["side"][0], c["side"][1], name, c["key"], v)
    if c.get("widget") == "fader":
        return 'slider_v cx=%d cy=%d w=%d h=%d label="%s" key=%s ns=36 vs=37 bw=%d %s' % (x, y, c["w"], c["h"], name, c["key"], c.get("bw", spec.COL_DX - 6), v)
    if c["kind"] == "knob":
        return 'knob cx=%d cy=%d r=%d label="%s" key=%s bw=%d %s' % (x, y, (c.get("tile", 126) - 10) // 2, name, c["key"],
                                                                       c.get("bw", spec.COL_DX - 6), v)
    return 'toggle cx=%d cy=%d label="%s" key=%s bw=%d %s' % (x, y, name, c["key"], c.get("bw", spec.COL_DX - 6), v)


def write_layout():
    S = spec
    L = ["# XXL Pro page layout. GENERATED by tools/gen_params.py from tools/spec.py -- edit spec.py, not this.",
         "# One tab; each page is a panel shown while its pg_<view> switch is on. The overview tiles, the sockets, cables",
         "# and buttons are placed and drawn by tools/post_skin.py. FIRST FUNCTIONAL LAYOUT: nothing here is final.",
         THEME,
         "qlinks_track = " + ",".join("ql%d" % (i + 1) for i in range(16)),
         "", "[tab XXL Pro]"]
    for k, lbl, x, y in S.NAV:
        L.append('button cx=%d cy=%d label="%s" key=%s when=in_sec:1' % (x, y + Y0, lbl, k))
    k, lbl, x, y, w, h = S.BAY_BTN
    L.append('button cx=%d cy=%d label="%s" key=%s when=in_mod:1' % (x, y + Y0, lbl, k))
    k, lbl, x, y, w, h = S.BAY_CLEAR
    L.append('button cx=%d cy=%d label="%s" key=%s when=pk_ta:1' % (x, y + Y0, lbl, k))
    for k in S.TILE_VIEWS:
        x, y, w, h = S.TILES[k]
        L.append('button cx=%d cy=%d label="" key=go_%s when=pg_overview:1' % (x + w // 2, y + h // 2 + Y0, k))
    for k in S.TILE_VIEWS:
        x, y, w, h = S.TILES[k]
        L.append('readout cx=%d cy=%d w=%d h=36 label="" key=ts_%s box=0 tsize=26 talign=left when=pg_overview:1' % (
            x + 14 + (w - 28) // 2, y + 82 + Y0, w - 28, k))
    L.append('readout cx=636 cy=%d w=232 h=40 label="" key=cpu_info box=0 tsize=28 talign=left when=pg_overview:1' % (S.STRIP_Y + 40 + Y0))
    for i in range(S.N_AO):
        x, y = S.aud_out_pos(i)
        L.append('button cx=%d cy=%d label="" key=tao_%d when=pk_ta:1' % (x, y + Y0, i))
    for i in range(S.N_AI):
        x, y = S.aud_in_pos(i)
        L.append('button cx=%d cy=%d label="" key=tai_%d when=pk_ta:1' % (x, y + Y0, i))
    L.append('button cx=%d cy=%d label="CANCEL" key=pk_cancel when=pk_c:1' % (S.PK_CANCEL[0], S.PK_CANCEL[1] + Y0))
    for key, lbl, b in (("pk_unplug", "UNPLUG", S.PK_UNPLUG), ("pk_done", "DONE", S.PK_DONE)):
        L.append('button cx=%d cy=%d label="%s" key=%s when=pk:4' % (b[0] + b[2] // 2, b[1] + b[3] // 2 + Y0, lbl, key))
    L.append('readout cx=420 cy=%d w=800 h=44 label="" key=patch_info box=0 tsize=28 talign=left when=in_bay:1' % (S.BAY_INFO_Y + Y0))
    L.append('readout cx=%d cy=%d w=%d h=44 label="" key=touch_info box=0 tsize=28 talign=right when=hdr_ti:1' % (
        S.HDR_TOUCH[0], S.HDR_TOUCH[1] + Y0, S.HDR_TOUCH[2]))
    L.append('readout cx=800 cy=%d w=290 h=44 label="" key=mod_info box=0 tsize=28 talign=left when=in_mod:1' % (28 + Y0))
    for c in S.CONTROLS:
        L.append(layout_line(c))
    L.append('qlinks "XXL Pro" = ' + ",".join("ql%d" % (i + 1) for i in range(16)))
    with open(os.path.join(ROOT, "layout.conf"), "w") as f:
        f.write("\n".join(L) + "\n")


def write_inventory():
    S = spec
    L = ["# XXL Pro inventory", "", "Every control and socket, generated from `tools/spec.py`.", ""]
    for v in S.VIEWS[1:]:
        cs = [c for c in S.CONTROLS if c["view"] == v[0]]
        if not cs:
            continue
        L += ["## " + v[1], "", "| Control | Key | Range |", "|---|---|---|"]
        for c in cs:
            if c.get("vals"):
                rng = " / ".join(c["vals"])
            elif c["kind"] == "knob":
                rng = "%g .. %g %s" % (c["min"], c["max"], c.get("unit", ""))
            else:
                rng = " / ".join(c["options"])
            L.append("| %s | `%s` | %s |" % (c["name"], c["key"], rng.strip()))
        L.append("")
    L += ["## Patch bay", "", "Outputs: " + ", ".join(a[1] for a in S.AUDIO_OUTS) + ".", "",
          "Inputs: " + ", ".join(b[1] for b in S.AUDIO_INS) + ".", "",
          "Any output into any input; one cable carries left and right; an input sums its cables; a module into "
          "itself, or a loop through other modules, is refused. Cables are parameters `ac_<out>_<in>`, saved with presets.",
          "", "%d controls, %d cables possible." % (len(S.CONTROLS), S.N_AO * S.N_AI - S.N_MOD), ""]
    with open(os.path.join(ROOT, "docs", "INVENTORY.md"), "w") as f:
        f.write("\n".join(L))


def write_presets():
    S = spec
    outs, ins = [a[0] for a in S.AUDIO_OUTS], [b[0] for b in S.AUDIO_INS]
    out = []
    for name, over, audio in PRESETS.PRESETS:
        vals = {}
        for k in over:
            assert k in S.CTRL, "preset %s: unknown control %s" % (name, k)
        for c in S.CONTROLS:
            v = over.get(c["key"], c["default"])
            if c.get("vals") and isinstance(v, str):
                v = c["vals"].index(v)
            if c["kind"] == "toggle":
                v = c["options"][int(v)] if not isinstance(v, str) else v
                assert v in c["options"], (name, c["key"], v)
            else:
                assert c["min"] <= v <= c["max"], (name, c["key"], v)
            vals[c["key"]] = v
        aud = set(audio)
        cost = sum(m[5] for m in S.MODULES if any(a == m[0] for a, _ in aud) and any(b == m[0] for _, b in aud))
        assert cost <= S.COST_BUDGET, (name, cost)
        for (a, b) in aud:
            assert a in outs and b in ins and a != b, (name, a, b)
        for a in outs:
            for b in ins:
                vals["ac_%s_%s" % (a, b)] = "On" if (a, b) in aud else "Off"
        out.append({"name": name, "values": vals})
    with open(os.path.join(ROOT, "presets.json"), "w") as f:
        json.dump({"presets": out}, f, indent=1)
        f.write("\n")
    return len(out)


def main():
    P, fam = build_params()
    write_params(P)
    write_header(P, fam)
    write_layout()
    write_inventory()
    n = write_presets()
    print("gen_params: %d parameters (%d controls), %d presets" % (len(P), len(spec.CONTROLS), n))


if __name__ == "__main__":
    main()
