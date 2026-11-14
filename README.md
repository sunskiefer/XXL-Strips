# XXL-Strips

The L'Cronx XXL set for Akai Force / MPC OS (ARMv7, VST2). Free. GPL-3.0-or-later.

| Plugin | Folder | Version | What it is |
|---|---|---|---|
| XXL STRIP | `XXL-STRIP/` | 0.1.1 | emulation of a classic large-format British console channel strip (4000 E / G style): drive, filters, four-band EQ in three models (E Brown, E Black, G), compressor, gate / expander |
| XXL STRIP BUS | `XXL-STRIP-BUS/` | 0.1.1 | emulation of the classic console stereo bus compressor (G-series style) |
| XXL STRIP MASTER | `XXL-STRIP-MASTER/` | 0.1.1 | master-bus strip in the same console style: drive, shelving EQ, high-frequency compressor, stereo image, transformer stage |
| XXL Pro | `XXL-Pro/` | 0.1.0 | "Pro" is for Process: fifteen emulations of classic studio processors in one plugin, joined on a patch bay |

### The fifteen modules of XXL Pro
| Module | Emulation of |
|---|---|
| XXL-2A | LA-2A-style optical tube levelling amplifier |
| XXL-1B | CL 1B-style optical tube compressor |
| XXL-16VU | 160 VU-style VCA compressor / limiter |
| XXL-76 | 1176-style FET limiting amplifier |
| XXL-67 | 670-style stereo vari-mu tube limiter |
| XXL-DISS | Distressor-style character compressor |
| XXL-73 | 1073-style preamp and EQ |
| XXL-55A | 550A-style 3-band proportional-Q EQ |
| XXL-56 | 560-style 10-band graphic EQ |
| XXL-EQ1-A | EQP-1A-style passive program equalizer |
| XXL-MQ-5 | MEQ-5-style passive mid-range equalizer |
| XXL-A80 | A80-style multitrack tape machine |
| XXL-AT12 | ATR-102-style mastering tape recorder |
| XXL-224 | 224-style digital reverb |
| XXL-480R | 480L-style digital reverb |

Each folder is one plugin: its source, tests, art, README, screenshots (`docs/img/`) and its Panel Editor page
(`<Name>-Panel-Editor.html`: open it in a browser, arrange the panel, export `layout.json` next to `build.sh`).

The release zips (`<Name>-<version>-mpc-armv7.zip`, with `install.sh` / `uninstall.sh`) are on the Releases page (published from
`releases/` by `.github/workflows/release.yml`); their SHA-256 sums are in `releases/SHA256SUMS.txt`.

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
Art by SunsKiefer, after the looks of the original panels.

## Credits
XXL STRIP uses code from Dusk Audio (GPL-3.0, `XXL-STRIP/third_party/dusk`). Everything else is L'Cronx code.
