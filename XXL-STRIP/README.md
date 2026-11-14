# XXL STRIP (L'Cronx) -- SSL-style channel strip for Akai Force / MPC OS

Status: 0.1.0, functional skin, tested as ARM code in an emulator only (not yet on a Force).
Build: `./build.sh` (Zig, ARMv7 only). Test: `test/run_arm_tests.sh`. Package: `./release.sh 0.1.0`.

Credits: E Brown / E Black filters and equaliser are Dusk Audio's FourKEQDSP (GPL-3.0-or-later, third_party/dusk).
Compressor, gate/expander, G-mode equaliser, VU and engine are L'Cronx code. Wrapper: mpc-vst-plugins.
Licence: GPL-3.0-or-later (required by the Dusk code).
