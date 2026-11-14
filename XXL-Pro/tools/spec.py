# SPDX-License-Identifier: GPL-3.0-or-later
"""XXL Pro ("Pro" is for Process): the one source of truth for every module, control, view, socket and position.

Everything else is generated from this file:
  tools/gen_params.py  -> params.json, src/param_ids.h, layout.conf, presets.json, docs/INVENTORY.md
  tools/post_skin.py   -> overview tiles, patch bay sockets and cables, buttons (reads the built skin + this file)

MPC stores automation and saved values by parameter INDEX, so once a version ships the parameter list is append-only.
Coordinates are skin pixels: the plugin page is 1280 x 628 (layout.conf adds 86 to y, the Force Shadow offset).

One plugin, fifteen process modules. Any module's output can be patched into any other module's input and into the
main output; an input sums its cables; a loop is refused; one cable carries left and right. There is no built-in dry
path: dry runs only while IN is patched to OUT. The page structure and the patch bay are PhyXXL's.

FIRST FUNCTIONAL LAYOUT (0.1.0): art, tiles and the final control placement come in the art phase (Panel Editor).
"""
OFF_ON = ["Off", "On"]

# (key, name on the panel, socket name, page title, kind, static cost in percent of one audio block -- UNMEASURED
#  placeholders until a bench run on the Force; the live guard is what protects the audio until then)
MODULES = [
    ("m2a", "XXL-2A", "2A", "XXL-2A  /  OPTICAL LEVELLER", "comp", 4),
    ("m1b", "XXL-1B", "1B", "XXL-1B  /  TUBE OPTICAL COMPRESSOR", "comp", 4),
    ("m16", "XXL-16VU", "16VU", "XXL-16VU  /  VCA COMPRESSOR", "comp", 4),
    ("m76", "XXL-76", "76", "XXL-76  /  FET LIMITER", "comp", 5),
    ("m67", "XXL-67", "67", "XXL-67  /  VARIABLE-MU LIMITER", "comp", 5),
    ("mds", "XXL-DISS", "DISS", "XXL-DISS  /  COMPRESSOR", "comp", 5),
    ("m73", "XXL-73", "73", "XXL-73  /  PREAMP AND EQ", "eq", 4),
    ("m55", "XXL-55A", "55A", "XXL-55A  /  3-BAND EQ", "eq", 3),
    ("m56", "XXL-56", "56", "XXL-56  /  10-BAND GRAPHIC EQ", "eq", 5),
    ("mq1", "XXL-EQ1-A", "EQ1-A", "XXL-EQ1-A  /  PROGRAM EQ", "eq", 3),
    ("mq5", "XXL-MQ-5", "MQ-5", "XXL-MQ-5  /  MID EQ", "eq", 3),
    ("ma8", "XXL-A80", "A80", "XXL-A80  /  MULTITRACK TAPE", "tape", 7),
    ("mat", "XXL-AT12", "AT12", "XXL-AT12  /  MASTER TAPE", "tape", 7),
    ("m22", "XXL-224", "224", "XXL-224  /  REVERB", "rev", 12),
    ("m48", "XXL-480R", "480R", "XXL-480R  /  REVERB", "rev", 14),
]
MKEYS = [m[0] for m in MODULES]
N_MOD = len(MODULES)
COST_BUDGET = 100   # the sum of the costs of the modules in the signal path may not pass this

# ---------------------------------------------------------------------------------------------------------- views
VIEWS = [("overview", "XXL Pro", "")] + [(m[0], m[1], m[1]) for m in MODULES] + [("bay", "PATCH BAY", "PATCH BAY")]
VIEW_KEYS = [v[0] for v in VIEWS]
N_VIEWS = len(VIEWS)

# overview: 4 x 4 tiles (15 modules + PATCH BAY), a strip below for the meters, the load and BYPASS
_TW, _TH, _GX, _GY, _TX, _TY = 309, 113, 9, 6, 13, 67
TILE_VIEWS = MKEYS + ["bay"]
TILES = {k: (_TX + (i % 4) * (_TW + _GX), _TY + (i // 4) * (_TH + _GY), _TW, _TH) for i, k in enumerate(TILE_VIEWS)}
STRIP_Y = 548

# ------------------------------------------------------------------------------------------------- the controls
# Six columns, three rows of knobs and switches per module page, filled in list order (Q-Link order = reading order).
# Big knobs with their dial (tick ring), two rows per page. A knob picture is KNOB_TILE px (the rendered knob with its
# shadow margin); the knob itself is 0.86 of that and the dial around it 1.63 x 1.51 of the tile / 1.0 (the user's
# tick-ring art: 163 x 151 px around an 86 px knob). Pages with more than 12 cells use seven narrower columns.
ROW_Y = [160, 446]           # knob centres (skin y)
KNOB_TILE = {6: 126, 7: 104}
KNOB_R = 58
COLS, COL_X0, COL_DX = 6, 112, 211   # (kept for the generators' box widths)
CONTROLS = []


def _place(view):
    return 0, 0   # set for every module further down (MODULE_COLS)


def K(key, name, lo, hi, de, view, unit="", intd=False, vals=None):
    """a knob; vals = the text of each step (a stepped selector shown as a knob)"""
    cx, cy = _place(view)
    if vals:
        lo, hi, intd = 0, len(vals) - 1, True
    CONTROLS.append(dict(key=key, name=name, kind="knob", min=lo, max=hi, default=de, view=view, cx=cx, cy=cy,
                         unit=unit, int=intd, vals=vals))


def T(key, name, de, view, options=OFF_ON):
    cx, cy = _place(view)
    CONTROLS.append(dict(key=key, name=name, kind="toggle", options=options, default=de, view=view, cx=cx, cy=cy))


# parameter 0 first: MPC's host toggles parameter 0 on insert and stop, so it is the plain OUTPUT level
CONTROLS.append(dict(key="out_level", name="Output", kind="knob", min=-24, max=12, default=0, view="overview",
                     cx=965, cy=STRIP_Y + 40, unit="dB", int=False, vals=None, side=(170, 70, 30)))

LINK = ["Dual", "Linked"]
# ---- XXL-2A
K("m2a_peak", "Peak Red", 0, 100, 30, "m2a"); K("m2a_gain", "Gain", 0, 100, 40, "m2a")
T("m2a_mode", "Limit", 0, "m2a", ["Compress", "Limit"]); K("m2a_emph", "SC Emph", 0, 100, 0, "m2a")
T("m2a_link", "Linked", 1, "m2a", LINK)
# ---- XXL-1B
K("m1b_thr", "Thresh", -40, 20, 20, "m1b", unit="dBu"); K("m1b_gain", "Gain", 0, 30, 0, "m1b", unit="dB")
K("m1b_ratio", "Ratio", 2, 10, 4, "m1b"); K("m1b_time", "Timing", 0, 2, 0, "m1b", vals=["Fixed", "Manual", "Fix-Man"])
K("m1b_att", "Attack", 0, 10, 5, "m1b"); K("m1b_rel", "Release", 0, 10, 5, "m1b")
T("m1b_link", "Linked", 1, "m1b", LINK)
# ---- XXL-16VU   (threshold: 0..100 is 0.01 .. 3 V RMS on a log scale)
K("m16_thr", "Thresh", 0, 100, 100, "m16"); K("m16_ratio", "Ratio", 0, 100, 40, "m16")
K("m16_out", "Output", -20, 20, 0, "m16", unit="dB"); T("m16_link", "Linked", 1, "m16", LINK)
# ---- XXL-76
K("m76_in", "Input", 0, 100, 24, "m76"); K("m76_out", "Output", 0, 100, 50, "m76")
K("m76_att", "Attack", 1, 7, 3, "m76", intd=True); K("m76_rel", "Release", 1, 7, 5, "m76", intd=True)
K("m76_ratio", "Ratio", 0, 5, 1, "m76", vals=["Amp only", "4:1", "8:1", "12:1", "20:1", "All"])
T("m76_rev", "Rev B", 0, "m76", ["Rev A", "Rev B"]); T("m76_link", "Linked", 1, "m76", LINK)
# ---- XXL-67
K("m67_in", "In Gain", -10.8, 9.2, 0, "m67", unit="dB"); K("m67_thr", "Thresh", 0, 100, 0, "m67")
K("m67_tc", "Time Con", 1, 6, 2, "m67", intd=True); K("m67_out", "Out Gain", -12, 12, 0, "m67", unit="dB")
T("m67_ms", "Lat-Vert", 0, "m67", ["Left-Right", "Lat-Vert"]); T("m67_link", "Linked", 1, "m67", LINK)
# ---- XXL-DISS
K("mds_in", "Input", 0, 10.5, 5, "mds"); K("mds_att", "Attack", 0, 10.5, 5, "mds"); K("mds_rel", "Release", 0, 10.5, 5, "mds")
K("mds_out", "Output", 0, 10.5, 5, "mds")
K("mds_ratio", "Ratio", 0, 7, 0, "mds", vals=["1:1", "2:1", "3:1", "4:1", "6:1", "10:1", "20:1", "MAX"])
K("mds_det", "Detector", 0, 2, 0, "mds", vals=["Norm", "HP", "Emp"])
K("mds_aud", "Audio", 0, 3, 0, "mds", vals=["Norm", "HP", "Dist 2", "Dist 3"]); T("mds_link", "Linked", 1, "mds", LINK)
# ---- XXL-73
K("m73_gain", "Gain", -10, 30, 0, "m73", unit="dB"); K("m73_out", "Output", -30, 10, 0, "m73", unit="dB")
K("m73_hpf", "Hi-Pass", 0, 4, 0, "m73", vals=["Off", "50 Hz", "80 Hz", "160 Hz", "300 Hz"])
K("m73_lf", "Low Frq", 0, 4, 0, "m73", vals=["Off", "35 Hz", "60 Hz", "110 Hz", "220 Hz"])
K("m73_lg", "Low", -16, 16, 0, "m73", unit="dB")
K("m73_mf", "Mid Frq", 0, 6, 0, "m73", vals=["Off", "360 Hz", "700 Hz", "1.6 kHz", "3.2 kHz", "4.8 kHz", "7.2 kHz"])
K("m73_mg", "Mid", -18, 18, 0, "m73", unit="dB"); K("m73_hg", "High", -18, 18, 0, "m73", unit="dB")
T("m73_eq", "EQ In", 1, "m73"); T("m73_ph", "Phase", 0, "m73")
# ---- XXL-55A
G55 = ["-12 dB", "-9 dB", "-6 dB", "-4 dB", "-2 dB", "0 dB", "+2 dB", "+4 dB", "+6 dB", "+9 dB", "+12 dB"]
K("m55_lf", "Low Frq", 0, 4, 1, "m55", vals=["50 Hz", "100 Hz", "200 Hz", "300 Hz", "400 Hz"])
K("m55_lg", "Low", 0, 10, 5, "m55", vals=G55); T("m55_lb", "Low Bell", 0, "m55", ["Shelf", "Bell"])
K("m55_mf", "Mid Frq", 0, 4, 2, "m55", vals=["400 Hz", "800 Hz", "1.5 kHz", "3 kHz", "5 kHz"])
K("m55_mg", "Mid", 0, 10, 5, "m55", vals=G55)
K("m55_hf", "High Frq", 0, 4, 2, "m55", vals=["5 kHz", "7 kHz", "10 kHz", "12.5 kHz", "15 kHz"])
K("m55_hg", "High", 0, 10, 5, "m55", vals=G55); T("m55_hb", "High Bell", 0, "m55", ["Shelf", "Bell"])
T("m55_flt", "Filter", 0, "m55"); T("m55_eq", "EQ In", 1, "m55"); T("m55_ph", "Phase", 0, "m55")
K("m55_out", "Output", -24, 12, 0, "m55", unit="dB")
# ---- XXL-56
BANDS56 = [31, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
for _i, _f in enumerate(BANDS56):
    K("m56_b%d" % (_i + 1), ("%d Hz" % _f) if _f < 1000 else ("%d kHz" % (_f // 1000)), -12, 12, 0, "m56", unit="dB")
T("m56_eq", "EQ In", 1, "m56"); T("m56_rng", "6 dB Rng", 0, "m56", ["12 dB", "6 dB"])
K("m56_out", "Output", -24, 12, 0, "m56", unit="dB")
# ---- XXL-EQ1-A
K("mq1_lf", "Low Frq", 0, 3, 2, "mq1", vals=["20 Hz", "30 Hz", "60 Hz", "100 Hz"])
K("mq1_lb", "Low Boost", 0, 10, 0, "mq1"); K("mq1_la", "Low Atten", 0, 10, 0, "mq1")
K("mq1_hf", "High Frq", 0, 6, 3, "mq1", vals=["3 kHz", "4 kHz", "5 kHz", "8 kHz", "10 kHz", "12 kHz", "16 kHz"])
K("mq1_hb", "Hi Boost", 0, 10, 0, "mq1"); K("mq1_bw", "Bandwidth", 0, 10, 5, "mq1")
K("mq1_af", "Atten Sel", 0, 2, 1, "mq1", vals=["5 kHz", "10 kHz", "20 kHz"]); K("mq1_ha", "Hi Atten", 0, 10, 0, "mq1")
T("mq1_in", "EQ In", 1, "mq1"); K("mq1_out", "Output", -24, 12, 0, "mq1", unit="dB")
# ---- XXL-MQ-5
K("mq5_lf", "Low Frq", 0, 4, 2, "mq5", vals=["200 Hz", "300 Hz", "500 Hz", "700 Hz", "1 kHz"])
K("mq5_lb", "Low Peak", 0, 10, 0, "mq5")
K("mq5_df", "Dip Frq", 0, 10, 4, "mq5", vals=["200 Hz", "300 Hz", "500 Hz", "700 Hz", "1 kHz", "1.5 kHz", "2 kHz",
                                               "3 kHz", "4 kHz", "5 kHz", "7 kHz"])
K("mq5_dp", "Dip", 0, 10, 0, "mq5")
K("mq5_hf", "High Frq", 0, 4, 1, "mq5", vals=["1.5 kHz", "2 kHz", "3 kHz", "4 kHz", "5 kHz"])
K("mq5_hb", "High Peak", 0, 10, 0, "mq5"); T("mq5_in", "EQ In", 1, "mq5"); K("mq5_out", "Output", -24, 12, 0, "mq5", unit="dB")
# ---- the two tape modules
TAPES = ["Type 1", "Type 2", "Type 3", "Type 4"]
for _m, _speeds, _sd in (("ma8", ["7.5 ips", "15 ips", "30 ips"], 1), ("mat", ["3.75 ips", "7.5 ips", "15 ips", "30 ips"], 2)):
    K(_m + "_in", "Rec Level", -12, 12, 0, _m, unit="dB"); K(_m + "_out", "Repro Lvl", -12, 12, 0, _m, unit="dB")
    K(_m + "_spd", "Speed", 0, 0, _sd, _m, vals=_speeds); K(_m + "_type", "Tape", 0, 3, 1, _m, vals=TAPES)
    K(_m + "_bias", "Bias", -6, 6, 0, _m, unit="dB"); K(_m + "_rhf", "Rec HF", -6, 6, 0, _m, unit="dB")
    K(_m + "_phf", "Repro HF", -6, 6, 0, _m, unit="dB"); K(_m + "_plf", "Repro LF", -6, 6, 0, _m, unit="dB")
    K(_m + "_wow", "Wow", 0, 100, 0, _m, unit="%"); K(_m + "_flut", "Flutter", 0, 100, 0, _m, unit="%")
    T(_m + "_hiss", "Hiss", 0, _m); T(_m + "_path", "Tape In", 1, _m, ["Thru", "Repro"])
    if _m == "mat":
        K("mat_head", "Head", 0, 2, 1, "mat", vals=["Narrow", "Middle", "Wide"])
# ---- XXL-224 (our own programs; fully wet: dry is a cable)
P224 = ["Small Hall", "Bright Hall", "Large Hall", "Room", "Chamber", "Plate A", "Plate B", "Plate C", "Chorus"]
K("m22_prog", "Program", 0, 8, 0, "m22", vals=P224)
K("m22_bass", "Bass", 0, 100, 34, "m22"); K("m22_mid", "Mid", 0, 100, 29, "m22")      # 0.6 .. 70 s, log
K("m22_xov", "Crossover", 0, 100, 40, "m22"); K("m22_treb", "Treble", 0, 100, 75, "m22")   # 100 Hz .. 10.9 kHz, log
K("m22_depth", "Depth", 0, 71, 0, "m22", intd=True); K("m22_pre", "Predelay", 0, 256, 0, "m22", unit="ms", intd=True)
K("m22_diff", "Diffusion", 1, 63, 40, "m22", intd=True); T("m22_mod", "Movement", 1, "m22")
K("m22_lvl", "Level", -24, 12, 0, "m22", unit="dB")
# ---- XXL-480R (our own programs; fully wet)
P480 = ["Small Hall", "Medium Hall", "Large Hall", "Dark Hall", "Small Room", "Large Room", "Wood Room", "Chamber",
        "Bright Plate", "Dark Plate", "Random Hall", "Random Space", "Ambience", "Tight Amb", "Post Amb", "Wide Space"]
K("m48_prog", "Program", 0, 15, 1, "m48", vals=P480)
K("m48_rt", "Rev Time", 0, 100, 40, "m48"); K("m48_shape", "Shape", 0, 100, 50, "m48")     # 0.3 .. 30 s, log
K("m48_spread", "Spread", 0, 100, 50, "m48"); K("m48_size", "Size", 0, 100, 60, "m48")
K("m48_hfc", "HF Cut", 0, 100, 80, "m48"); K("m48_pre", "Predelay", 0, 250, 0, "m48", unit="ms", intd=True)   # 500 Hz .. 20 kHz
K("m48_bm", "Bass Mult", 0, 100, 50, "m48"); K("m48_xov", "Crossover", 0, 100, 40, "m48")    # x0.25 .. x4; 100 Hz .. 5 kHz
K("m48_rthc", "RT HF Cut", 0, 100, 60, "m48"); K("m48_diff", "Diffusion", 0, 100, 70, "m48")
K("m48_spin", "Spin", 0, 100, 30, "m48"); K("m48_wand", "Wander", 0, 100, 30, "m48")
K("m48_lvl", "Level", -24, 12, 0, "m48", unit="dB")
# ---- overview strip
T("bypass", "Bypass", 0, "overview")
CONTROLS[-1].update(cx=1193, cy=STRIP_Y + 6, bw=150)
# ---- patch bay: the level of the dry cable (IN > OUT); fully down = off
CONTROLS.append(dict(key="dry_level", name="Dry Level", kind="knob", min=-60, max=12, default=0, view="bay",
                     cx=1120, cy=592, unit="dB", int=False, vals=None, side=(240, 64, 28)))
CTRL = {c["key"]: c for c in CONTROLS}

# ---- where the controls sit until the Panel Editor says otherwise: knobs fill the cells in order (left to right, two
# rows), then the ON/OFF buttons, two stacked in a cell
# Faders (with the slider caps) where the unit itself has faders: the ten bands of XXL-56 and the first six
# controls of the two reverbs.
FADERS = ["m56_b%d" % (i + 1) for i in range(10)] + ["m22_bass", "m22_mid", "m22_xov", "m22_treb", "m22_depth", "m22_pre"] + \
         ["m48_rt", "m48_shape", "m48_spread", "m48_size", "m48_hfc", "m48_pre"]
for _k in FADERS:
    CTRL[_k].update(widget="fader", w=78, h=170)
VU_CELLS = {"m2a": 2, "m1b": 2, "m16": 2, "m76": 2, "m67": 2, "ma8": 2, "mat": 1}   # the units with a VU meter
METERS = {}
MODULE_COLS = {}
for _m in MKEYS:
    if _m == "m56":   # ten faders in one row, the two buttons and OUTPUT under them
        MODULE_COLS[_m] = 10
        for _i in range(10):
            CTRL["m56_b%d" % (_i + 1)].update(cx=64 + 128 * _i, cy=162, w=78, h=190, bw=124)
        CTRL["m56_eq"].update(cx=200, cy=466, bw=220)
        CTRL["m56_rng"].update(cx=460, cy=466, bw=220)
        CTRL["m56_out"].update(cx=1100, cy=ROW_Y[1], tile=126, bw=207)
        continue
    _kn = [c for c in CONTROLS if c["view"] == _m and c["kind"] == "knob"]
    _tg = [c for c in CONTROLS if c["view"] == _m and c["kind"] == "toggle"]
    _cells = len(_kn) + len(_tg) + VU_CELLS.get(_m, 0)   # one key per cell, and room for the meter
    _cols = 6 if _cells <= 12 else 7
    assert _cells <= 2 * _cols, (_m, _cells)
    MODULE_COLS[_m] = _cols
    _dx = 1280.0 / _cols
    for _i, _c in enumerate(_kn):
        _c.update(cx=int(_dx * (_i % _cols) + _dx / 2), cy=ROW_Y[_i // _cols] - (9 if _c.get("widget") == "fader" else 0),
                  tile=KNOB_TILE[_cols], bw=int(_dx) - 6)
    if _m in VU_CELLS:   # the VU dial: the last cell(s) of the lower row
        _n = VU_CELLS[_m]
        METERS[_m] = ("vu", int(1280 - _dx * _n / 2), ROW_Y[1], 340 if _n == 2 else 176)
    if _m == "mds":      # the gain reduction lamps: the free cells of the lower row
        METERS[_m] = ("lamps", int(1280 - _dx * 2), ROW_Y[1], 640)
    for _j, _c in enumerate(_tg):
        _i = len(_kn) + _j
        _c.update(cx=int(_dx * (_i % _cols) + _dx / 2), cy=ROW_Y[_i // _cols], bw=int(_dx) - 6)

# ---- faceplates: each module's panel takes the colour of the unit's front panel in the manual (panel, ink, file name).
# Units with a black panel keep the plain dark page. Two units of the same colour share one picture.
_DARK, _LIGHT = (20, 20, 20), (255, 255, 255)
FACE = {"m2a": ((203, 197, 184), _DARK, "cream"), "m1b": ((24, 62, 126), _LIGHT, "blue"), "m73": ((40, 54, 74), _LIGHT, "navy"),
        "m55": ((42, 44, 48), _LIGHT, "charcoal"), "m56": ((42, 44, 48), _LIGHT, "charcoal"),
        "mq1": ((24, 84, 110), _LIGHT, "teal"), "mq5": ((24, 84, 110), _LIGHT, "teal"),
        "ma8": ((200, 200, 198), _DARK, "silver"), "mat": ((200, 200, 198), _DARK, "silver")}
FACE_Y = (58, 628)

# ---- knob cap colours (tools/knob_render.py's six): each module's knobs take the colour of the unit it stands for
# ("WHITE x" = the off-white ring, used where the unit's own knobs have a white / silver ring; black ring elsewhere)
KNOB_COLOUR = {"m2a": "BLACK", "m1b": "BLACK", "m16": "WHITE GREY", "m76": "BLACK", "m67": "BLACK", "mds": "BLACK",
               "m73": "BLUE", "m55": "WHITE BLUE", "m56": "WHITE GREY", "mq1": "BLACK", "mq5": "BLACK", "ma8": "WHITE GREY", "mat": "BLACK",
               "m22": "BLACK", "m48": "WHITE GREY", "overview": "WHITE GREY", "bay": "WHITE GREY"}
KNOB_COLOUR_KEY = {"m73_gain": "RED", "m73_out": "GREY", "m73_hg": "GREY", "m56_b6": "WHITE RED"}   # the exceptions
for _c in CONTROLS:
    _c["colour"] = KNOB_COLOUR_KEY.get(_c["key"], KNOB_COLOUR[_c["view"]])
    if _c.get("widget") == "fader":   # slider caps come in the six colours only
        _c["colour"] = _c["colour"].replace("WHITE ", "")

# ---- the Panel Editor's layout file (layout.json, made with XXL-Pro-Panel-Editor.html): where YOU put each control.
# Per control: x, y (centre), r (knob radius), type (knob / fader / switch), label (the name shown), w, h (fader).
# Plus free text labels and a background picture per page. Controls not in the file keep the positions above.
import json as _json
import os as _os
LAYOUT_FILE = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "layout.json")
LAYOUT = _json.load(open(LAYOUT_FILE)) if _os.path.isfile(LAYOUT_FILE) else {}
for _k, _o in LAYOUT.get("controls", {}).items():
    if _k not in CTRL:
        continue
    _c = CTRL[_k]
    _c["cx"], _c["cy"] = int(_o.get("x", _c["cx"])), int(_o.get("y", _c["cy"]))
    if "label" in _o:
        _c["label"] = str(_o["label"])
    if _c["kind"] == "knob" and "side" not in _c:
        _c["r"] = int(_o.get("r", KNOB_R))
        pass
EXTRA_LABELS = LAYOUT.get("labels", [])     # [{view, x, y, size, text}]
PAGE_ART = LAYOUT.get("art", {})            # {view: file name in art/panels/}
assert CONTROLS[0]["key"] == "out_level"
assert len(CTRL) == len(CONTROLS)
for _m in MKEYS:
    assert sum(1 for c in CONTROLS if c["view"] == _m) <= 16, _m

# ------------------------------------------------------------------------------------------------ navigation
NAV = [("nav_zoom", "OVERVIEW", 96, 28), ("nav_prev", "<", 208, 28), ("nav_next", ">", 264, 28)]
NAV_SIZE = {"nav_zoom": (160, 44), "nav_prev": (48, 44), "nav_next": (48, 44)}
BAY_BTN = ("fm_bay", "PATCH BAY", 392, 28, 180, 44)   # on every module page
HDR_TOUCH = (1112, 28, 316)   # the readout at the top right: the touched control and its value
TITLE_X = 500                 # the page title starts here (after the header buttons)

# --------------------------------------------------------------------------------------------- patch bay sockets
JACK_GROUP = 9   # picture switches have at most JACK_GROUP + 1 positions (the Force: nothing above 11 seen working)
JACK_R = 17
AUDIO_OUTS = [("in", "IN")] + [(m[0], m[2]) for m in MODULES]
AUDIO_INS = [(m[0], m[2]) for m in MODULES] + [("out", "OUT")]
N_AO, N_AI = len(AUDIO_OUTS), len(AUDIO_INS)
# Sockets sit in groups with a heading, the same on both sides: three columns, eight rows.
#   column 0: COMPRESSOR     column 1: EQ, then MAIN (IN on the output side, OUT on the input side)     column 2: TAPE, REVERB
BAY_Y0, BAY_DY = 84, 56
AO_X = (145, 310, 490)            # output columns: the name left of the socket
AI_X = (790, 970, 1135)           # input columns: the name right of the socket
BAY_GROUPS = [(0, 0, "COMPRESSOR"), (1, 0, "EQ"), (1, 6, "MAIN"), (2, 0, "TAPE"), (2, 3, "REVERB")]   # (column, row, heading)
_SLOT = [(0, 1 + i) for i in range(6)] + [(1, 1 + i) for i in range(5)] + [(2, 1), (2, 2), (2, 4), (2, 5)]   # per module
_MAIN = (1, 7)
assert [m[4] for m in MODULES] == ["comp"] * 6 + ["eq"] * 5 + ["tape"] * 2 + ["rev"] * 2


def aud_out_pos(a):
    c, r = _MAIN if a == 0 else _SLOT[a - 1]
    return (AO_X[c], BAY_Y0 + r * BAY_DY)


def aud_in_pos(b):
    c, r = _MAIN if b == N_MOD else _SLOT[b]
    return (AI_X[c], BAY_Y0 + r * BAY_DY)


def a_blocked(a, b):
    """out a (0 = IN, 1..15 modules) into in b (0..14 modules, 15 = OUT): a module into itself is a loop"""
    return a == b + 1


PICK_AUD = (152, 50)
PK_STEPS = ["Off", "Choose", "Pick input", "Pick output", "Connected"]
PK_CANCEL = (1170, 28)
PK_DONE = (330, 440, 250, 66)
PK_UNPLUG = (700, 440, 250, 66)
BAY_CLEAR = ("bay_clear", "CLEAR ALL", 640, 28, 180, 44)
BAY_INFO_Y = 592
CABLE_TILE = 128
CABLE_COLOURS = [(150, 150, 150), (240, 240, 240), (140, 200, 240), (150, 224, 150), (70, 165, 95), (230, 200, 90),
                 (220, 120, 100)]
