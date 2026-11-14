# XXL Pro tape modules -- measured reference behaviour (targets for our own code)

Measured 2026-11-14 at 48 kHz. Frequency response from a low-level impulse, saturation from 1 kHz tones, wow and
flutter from the pitch of a 3 kHz tone. Behaviour only; no code was taken.
Response rows are dB against 1 kHz at: 20, 30, 50, 100, 200, 500, 1k, 3k, 5k, 8k, 10k, 12k, 15k, 18k, 20k Hz.

## Shared controls (both modules)
Input / record level, output / repro level, tape speed, tape type (four), operating level +3 to +9 dB, bias offset
-6 to +6 dB, EQ standard (two), signal path Input / Sync / Repro / Thru, record HF trim, repro HF trim, repro LF trim
(each -6 to +6 dB), wow depth 0-0.3 %, flutter depth 0-0.1 %, hiss on/off. XXL-AT12 adds head width (three) and
crosstalk.

## XXL-A80 (two-inch multitrack)
| Speed | 20 | 30 | 50 | 100 | 200 | 500 | 1k | 3k | 5k | 8k | 10k | 12k | 15k | 18k | 20k |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 7.5 | +2.6 | +1.3 | +0.1 | -0.2 | 0 | +0.2 | 0 | -0.3 | -0.5 | -0.5 | -0.4 | -0.3 | -0.3 | -0.3 | -0.4 |
| 15 | +2.2 | +3.0 | +2.0 | +0.2 | -0.1 | +0.2 | 0 | -0.3 | -0.5 | -0.5 | -0.4 | -0.3 | -0.3 | -0.3 | -0.4 |
| 30 | +1.4 | +2.4 | +3.9 | +2.4 | +0.4 | -0.1 | 0 | -0.2 | -0.2 | -0.2 | -0.2 | -0.3 | -0.5 | -0.8 | -1.0 |

The low bump moves up with speed: about 20 Hz at 7.5, 30 Hz at 15, 50 Hz at 30. Speed Off and path Thru are flat.
Tape type changes the top only: the two older types sit 0.1-0.4 dB down above 10 kHz, the two newer types 0.5 dB up.

Saturation at 1 kHz, default tape type:
| Input | Level change | 2nd | 3rd | 5th |
|---|---|---|---|---|
| -24 dBFS | -0.1 dB | -79 dBc | -50 | -66 |
| -12 | -0.5 | -67 | -41 | -55 |
| -6 | -0.8 | -61 | -37 | -51 |
| 0 | -1.5 | -56 | -29 | -58 |
| +6 | -4.4 | -54 | -16 | -36 |

Third harmonic dominates. Tape types at 0 dBFS: third harmonic -28, -29, -22, -20 dBc in list order.
Lows compress first: 50 Hz reads +1.7 dB at -18 dBFS and -1.0 dB at 0 dBFS. 10 kHz loses 0.6 to 1.3 dB.
Wow at maximum: 0.21 % rms pitch deviation, slow (about 0.6 Hz). Flutter at maximum: 0.07 % rms at about 7 Hz.
Hiss on: -83 dBFS. Delay through the module: 6 samples.

## XXL-AT12 (mastering recorder)
| Speed | 20 | 30 | 50 | 100 | 200 | 500 | 1k | 3k | 5k | 8k | 10k | 12k | 15k | 18k | 20k |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3.75 | -2.7 | +0.3 | +0.5 | -0.5 | -1.0 | -0.7 | 0 | +1.4 | +1.0 | -1.1 | -3.7 | -7.2 | -11.5 | -17.0 | -21.2 |
| 7.5 | -0.8 | +2.2 | +1.0 | +0.8 | 0 | -0.2 | 0 | +0.2 | +0.5 | +0.8 | +0.9 | +1.0 | +0.5 | -0.7 | -2.1 |
| 15 | +1.9 | +3.3 | +1.6 | +0.1 | -0.2 | -0.2 | 0 | +0.4 | +0.7 | +0.8 | +0.8 | +0.6 | 0 | -1.4 | -2.7 |
| 30 | -6.5 | -4.6 | 0 | -0.3 | -0.4 | 0 | 0 | -0.2 | -0.6 | -0.9 | -0.7 | -0.5 | -0.3 | -0.3 | -0.5 |

The slowest speed rolls the top off hard (-21 dB at 20 kHz); the fastest loses the deep lows (-6.5 dB at 20 Hz).
Head width changes the low bump only: narrow +3.8 dB at 30 Hz, middle +3.3, wide +2.8.
Sync path is its own voicing: lifted lows (+3.7 to +4.0 dB up to 100 Hz) and a falling top (-8.8 dB at 20 kHz).
Tape type barely changes the response here.

Saturation at 1 kHz, default tape type:
| Input | Level change | 2nd | 3rd | 5th |
|---|---|---|---|---|
| -24 dBFS | +0.1 dB | -75 dBc | -48 | -64 |
| -12 | +0.4 | -63 | -43 | -52 |
| -6 | +0.4 | -57 | -52 | -48 |
| 0 | -0.5 | -52 | -26 | -50 |
| +6 | -3.7 | -48 | -14 | -30 |

Tape types at 0 dBFS: third harmonic -24, -26, -29, -26 dBc in list order.
Wow at maximum: 0.13 % rms at about 2 Hz. Flutter at maximum measured only 0.004 % rms here, far below its 0.1 %
marking; to be re-checked. Hiss on: -90 dBFS. Delay through the module: 8 samples.

## Both modules
- Bias offset tilts the top: -6 dB gives +2.9 dB at 20 kHz, +6 dB gives -2.9 dB.
- Record HF trim: up to 5.8 dB at 20 kHz, starting around 5 kHz. Repro HF trim: up to 5.9 dB, starting around 3 kHz.
- Repro LF trim: a low shelf, full 6 dB below 50 Hz, 3 dB at 100 Hz.
- EQ standard and operating level made no difference to the low-level response. Operating level should change where
  saturation starts; that is not measured yet.

## Not measured yet
Operating level against saturation, EQ standard at high level, crosstalk, how saturation changes with speed and bias,
the hiss spectrum, and the XXL-AT12 flutter reading above. Tape is level-dependent throughout, so these targets
describe it less completely than the compressor and EQ targets do.
