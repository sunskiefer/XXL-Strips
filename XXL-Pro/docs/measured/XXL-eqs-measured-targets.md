# XXL Pro EQ and preamp modules -- measured reference behaviour (targets for our own code)

Measured 2026-11-14 at 48 kHz from impulse responses. Behaviour only; no code was taken.
Rows show the change in dB against the flat setting at: 30, 60, 100, 200, 400, 700, 1k, 2k, 3.5k, 5k, 8k, 12k, 16k Hz.

## XXL-73 (preamp and EQ)
Controls: input mode Line / Mic, input gain, mic gain 20-80 dB, output attenuator, high-pass Off / 50 / 80 / 160 / 300 Hz,
low band Off / 35 / 60 / 110 / 220 Hz with gain -17.7 to +14.2 dB, presence band Off / 360 / 700 / 1600 / 3200 / 4800 /
7200 Hz with gain -18.1 to +19.2 dB, 12 kHz shelf -18.2 to +20.2 dB, polarity, EQ in, level match.
Flat setting rolls off gently at the top: -0.6 dB at 8 kHz, -1.6 dB at 16 kHz.

| Control | 30 | 60 | 100 | 200 | 400 | 700 | 1k | 2k | 3.5k | 5k | 8k | 12k | 16k |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| High-pass 50 | -8.1 | -0.5 | -0.3 | -0.1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| High-pass 80 | -25.0 | -5.6 | -1.1 | -0.6 | -0.2 | -0.1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| High-pass 160 | -43.5 | -25.1 | -11.3 | -0.5 | -0.1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| High-pass 300 | -61.3 | -43.3 | -30.1 | -12.5 | -0.2 | +0.4 | +0.2 | +0.1 | 0 | 0 | 0 | 0 | 0 |
| Low 35 Hz max | +15.3 | +13.2 | +8.9 | +2.5 | +0.5 | +0.1 | +0.1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Low 60 Hz max | +15.4 | +15.0 | +13.2 | +6.0 | +0.9 | +0.1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Low 110 Hz max | +14.6 | +14.6 | +14.4 | +10.8 | +2.7 | +0.3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Low 220 Hz max | +14.2 | +14.1 | +13.9 | +12.5 | +7.5 | +2.8 | +1.2 | +0.2 | +0.1 | 0 | 0 | 0 | 0 |
| Low 220 Hz min | -17.8 | -17.6 | -17.2 | -15.0 | -9.3 | -4.2 | -2.2 | -0.5 | -0.2 | -0.1 | 0 | 0 | 0 |
| Presence 360 max | +2.4 | +6.0 | +9.8 | +16.0 | +18.9 | +14.5 | +11.3 | +6.0 | +2.9 | +1.6 | +0.7 | +0.3 | +0.2 |
| Presence 700 max | +0.6 | +2.1 | +4.4 | +9.3 | +15.6 | +19.2 | +17.4 | +11.0 | +6.5 | +4.2 | +2.1 | +1.0 | +0.5 |
| Presence 1600 max | +0.1 | +0.2 | +0.6 | +2.1 | +5.7 | +10.7 | +15.2 | +16.0 | +9.1 | +6.0 | +3.1 | +1.5 | +0.8 |
| Presence 3200 max | 0 | +0.2 | +0.5 | +1.7 | +4.6 | +8.4 | +11.3 | +17.1 | +19.1 | +17.0 | +13.0 | +9.3 | +6.9 |
| Presence 4800 max | 0 | 0 | +0.1 | +0.3 | +1.1 | +2.7 | +4.5 | +9.8 | +16.2 | +19.2 | +14.6 | +9.9 | +7.0 |
| Presence 7200 max | 0 | 0 | 0 | +0.1 | +0.3 | +0.9 | +1.6 | +4.9 | +9.9 | +15.0 | +17.8 | +11.1 | +7.5 |
| 12 kHz shelf max | 0 | 0 | 0 | 0 | +0.2 | +0.6 | +1.2 | +4.7 | +10.2 | +13.8 | +16.9 | +18.2 | +18.6 |
| 12 kHz shelf min | 0 | 0 | 0 | 0 | -0.1 | -0.4 | -1.3 | -7.5 | -13.9 | -16.0 | -16.9 | -17.1 | -17.1 |

High-pass is steep: about 18 dB per octave. Low band is a shelf. Presence bands are broad bells.
Mic mode adds gain with a rising top (+5.9 dB at 30 Hz to +13.9 dB at 16 kHz at its default).
Drive: harmonics rise with input gain and level. At -6 dBFS with +2.65 dB input gain: 2nd -52 dBc, 3rd -62 dBc.
At -18 dBFS with input gain below unity: 2nd -88 dBc.

## XXL-55A (3-band EQ)
Controls: low 50 / 100 / 200 / 300 / 400 Hz, mid 400 / 800 / 1500 / 3000 / 5000 Hz, high 5 / 7 / 10 / 12.5 / 15 kHz;
gain per band in steps -12, -9, -6, -4, -2, 0, +2, +4, +6, +9, +12 dB; low and high Shelf / Bell; band-pass filter
(50 Hz - 15 kHz); band in switches; polarity. Flat and very clean at the flat setting.

| Control at +12 | 30 | 60 | 100 | 200 | 400 | 700 | 1k | 2k | 3.5k | 5k | 8k | 12k | 16k |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Low 50 Hz shelf | +12.6 | +11.3 | +9.3 | +5.7 | +2.4 | +1.0 | +0.5 | +0.1 | 0 | 0 | 0 | 0 | 0 |
| Low 50 Hz bell | +7.2 | +11.5 | +6.9 | +2.4 | +0.7 | +0.2 | +0.1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Low 400 Hz shelf | +13.3 | +13.3 | +13.2 | +13.0 | +12.1 | +10.5 | +8.8 | +5.1 | +2.5 | +1.4 | +0.6 | +0.3 | +0.1 |
| Low 400 Hz bell | +0.3 | +0.9 | +2.1 | +6.2 | +11.8 | +7.7 | +4.7 | +1.5 | +0.5 | +0.3 | +0.1 | 0 | 0 |
| Mid (default) | 0 | +0.1 | +0.2 | +0.8 | +2.7 | +6.3 | +9.6 | +10.0 | +5.0 | +2.9 | +1.3 | +0.6 | +0.3 |
| High 5 kHz shelf | -2.1 | -2.0 | -2.0 | -1.7 | -0.8 | +0.9 | +2.6 | +6.7 | +9.5 | +10.8 | +11.7 | +12.2 | +12.3 |
| High 5 kHz bell | 0 | 0 | 0 | +0.1 | +0.3 | +0.9 | +1.7 | +5.0 | +9.8 | +11.4 | +7.7 | +4.3 | +2.6 |
| High 15 kHz shelf | 0 | 0 | 0 | +0.1 | +0.2 | +0.4 | +0.7 | +2.3 | +4.7 | +6.7 | +9.1 | +10.8 | +11.6 |
| High 15 kHz bell | 0 | 0 | 0 | 0 | +0.1 | +0.1 | +0.2 | +0.8 | +2.1 | +3.7 | +6.9 | +10.2 | +10.8 |
| Band-pass on | -8.5 | -3.3 | -1.5 | -0.6 | -0.4 | -0.3 | -0.3 | -0.3 | -0.4 | -0.5 | -0.8 | -1.4 | -2.3 |

Cuts mirror boosts. The 5 kHz high shelf dips the lows about 2 dB while it lifts the top. Polarity invert also reads
1.2 dB lower in this test (seen on XXL-73 too); to be re-checked, it may be a measuring artefact.

## XXL-56 (10-band graphic EQ)
Controls: ten bands at 31, 63, 125, 250, 500 Hz, 1, 2, 4, 8, 16 kHz, each -12 to +12 dB; EQ in; 6 dB range switch.
Each band at maximum gives +10.5 to +12.6 dB at its centre and is about one octave wide at half height
(1 kHz band at +12: +9.8 at 700 Hz, +12.5 at 1 kHz, +6.3 at 2 kHz). Neighbouring bands add: all ten at +12 gives
about +21 to +25 dB across the range, falling to +15 at 16 kHz. With the 6 dB range on, the 1 kHz band at maximum
gives +5.1 dB with the same width.

## XXL-EQ1-A (program EQ)
Controls: low frequency 20 / 30 / 60 / 100 Hz with separate boost and attenuation 0-10; high boost at 3 / 4 / 5 / 8 /
10 / 12 / 16 kHz with bandwidth sharp-to-broad; high attenuation at 5 / 10 / 20 kHz; filter network in.

| Control at 10 | 30 | 60 | 100 | 200 | 400 | 700 | 1k | 2k | 3.5k | 5k | 8k | 12k | 16k |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Low boost | +13.1 | +11.9 | +10.1 | +6.4 | +2.9 | +1.2 | +0.6 | +0.2 | 0 | 0 | 0 | 0 | 0 |
| Low attenuation | -17.9 | -16.9 | -15.3 | -11.6 | -6.9 | -3.7 | -2.2 | -0.7 | -0.2 | -0.1 | 0 | 0 | 0 |
| High boost | -1.1 | -1.1 | -1.1 | -1.0 | -0.9 | -0.5 | +0.1 | +2.5 | +6.3 | +9.4 | +12.0 | +9.3 | +6.5 |
| High attenuation | +0.1 | +0.1 | +0.1 | 0 | -0.3 | -0.9 | -1.8 | -4.9 | -8.3 | -10.5 | -13.0 | -14.4 | -15.1 |

Low boost and low attenuation have different shapes (attenuation reaches further up), which is what lets both be used
together. High boost is a bell and takes about 1 dB off everything below it. Tube-style 2nd harmonic at the flat
setting: -68 dBc at -18 dBFS, -56 dBc at -6 dBFS.

## XXL-MQ-5 (mid EQ)
Controls: low-mid boost at 200 / 300 / 500 / 700 / 1000 Hz, dip at 200 Hz - 7 kHz, high-mid boost at 1.5 / 2 / 3 / 4 /
5 kHz, each amount 0-10; filter network in.

| Control at 10 | 30 | 60 | 100 | 200 | 400 | 700 | 1k | 2k | 3.5k | 5k | 8k | 12k | 16k |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Low-mid boost (default 500 Hz) | +0.1 | +0.4 | +1.1 | +3.8 | +9.6 | +8.6 | +5.4 | +1.7 | +0.6 | +0.3 | +0.1 | 0 | 0 |
| Dip (default) | 0 | 0 | -0.1 | -0.5 | -2.0 | -6.5 | -10.9 | -3.5 | -1.1 | -0.5 | -0.2 | -0.1 | 0 |
| High-mid boost (default 2 kHz) | 0 | 0 | 0 | +0.1 | +0.3 | +0.9 | +2.1 | +8.5 | +2.8 | +1.2 | +0.4 | +0.2 | +0.1 |

Boosts reach about +10 dB, the dip about -11 dB. With everything at zero the network still leaves a small bump of a
few tenths of a dB at the selected frequencies.

## Not measured yet (all five)
The in-between frequency positions not listed, the program EQ's bandwidth control with boost applied, how the
bands interact when used together, and harmonics with the EQ bands engaged.
