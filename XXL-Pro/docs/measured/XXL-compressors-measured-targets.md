# XXL Pro compressor modules -- measured reference behaviour (targets for our own code)

Measured 2026-11-14 at 48 kHz with 1 kHz tones. Behaviour only; no code was taken. XXL-2A is in its own file.
Tables show level change in dB against input level (dBFS RMS): -40, -30, -24, -18, -12, -6, 0.
Timing rows show gain reduction in dB at a time after a tone steps from -40 up to -6 dBFS (attack) and back (release).

## XXL-1B (tube optical)
Controls: threshold -40 dBu to Off, gain Off to +30 dB, ratio 2:1 to 10:1, attack and release Fixed / Manual / Fix-Man
with manual attack and release 0-10, stereo link, meter.

| Threshold | Ratio | -40 | -30 | -24 | -18 | -12 | -6 | 0 |
|---|---|---|---|---|---|---|---|---|
| -22 dBu | 2:1 | -0.8 | -3.1 | -5.9 | -9.2 | -12.6 | -16.0 | -19.4 |
| -22 dBu | 4:1 | -1.1 | -3.6 | -6.7 | -10.4 | -14.4 | -18.6 | -23.0 |
| -22 dBu | 10:1 | -2.1 | -5.0 | -8.9 | -13.7 | -19.0 | -24.6 | -30.4 |
| -10 dBu | 2:1 | -0.3 | -0.5 | -1.1 | -2.5 | -5.1 | -8.3 | -11.7 |
| -10 dBu | 4:1 | -0.5 | -0.8 | -1.4 | -2.9 | -5.8 | -9.4 | -13.3 |
| -10 dBu | 10:1 | -1.3 | -1.7 | -2.4 | -4.2 | -7.8 | -12.4 | -17.5 |
| +2 dBu | 4:1 | -0.4 | -0.4 | -0.5 | -0.7 | -1.1 | -2.1 | -4.3 |

Very soft knee. Higher ratios also take a little off quiet signals (10:1 reads about 1 dB down at -40).
Gain knob is close to its dB marking (+5 reads +5.9, +30 reads +30.2).

| Timing | 1 ms | 2 ms | 10 ms | 50 ms | 100 ms | Release 10 ms | 30 ms | 100 ms | 1 s | 4 s |
|---|---|---|---|---|---|---|---|---|---|---|
| Fixed | 5.1 | 9.6 | 11.0 | 13.1 | 13.4 of 13.5 | 1.7 | 0.5 | 0 | 0 | 0 |
| Manual 0 / 0 | 8.6 | 14.5 | 15.3 | 15.7 | 15.7 | 12.2 | 3.9 | 0 | 0 | 0 |
| Manual 10 / 10 | 0.3 | 1.0 | 3.6 | 10.7 | 13.5 of 15.5 | 15.5 | 15.5 | 15.3 | 13.5 | 8.5 |

## XXL-16VU (VCA)
Controls: threshold 0.01-3 V RMS, ratio 1:1 to infinity, output -20 to +20 dB, stereo link, meter.

| Threshold | Ratio | -40 | -30 | -24 | -18 | -12 | -6 | 0 |
|---|---|---|---|---|---|---|---|---|
| 0.031 V | 2:1 | -1.9 | -6.9 | -9.9 | -12.9 | -15.9 | -18.9 | -21.9 |
| 0.031 V | 4:1 | -2.9 | -10.4 | -14.9 | -19.4 | -23.9 | -28.4 | -32.9 |
| 0.031 V | infinity | -3.8 | -13.7 | -19.7 | -25.6 | -31.6 | -37.5 | -43.5 |
| 0.173 V | 2:1 | 0 | 0 | -1.7 | -4.7 | -7.7 | -10.7 | -13.7 |
| 0.173 V | 4:1 | 0 | 0 | -2.6 | -7.1 | -11.6 | -16.1 | -20.6 |
| 0.173 V | infinity | 0 | 0 | -3.4 | -9.4 | -15.3 | -21.3 | -27.2 |
| 0.959 V | 4:1 | 0 | 0 | 0 | 0 | 0 | -3.8 | -8.3 |

Hard knee, exact textbook slopes (2:1 = 0.5 dB per dB, 4:1 = 0.75, infinity = 1.0). Threshold in volts maps to
dBFS: 0.173 V sits near -27.5 dBFS, and each doubling of volts raises it 6 dB.
Timing is automatic and depends on level: 19 dB of reduction reaches 10 dB in 2 ms and settles by 100 ms; release
is near-linear, about 100 dB per second at first (8.3 left of 19.3 after 100 ms, gone by 300 ms).

## XXL-76 (FET limiter)
Controls: input, output, attack 1-7 (7 fastest), release 1-7 (7 fastest), ratio buttons 4 / 8 / 12 / 20 in any
combination (16 states, including amplifier only and all buttons), circuit revision (two), stereo link, meter.
The input knob both drives the level and sets how hard it limits; there is no threshold knob.

| Input knob | Ratio | -40 | -30 | -24 | -18 | -12 | -6 | 0 |
|---|---|---|---|---|---|---|---|---|
| lower | 4:1 | +16.7 | +16.7 | +16.7 | +14.6 | +9.6 | +4.7 | -0.3 |
| lower | 20:1 | +16.7 | +16.7 | +16.7 | +16.7 | +13.2 | +7.4 | +1.5 |
| lower | all | +16.7 | +16.7 | +16.7 | +16.7 | +14.2 | +8.4 | +2.9 |
| middle | 4:1 | +29.3 | +26.7 | +21.7 | +16.8 | +11.8 | +6.9 | +1.9 |
| middle | 20:1 | +29.3 | +29.3 | +25.2 | +19.4 | +13.5 | +7.6 | +1.8 |
| middle | all | +29.3 | +29.3 | +26.2 | +20.4 | +14.9 | +9.3 | +3.7 |
| higher | 4:1 | +35.7 | +28.0 | +23.0 | +18.1 | +13.1 | +8.1 | +3.2 |
| higher | 20:1 | +36.6 | +31.2 | +25.4 | +19.5 | +13.7 | +7.8 | +1.9 |

Higher ratios start limiting later and then hold the output flatter. All buttons starts latest and lets the level
rise again above the knee. Output levels off near +2 dBFS at these settings before the output knob.

| Attack / release | 1 ms | 2 ms | 5 ms | Release 10 ms | 30 ms | 100 ms | 300 ms | 1 s | 2 s |
|---|---|---|---|---|---|---|---|---|---|
| 1 / 1 (slowest) | 13.2 | 23.3 | 24.0 of 25.6 | 24.8 | 25.0 | 24.9 | 21.7 | 12.4 | 5.0 |
| 4 / 4 | 16.6 | 24.8 | 24.9 of 26.3 | 25.6 | 25.0 | 21.8 | 14.1 | 3.9 | 1.4 |
| 7 / 7 (fastest) | 19.1 | 26.2 | 26.3 of 26.8 | 18.7 | 9.4 | 3.9 | 1.9 | 0.4 | 0 |

Attack is always under 2 ms. Release runs from about 100 ms (7) to about 2 s (1).
Harmonics while limiting at -12 dBFS: 2nd about -43 to -45 dBc, 3rd about -50 dBc; the two revisions differ by about 1 dB of gain.

## XXL-67 (tube variable-mu limiter)
Controls per side: input gain -10.76 to +9.24 dB, threshold 0-1, time constant 1-6, output gain, bypass, DC threshold;
plus mode Left-Right / Lateral-Vertical, side-chain link, meter.

| Threshold | -40 | -30 | -24 | -18 | -12 | -6 | 0 |
|---|---|---|---|---|---|---|---|
| 0.00 | -0.8 | -0.8 | -0.8 | -0.8 | -0.7 | -0.7 | -0.6 |
| 0.25 | -0.8 | -0.8 | -1.0 | -1.4 | -2.1 | -3.5 | -5.5 |
| 0.50 | -0.8 | -1.2 | -1.7 | -2.7 | -4.5 | -7.1 | -9.7 |
| 0.75 | -0.9 | -1.5 | -2.3 | -3.8 | -6.2 | -9.0 | -11.8 |
| 1.00 | -1.0 | -1.7 | -2.7 | -4.5 | -7.2 | -9.8 | -13.2 |

Gentle curve with no fixed ratio: the slope grows with level, reaching about 0.45 dB per dB at the top. Default sits
0.76 dB below unity. Input gain is exact in dB. Attack is under 2 ms at every setting.

| Time constant | Release 100 ms | 300 ms | 1 s | 2 s | 4 s |
|---|---|---|---|---|---|
| 1 | 2.9 of 7.2 | 0.3 | 0 | 0 | 0 |
| 2 | 5.6 | 2.8 | 0.2 | 0 | 0 |
| 3 | 6.8 | 5.5 | 2.4 | 0.7 | 0 |
| 4 | 7.1 | 6.5 | 4.4 | 2.4 | 0.7 |
| 5 | 6.8 | 5.8 | 4.4 | 3.1 | 1.6 |
| 6 | 5.7 | 4.9 | 4.2 | 3.6 | 2.7 |

Positions 5 and 6 are program dependent: a fast first part and a slow tail. At position 5 a 0.2 s loud burst leaves
2.0 dB after 1 s, a 6 s loud passage leaves 4.6 dB.

## XXL-DISS (compressor with detector and audio options)
Controls: input, attack, release, output (all 0-10.5), ratio 1:1 / 2 / 3 / 4 / 6 / 10 / 20 / MAX, detector Norm / HP /
Emp and link combinations, audio Norm / HP / Dist 2 / Dist 3 combinations, headroom 4-28 dB.
Like the FET module, the input knob drives the level into a fixed threshold.

| Input knob | Ratio | -40 | -30 | -24 | -18 | -12 | -6 | 0 |
|---|---|---|---|---|---|---|---|---|
| lower | 2:1 | +2.4 | +2.4 | +2.2 | +1.5 | -0.5 | -4.4 | -8.9 |
| lower | 10:1 | +2.4 | +2.4 | +2.4 | +1.2 | -3.1 | -8.4 | -13.8 |
| middle | 2:1 | +8.4 | +8.2 | +7.5 | +5.5 | +1.6 | -2.9 | -7.5 |
| middle | 10:1 | +8.4 | +8.4 | +7.2 | +2.9 | -2.4 | -7.8 | -13.0 |
| higher | 2:1 | +17.7 | +16.1 | +12.9 | +8.5 | +3.9 | -0.7 | -5.4 |
| higher | 10:1 | +17.9 | +14.4 | +9.3 | +4.0 | -1.4 | -6.6 | -11.6 |
| higher | MAX | +17.9 | +15.8 | +10.2 | +4.6 | -1.0 | -6.5 | -11.7 |

| Attack / release knobs | 1 ms | 2 ms | 10 ms | 50 ms | Release 30 ms | 100 ms | 300 ms | 1 s | 4 s |
|---|---|---|---|---|---|---|---|---|---|
| 0 / 0 | 19.7 | 20.5 | 20.5 | 20.5 of 20.8 | 12.4 | 9.7 | 4.6 | 2.6 | 0.6 |
| middle | 10.9 | 18.5 | 20.4 | 20.6 | 19.1 | 16.5 | 13.4 | 8.1 | 2.2 |
| 10.5 / 10.5 | 4.9 | 6.9 | 13.5 | 19.2 | 20.1 | 18.9 | 16.8 | 14.1 | 12.5 |

Detector options (level change at -12 dBFS, 10:1): Norm treats 60 Hz, 1 kHz and 8 kHz alike (-1.7 to -1.9 dB);
HP stops lows from triggering it (60 Hz +3.6); Emp makes highs trigger harder (8 kHz -6.4).
Audio options at -12 dBFS: Norm 2nd -67 / 3rd -66 dBc; Dist 2 -62 / -59; Dist 3 -57 / -47.

## Not measured yet (all five)
Stereo link against dual mono, meter ballistics, the remaining ratio-button combinations on XXL-76, lateral-vertical
mode and DC threshold on XXL-67, the headroom control and the link options on XXL-DISS.
