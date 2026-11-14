# XXL STRIP MASTER (L'Cronx) -- master colour processor for Akai Force / MPC OS

A master-bus strip in the same console style: drive and density, shelving EQ, high-frequency compressor, stereo image, transformer stage, VU meter.

Status: 0.1.1, rendered knobs and keys, VU dial, lamp meters, Panel Editor, tested as ARM code in an emulator only (not yet on a Force).
Stages: drive (with density), LF/HF shelving EQ, HF compressor, stereo image (width, space), transformer, VU.
Build: `./build.sh` (Zig, ARMv7 only). Test: `test/run_arm_tests.sh`. Package: `./release.sh 0.1.1`.
All DSP is L'Cronx code (src/master_dsp.h, src/strip_dsp.h), written from published descriptions; voicing unverified.
Wrapper: mpc-vst-plugins. Licence: GPL-3.0-or-later.

Art by SunsKiefer, after the looks of the original panels.
