# Measured reference behaviour: targets for XXL STRIP

Measured 2026-11-14 by running a reference channel strip in a test host at 48 kHz and feeding it impulses and 1 kHz tones.
Behaviour only: no code was taken from the plugin. Raw logs were kept in the session's work area only.

Caveat: EQ frequencies were set through the host's linear mapping, so the "set" frequency is not the plugin's
label frequency. The peak frequency listed is what was actually measured. Gains, widths and shapes are valid.

## Signal path facts
- Zero latency. Unity gain at default (+0.03 dB).
- Always-on low cut: -2.9 dB at 20 Hz with both filters Off.
- Line input, Trim: exact dB gain (-20..+20). Fader: exact dB (+10 max). Phase: polarity flip.
- Parameters: line input, phase, HPF (Off, 20-350 Hz), LPF (Off, 21.9-3 kHz), filters to side chain, filters pre dynamics,
  HF/LF gain +-15, HF 1.5-16 kHz, LF 30-450 Hz, HF/LF bell, HMF 0.6-7 kHz, LMF 0.2-2.5 kHz, Q 0.5-3, EQ type Brown/Black,
  EQ in, EQ to side chain, EQ pre dynamics, comp in / ratio 1:1-inf / threshold -20..+10 / release 0.1-4 s / fast attack,
  stereo link, gate in / threshold -30..+10 / range 0-40 / release 0.1-4 s / mode Expand, Gate 1, Gate 2 / fast attack,
  dynamics in, key listen, fader, trim, drive 0-30.

## Filters (dB relative to 1 kHz)
| Setting | Response |
|---|---|
| HPF 80 Hz | -0.6 @80, -2.7 @56, -7.1 @40, -12.2 @30, -21.1 @20 |
| HPF 350 Hz | -0.4 @350, -3.0 @227, -7.5 @160, -13.3 @113, -19.3 @80, -25.6 @56 |
| LPF 8 kHz | -1.5 @8k, -4.0 @11k, -7.0 @14k, -10.8 @18k, -14.2 @22k |
| LPF 3 kHz | -2.3 @3k, -5.2 @4k, -11.2 @6k, -16.0 @8k, -25.7 @14k |

HPF: about 12 dB/octave, -3 dB point at about 0.65 x the label. LPF: gentle, heading to about 12 dB/octave, -3 dB a little above the label.

## EQ (gain knob at +-15)
| Band | Brown | Black |
|---|---|---|
| HF shelf | +13.3 to +14.6 | +13.4 to +14.5 |
| HF bell | peak +16.0 to +16.5 | peak +17.6 to +18.2 |
| LF shelf | +13.4 to +13.8 (stops short) | +15.3 to +15.7 |
| LF bell | peak +14.5 | peak +20.0 |
| HMF Q 3 | +15.5 to +15.8, about 1.05 octave wide | +18.1 to +18.3, about 1.0 octave wide |
| HMF Q 0.5 | +15.6 to +16.0, about 5 octaves wide | +14.9 to +15.4, about 5 octaves wide |
| LMF Q 3 | +14.1 to +14.7 | (not captured) |

- Width (measured at half the peak dB): Q 0.5 = about 5 octaves, Q 1 = about 3.5, Q 1.75 = about 2.5, Q 3 = about 1.
- Cuts mirror boosts within 0.1 dB.
- Black: bell bands peak about 3 dB (HF) to 5.5 dB (LF) above the knob value; narrow mids peak about 3 dB above.

## Compressor
Static curve, 1 kHz sine, gain change in dB against input level (dBFS RMS):

| Input | thr -10, 2:1 | thr -10, 4:1 | thr -10, 10:1 | thr -10, inf | thr 0, 4:1 | thr 0, inf |
|---|---|---|---|---|---|---|
| -28 | -0.1 | -0.2 | -0.2 | -0.3 | 0 | 0 |
| -24 | -0.3 | -0.8 | -1.1 | -1.7 | 0 | 0 |
| -20 | -0.7 | -1.8 | -2.7 | -3.9 | 0 | 0 |
| -16 | -1.3 | -3.3 | -4.9 | -7.1 | -0.3 | -0.6 |
| -12 | -2.1 | -5.3 | -7.8 | -11.0 | -1.0 | -2.1 |
| -8 | -3.0 | -7.7 | -11.1 | -14.9 | -2.2 | -4.6 |
| -4 | -4.2 | -10.4 | -14.3 | -18.8 | -3.8 | -8.1 |
| 0 | -5.5 | -13.1 | -17.5 | -22.7 | -5.9 | -12.0 |

- Very soft knee: reduction starts 15-20 dB below where the curve settles.
- At inf:1 the output settles at about -12 dBFS RMS for threshold 0, about -23 dBFS RMS for threshold -10.
- No make-up gain is added.

Timing (threshold -10, 10:1, tone stepping -40 to 0 dBFS and back):

| Setting | Attack to 63% | Attack to 90% |
|---|---|---|
| Auto attack | 32-34 ms | 52-58 ms |
| Fast attack | under 2 ms | under 2 ms |

| Release knob | Reduction left after 100 ms | 500 ms | 1 s | 2 s | Time to 10% |
|---|---|---|---|---|---|
| 0.1 s | -0.2 dB of 16.6 | 0 | 0 | 0 | 0.06 s |
| 0.5 s | -8.8 of 17.3 | -0.1 | 0 | 0 | 0.24 s |
| 1.2 s | -12.1 of 17.5 | -7.4 | -4.4 | -1.5 | 1.85 s |
| 4 s | -16.6 of 17.8 | -12.4 | -8.9 | -4.9 | 3.9 s |

Release falls roughly in a straight line in dB (constant dB per second), not as an exponential curve.

## Gate / expander (output minus input, dB)
- Expand, threshold -10, range 40: 0 dB down to -30 dBFS, then about 1.1 dB extra loss per dB (about 2:1 downward), limited by Range.
- Gate 1 and Gate 2: hard switch. Threshold -10 opens between -30 and -25 dBFS; threshold -20 opens between -40 and -35 dBFS.
- Range 15 gives -18.8 dB closed; Range 40 gives -54 dB closed.
- Release 0.1 s: closes to 63% in about 0.12 s. Attack was faster than the 2 ms measuring window.
- Gate 1 against Gate 2 showed no difference on steady tones; the difference (likely hysteresis or hold) is not yet measured.

## Drive (1 kHz)
| Input | Drive | Level change | 2nd harmonic | 3rd harmonic |
|---|---|---|---|---|
| -18 dBFS | 0 | 0 | -76 dBc | -118 dBc |
| -18 dBFS | 10 | 0 | -48 | -68 |
| -18 dBFS | 20 | 0 | -38 | -48 |
| -18 dBFS | 30 | 0 | -29 | -29 |
| -6 dBFS | 20 | -1.4 dB | -28 | -25 |
| -6 dBFS | 30 | -6.3 dB | -29 | -13 |

Level-matched, mostly 2nd harmonic at low drive, 3rd taking over when pushed.

## Not measured yet
- Gate 1 vs Gate 2 difference, gate hold, stereo link, side-chain routing switches, key listen, EQ at exact label frequencies,
  LMF in Black at high Q, VU/meter behaviour (the meters are not readable from outside the plugin).
