# XXL-2A -- measured reference behaviour (targets for our own code)

Measured 2026-11-14 at 48 kHz with 1 kHz tones unless noted. Behaviour only; no code was taken.

## Controls
Peak reduction 0-100 (default 30), gain 0-100 (default 40), mode Compress / Limit, stereo Dual mono / Linked,
side-chain high-frequency emphasis 0 (flat) to maximum, meter Input / Output / Gain reduction.

## Gain knob (peak reduction 0)
| Knob | Level change |
|---|---|
| 0 | silent |
| 20 | -9.9 dB |
| 40 | -0.25 dB (unity) |
| 60 | +9.4 dB |
| 80 | +19.1 dB |
| 100 | +28.7 dB |
About 0.48 dB per step above 20.

## Static curve, COMPRESS (gain 40). Level change in dB against input level (dBFS RMS)
| Peak reduction | -40 | -30 | -24 | -18 | -12 | -6 | 0 |
|---|---|---|---|---|---|---|---|
| 10 | -0.3 | -0.3 | -0.3 | -0.3 | -0.3 | -0.3 | -0.3 |
| 30 | -0.3 | -0.3 | -0.3 | -0.3 | -0.4 | -3.5 | -8.2 |
| 50 | -0.3 | -0.3 | -0.3 | -2.2 | -6.9 | -11.8 | -16.7 |
| 70 | -0.3 | -1.2 | -5.4 | -10.4 | -15.2 | -19.9 | -24.3 |
| 100 | -4.6 | -12.9 | -17.7 | -22.1 | -26.4 | -30.1 | -33.1 |

LIMIT is the same below the knee and a little steeper above it (peak reduction 70 at 0 dBFS: -26.7 against -24.3).
Above the knee the reduction grows about 0.8 dB per dB in COMPRESS and about 0.9 in LIMIT. The knob moves the
threshold: about 12 dB lower per 20 steps.

## Timing (peak reduction 60, tone stepping -40 to -6 dBFS and back; steady reduction 15.7 dB)
| Attack, time after onset | 2 ms | 5 ms | 10 ms | 20 ms | 50 ms | 100 ms |
|---|---|---|---|---|---|---|
| Reduction | 3.0 | 5.6 | 9.7 | 11.9 | 14.1 | 15.3 |

| Release, time after the loud part ends | 10 ms | 30 ms | 60 ms | 100 ms | 200 ms | 500 ms | 1 s | 2 s |
|---|---|---|---|---|---|---|---|---|
| Reduction left | 14.3 | 10.9 | 7.8 | 5.7 | 3.7 | 1.8 | 0.5 | 0 |

Two-stage release: half recovers in about 60 ms, the rest over about a second. The release did not change with how
long the loud part lasted (0.1 s, 2 s, 6 s gave the same recovery).

## Side-chain emphasis (peak reduction 60, -12 dBFS)
| Tone | Flat | Maximum emphasis |
|---|---|---|
| 60 Hz | -10.7 | -2.3 |
| 200 Hz | -10.8 | -1.9 |
| 1 kHz | -11.1 | -3.5 |
| 5 kHz | -12.7 | -10.9 |
| 10 kHz | -13.6 | -13.0 |
At maximum the detector hears mostly highs, so lows and mids are compressed far less.

## Harmonics
None measurable with no compression (below -150 dBc at -6 dBFS). Unity gain path is clean.

## Not measured yet
Dual mono against linked, the meter ballistics, harmonics while compressing.
