# XXL STRIP BUS (L'Cronx) -- SSL-style stereo bus compressor for Akai Force / MPC OS

An emulation of the classic console stereo bus compressor (G-series style), with a VU meter.

Status: 0.1.1, rendered knobs and keys, VU dial, lamp meters, Panel Editor, tested as ARM code in an emulator only (not yet on a Force).
Build: `./build.sh` (Zig, ARMv7 only). Test: `test/run_arm_tests.sh`. Package: `./release.sh 0.1.1`.
All DSP is L'Cronx code (src/bus_comp.h, src/strip_dsp.h). Wrapper: mpc-vst-plugins. Licence: GPL-3.0-or-later.

Art by SunsKiefer, after the looks of the original panels.
