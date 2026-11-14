# XXL-Strips

The L'Cronx XXL set for Akai Force / MPC OS (ARMv7, VST2). Free. GPL-3.0-or-later.

| Plugin | Folder | Version | What it is |
|---|---|---|---|
| XXL STRIP | `XXL-STRIP/` | 0.1.1 | channel strip |
| XXL STRIP BUS | `XXL-STRIP-BUS/` | 0.1.1 | bus compressor strip |
| XXL STRIP MASTER | `XXL-STRIP-MASTER/` | 0.1.1 | master strip |
| XXL Pro | `XXL-Pro/` | 0.1.0 | "Pro" is for Process: 15 process modules in one plugin, joined on a patch bay |

Each folder is one plugin: its source, tests, art, README, screenshots (`docs/img/`) and its Panel Editor page
(`<Name>-Panel-Editor.html`: open it in a browser, arrange the panel, export `layout.json` next to `build.sh`).

The release zips (`<Name>-<version>-mpc-armv7.zip`, with `install.sh` / `uninstall.sh`) are in `releases/`, with their
SHA-256 sums in `releases/SHA256SUMS.txt`.

## Status
Built and tested as ARM code under an emulator (2026-11-14): XXL Pro 887 checks, XXL STRIP 166, XXL STRIP BUS 89,
XXL STRIP MASTER 99, all passing. Not yet verified on a Force.

## Building
Needs Python 3 (numpy, scipy, Pillow, opencv), Zig (`pip install ziglang`) and the wrapper
[`sunskiefer/mpc-vst-plugins`](https://github.com/sunskiefer/mpc-vst-plugins) at commit `d43f0d0` checked out as
`third_party/mpc-vst-plugins` inside the plugin folder (or `MPC_VST=<path>`). Then, in a plugin folder:

    ./build.sh
    test/run_arm_tests.sh        # needs qemu-arm-static (QEMU_ARM=<path>)
    ./release.sh <version>

The three strips share XXL Pro's rendered knob frames: build XXL Pro first, or run `tools/render_knobs.py` in the strip.

## Art
Knobs are rendered by `tools/knob_render.py`; keys by `tools/key_render.py` with the same light. Slider caps, tick
ring and VU face are L'Cronx art (`art/user/`).

## Credits
XXL STRIP uses code from Dusk Audio (GPL-3.0, `XXL-STRIP/third_party/dusk`). Everything else is L'Cronx code.
