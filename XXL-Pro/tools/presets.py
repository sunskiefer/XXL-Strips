# SPDX-License-Identifier: GPL-3.0-or-later
"""Factory presets. Each: (name, {control: value}, [(out, in)]). Add at the END only.

Outs are "in" and the module keys; ins are the module keys and "out". Controls not named take their defaults and
cables not named are unplugged, so a preset always sounds the same whatever was loaded before. Stepped knobs take
the text of the step. Dry signal exists only where ("in", "out") is listed.
"""


def chain(*names):
    names = list(names)
    return [(a, b) for a, b in zip(["in"] + names, names + ["out"])]


def par(*names):
    """the named modules side by side, with the dry cable"""
    return [("in", "out")] + [("in", n) for n in names] + [(n, "out") for n in names]


def send(*names):
    """dry cable plus a chain beside it"""
    return [("in", "out")] + chain(*names)


C2A = {"m2a_peak": 45, "m2a_gain": 48}
PRESETS = [
    ("Default (dry cable)", {}, [("in", "out")]),
    # one module each
    ("INIT XXL-2A", {}, chain("m2a")), ("INIT XXL-1B", {"m1b_thr": -10}, chain("m1b")),
    ("INIT XXL-16VU", {"m16_thr": 50}, chain("m16")), ("INIT XXL-76", {}, chain("m76")),
    ("INIT XXL-67", {"m67_thr": 50}, chain("m67")), ("INIT XXL-DISS", {"mds_ratio": "4:1"}, chain("mds")),
    ("INIT XXL-73", {}, chain("m73")), ("INIT XXL-55A", {}, chain("m55")), ("INIT XXL-56", {}, chain("m56")),
    ("INIT XXL-EQ1-A", {}, chain("mq1")), ("INIT XXL-MQ-5", {}, chain("mq5")), ("INIT XXL-A80", {}, chain("ma8")),
    ("INIT XXL-AT12", {}, chain("mat")), ("INIT XXL-224 (wet only)", {}, chain("m22")),
    ("INIT XXL-480R (wet only)", {}, chain("m48")),
    # vocals
    ("VOX Level 2A", {"m2a_peak": 50, "m2a_gain": 50}, chain("m2a")),
    ("VOX 76 into 2A", {"m76_in": 30, "m76_ratio": "4:1", "m76_att": 3, "m76_rel": 6, "m76_out": 44, "m2a_peak": 40,
                        "m2a_gain": 44}, chain("m76", "m2a")),
    ("VOX Air Program EQ", {"mq1_hf": "12 kHz", "mq1_hb": 4, "mq1_bw": 7, "mq1_lf": "100 Hz", "mq1_la": 2}, chain("mq1")),
    ("VOX 73 Chain", {"m73_gain": 6, "m73_out": -6, "m73_hpf": "80 Hz", "m73_mf": "3.2 kHz", "m73_mg": 3, "m73_hg": 3,
                      "m2a_peak": 45, "m2a_gain": 46}, chain("m73", "m2a")),
    ("VOX Plate Beside", {"m48_prog": "Bright Plate", "m48_rt": 35, "m48_pre": 30, "m48_lvl": -10}, send("m48")),
    ("VOX Hall Beside", {"m22_prog": "Small Hall", "m22_pre": 40, "m22_lvl": -12}, send("m22")),
    # drums
    ("DRUMS 76 Smash Beside", {"m76_in": 48, "m76_ratio": "All", "m76_att": 7, "m76_rel": 7, "m76_out": 36}, par("m76")),
    ("DRUMS DISS Crush Beside", {"mds_in": 8, "mds_ratio": "10:1", "mds_att": 3, "mds_rel": 2, "mds_out": 3.5,
                                 "mds_aud": "Dist 3"}, par("mds")),
    ("DRUMS 16VU Punch", {"m16_thr": 55, "m16_ratio": 45, "m16_out": 4}, chain("m16")),
    ("DRUMS Tape Glue", {"ma8_in": 6, "ma8_out": -4, "ma8_spd": "15 ips"}, chain("ma8")),
    ("DRUMS 55A Snap", {"m55_lf": "100 Hz", "m55_lg": "+4 dB", "m55_mf": "400 Hz", "m55_mg": "-4 dB", "m55_hf": "10 kHz",
                        "m55_hg": "+4 dB"}, chain("m55")),
    ("DRUMS Room Beside", {"m48_prog": "Small Room", "m48_rt": 20, "m48_lvl": -8}, send("m48")),
    ("KICK Program EQ Trick", {"mq1_lf": "60 Hz", "mq1_lb": 5, "mq1_la": 4}, chain("mq1")),
    ("SNARE 73 Crack", {"m73_gain": 8, "m73_out": -8, "m73_mf": "4.8 kHz", "m73_mg": 5, "m73_lf": "220 Hz", "m73_lg": 3},
     chain("m73")),
    # bass
    ("BASS 2A Hold", {"m2a_peak": 55, "m2a_gain": 52}, chain("m2a")),
    ("BASS 1B Smooth", {"m1b_thr": -14, "m1b_ratio": 4, "m1b_gain": 5}, chain("m1b")),
    ("BASS 76 Grip", {"m76_in": 34, "m76_ratio": "8:1", "m76_att": 2, "m76_rel": 5, "m76_out": 42}, chain("m76")),
    ("BASS Tape Weight", {"mat_in": 5, "mat_out": -3, "mat_spd": "15 ips", "mat_head": "Narrow"}, chain("mat")),
    ("BASS Mid Focus", {"mq5_lf": "700 Hz", "mq5_lb": 4, "mq5_df": "300 Hz", "mq5_dp": 3}, chain("mq5")),
    # mix and master
    ("MIX 67 Glue", {"m67_thr": 45, "m67_tc": 5}, chain("m67")),
    ("MIX 67 Lat-Vert", {"m67_thr": 40, "m67_tc": 3, "m67_ms": 1}, chain("m67")),
    ("MIX Tape Master 30", {"mat_in": 3, "mat_out": -2, "mat_spd": "30 ips"}, chain("mat")),
    ("MIX Tape Master 15", {"mat_in": 4, "mat_out": -3, "mat_spd": "15 ips", "mat_bias": 1}, chain("mat")),
    ("MIX Program EQ Smile", {"mq1_lf": "30 Hz", "mq1_lb": 3, "mq1_hf": "16 kHz", "mq1_hb": 3, "mq1_bw": 8}, chain("mq1")),
    ("MIX Graphic Tilt", {"m56_b1": 2, "m56_b2": 1.5, "m56_b3": 1, "m56_b8": 1, "m56_b9": 1.5, "m56_b10": 2, "m56_rng": 1},
     chain("m56")),
    ("MIX EQ into 67 into Tape", {"mq1_lb": 2, "mq1_hb": 2, "m67_thr": 35, "m67_tc": 5, "mat_in": 2, "mat_out": -1},
     chain("mq1", "m67", "mat")),
    ("MIX 1B Gentle", {"m1b_thr": -4, "m1b_ratio": 2, "m1b_gain": 2}, chain("m1b")),
    ("MIX DISS Bus", {"mds_in": 5.5, "mds_ratio": "2:1", "mds_att": 6, "mds_rel": 4, "mds_out": 4.5, "mds_det": "HP"}, chain("mds")),
    # keys, guitars, samples
    ("KEYS Tape Wobble", {"ma8_wow": 60, "ma8_flut": 40, "ma8_spd": "7.5 ips", "ma8_in": 4, "ma8_out": -3}, chain("ma8")),
    ("KEYS Chorus 224", {"m22_prog": "Chorus", "m22_lvl": -3}, send("m22")),
    ("GTR 73 Edge", {"m73_gain": 14, "m73_out": -13, "m73_mf": "1.6 kHz", "m73_mg": 4, "m73_hpf": "80 Hz"}, chain("m73")),
    ("GTR 55A Presence", {"m55_mf": "3 kHz", "m55_mg": "+4 dB", "m55_lf": "100 Hz", "m55_lg": "-2 dB"}, chain("m55")),
    ("SAMPLE Old Tape", {"mat_spd": "3.75 ips", "mat_in": 6, "mat_out": -4, "mat_wow": 35, "mat_hiss": 1}, chain("mat")),
    ("SAMPLE Console Chain", {"m73_gain": 6, "m73_out": -6, "m55_hf": "10 kHz", "m55_hg": "+2 dB", "m76_in": 28}, chain("m73", "m55", "m76")),
    ("SAMPLE Split And Merge", {"m76_in": 40, "m76_ratio": "20:1", "m76_out": 40, "ma8_in": 6, "ma8_out": -4, "m56_b9": 3},
     [("in", "m76"), ("in", "ma8"), ("m76", "m56"), ("ma8", "m56"), ("m56", "out")]),
    # spaces
    ("SPACE Large Hall Beside", {"m22_prog": "Large Hall", "m22_mid": 38, "m22_bass": 42, "m22_pre": 25, "m22_lvl": -10}, send("m22")),
    ("SPACE Chamber Beside", {"m22_prog": "Chamber", "m22_lvl": -8}, send("m22")),
    ("SPACE Random Hall Beside", {"m48_prog": "Random Hall", "m48_rt": 50, "m48_lvl": -10}, send("m48")),
    ("SPACE Ambience Beside", {"m48_prog": "Ambience", "m48_rt": 25, "m48_lvl": -6}, send("m48")),
    ("SPACE Dark Hall Wet", {"m48_prog": "Dark Hall", "m48_rt": 60}, chain("m48")),
    ("SPACE Plate into Tape Beside", {"m22_prog": "Plate A", "ma8_in": 4, "ma8_out": -3, "m22_lvl": -8}, send("m22", "ma8")),
    ("SPACE Squashed Room Beside", {"m48_prog": "Large Room", "m76_in": 44, "m76_ratio": "20:1", "m76_rel": 7, "m76_out": 34,
                                    "m48_lvl": -4}, send("m48", "m76")),
    ("SPACE Two Reverbs Beside", {"m22_prog": "Plate B", "m22_lvl": -12, "m48_prog": "Large Hall", "m48_lvl": -14}, par("m22", "m48")),
]
assert len({p[0] for p in PRESETS}) == len(PRESETS)
