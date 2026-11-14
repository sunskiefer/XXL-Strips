# XXL STRIP (L'Cronx) -- SSL-style channel strip for Akai Force / MPC OS

An emulation of a classic large-format British console channel strip (4000 E / G style): drive, filters, four-band EQ in three models (E Brown, E Black, G), compressor, gate / expander, VU meter.

Status: 0.1.1, rendered knobs and keys, VU dial, lamp meters, Panel Editor, tested and running on an Akai Force (2026-11-14).
Build: `./build.sh` (Zig, ARMv7 only). Test: `test/run_arm_tests.sh`. Package: `./release.sh 0.1.1`.

Credits: E Brown / E Black filters and equaliser are Dusk Audio's FourKEQDSP (GPL-3.0-or-later, third_party/dusk).
Compressor, gate/expander, G-mode equaliser, VU and engine are L'Cronx code. Wrapper: mpc-vst-plugins.
Licence: GPL-3.0-or-later (required by the Dusk code).

Art by SunsKiefer, after the looks of the original panels.
