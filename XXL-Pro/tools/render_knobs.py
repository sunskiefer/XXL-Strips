#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Knob filmstrips from tools/knob_render.py, used EXACTLY as it is (its light, geometry, materials and colours are
not touched: this only calls render(albedo, angle) once per frame and stacks the frames).

    python3 tools/render_knobs.py            (slow the first time; frames are kept in build/knobs/)

The light is fixed in panel space, so every frame is lit the same; only the knob's own parts turn (pointer, 16 lobes,
grain). 128 frames from -135 to +135 degrees, 400 px each, saved as build/knobs/<COLOUR>.npy (plus ALPHA.npy, each frame's transparency) for post_skin.py, which
scales them to each knob's size. The panel colour is the script's own background (36, 34, 30).
"""
import os, sys
from multiprocessing import Pool
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "build", "knobs")
FRAMES = 128


def frame(job):
    import knob_render as K
    name, i = job
    ang = -135.0 + 270.0 * i / (FRAMES - 1)
    if name.startswith("WHITE_"):   # the off-white ring: the script's own SKIRT_OFFWHITE
        return np.asarray(K.render(K.lin(K.COL[name[6:]]), ang, K.SKIRT_OFFWHITE))
    return np.asarray(K.render(K.lin(K.COL[name]), ang))


def white_frame(i):
    """the same frame over a white panel: with the normal one it gives the knob's transparency (see ALPHA below)"""
    import knob_render as K
    K.BG = np.array([1.0, 1.0, 1.0])
    ang = -135.0 + 270.0 * i / (FRAMES - 1)
    return np.asarray(K.render(K.lin(K.COL["GREY"]), ang))


def main():
    import knob_render as K
    os.makedirs(OUT, exist_ok=True)
    names = sys.argv[1:] or (list(K.COL) + ["WHITE_" + c for c in K.COL])
    for name in names:
        path = os.path.join(OUT, name + ".npy")
        if os.path.isfile(path):
            continue
        with Pool() as p:
            fr = p.map(frame, [(name, i) for i in range(FRAMES)], chunksize=4)
        np.save(path, np.stack(fr))
        print("render_knobs:", name, flush=True)
    # ALPHA: how opaque each pixel of each frame is (knob + its soft shadow), so the knob can sit on any panel with a
    # transparent background. The script draws knob-over-panel; the same frame over a white panel differs from it by
    # exactly (1 - panel) x (1 - alpha), so alpha comes out without touching the script or its light.
    path = os.path.join(OUT, "ALPHA.npy")
    if not os.path.isfile(path) and os.path.isfile(os.path.join(OUT, "GREY.npy")):
        grey = np.load(os.path.join(OUT, "GREY.npy")).astype(np.float32) / 255.0
        with Pool() as p:
            white = np.stack(p.map(white_frame, range(FRAMES), chunksize=4)).astype(np.float32) / 255.0
        bg = np.asarray(K.BG, np.float32)
        alpha = 1.0 - ((white - grey) / (1.0 - bg)[None, None, None, :]).mean(axis=3)
        np.save(path, np.clip(alpha, 0, 1).astype(np.float32))
        print("render_knobs: ALPHA", flush=True)


if __name__ == "__main__":
    main()
