# XXL Pro

"Pro" is for Process. Fifteen process modules in one effect for Akai Force / MPC OS (ARMv7), part of the L'Cronx XXL
set (XXL STRIP, XXL STRIP BUS, XXL STRIP MASTER, XXL Pro). Free. GPL-3.0-or-later.

| Compressors | EQ and preamp | Tape | Reverb |
|---|---|---|---|
| XXL-2A, XXL-1B, XXL-16VU, XXL-76, XXL-67, XXL-DISS | XXL-73, XXL-55A, XXL-56, XXL-EQ1-A, XXL-MQ-5 | XXL-A80, XXL-AT12 | XXL-224, XXL-480R |

## What each module is
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

## How it works
- **Overview**: a tile per module (tap to open its page) and the PATCH BAY tile. Each tile says whether its module is
  in the signal path.
- **Patch bay**: tap a socket, then the other end. Any module's output goes into any other module's input and into
  OUT; one cable carries left and right; an input sums its cables, so series, parallel, split and merge all work
  (parallel compression: IN > OUT and IN > compressor > OUT). A loop is refused. One of each module.
- **Dry signal** exists only while IN is patched to OUT; DRY LEVEL on the patch bay page sets how loud that cable is. A fresh plugin starts with that one cable so it passes sound;
  unplug it and the dry is gone. The reverbs are fully wet for the same reason.
- A module runs only while it is in the path (fed from IN and reaching OUT).
- **Limit rule**: every module has a cost; a cable that would bring the path over the budget is refused and its
  socket is dimmed. A live guard measures the audio work; if it stays over the limit, the module that joined the
  path last is taken out with a fade (a reverb goes silent, anything else passes its input) until the patch changes.
- Cables are saved with presets and projects. 59 factory presets.
- Q-Links follow the page: the controls of the open module in reading order.

## Where the sound comes from
All DSP is our own code (`src/pro_dsp.h`), written to measured behaviour targets (`docs/measured/`): static curves,
attack and release, frequency responses, harmonics. `test/arm_check.cc` prints each module next to its targets.
The two reverbs are our own designs tuned to outside behaviour (decay times per band, first sound, early energy);
their programs are ours. The page structure and the patch bay come from PhyXXL.

## Not done yet / not verified
- Nothing has run on a real Force: CPU load, touch, Q-Links and the guard are untested on the device. The module
  costs in `tools/spec.py` are placeholders until a bench run (all fifteen in series cost 85 of 100 today).
- First functional skin: no panel art, tiles or final control placement yet.
- XXL-480R carries 16 of our own programs and 13 controls; the delay and effect programs are left out.
- XXL-AT12's saturation follows its targets only roughly; tape low-end compression, crosstalk and operating level
  are not modelled. XXL-76 ratio buttons: 4, 8, 12, 20 and All (not every combination). XXL-67 and the tape modules
  have one set of controls for both sides.
- Tape wow and flutter delay the signal a little (up to about 2 ms): a parallel dry path will comb while they are on.

## Build (ARM only)
    ./build.sh && QEMU_ARM=/path/to/qemu-arm-static test/run_arm_tests.sh && ./release.sh 0.1.0

Art by SunsKiefer, after the looks of the original panels.
