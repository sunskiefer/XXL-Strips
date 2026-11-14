# XXL Pro reverb modules -- measured reference behaviour (targets for our own designs)

Measured 2026-11-14 at 48 kHz from impulse responses, fully wet. Behaviour only; no code was taken.
For each program: decay time (time to fall 60 dB) in three bands (low 90-350 Hz, mid 500 Hz-2 kHz, high 4-9 kHz),
when the first sound arrives, how much of the energy lands in the first 80 ms, how alike left and right are
(0 = fully different, 1 = identical), and overall level.

These two cannot be rebuilt from measurements the way a compressor or EQ can: the numbers below describe how each
program sounds from outside, not how it is made inside. XXL-224 and XXL-480R will be our own reverb designs, tuned to
these targets, with our own program names.

Caveat: switching program through the host did not always bring that program's own decay settings with it, so many
programs below show similar decay times. What does change reliably per program is the early pattern, the first-sound
time, the stereo spread and the level. The decay controls were measured separately.

## XXL-224 (nine programs)
Controls: program, bass decay and mid decay 0.6-70 s, crossover and treble decay 100 Hz-10.9 kHz, depth 0-71,
predelay 0-256 ms, diffusion 1-63, two slow-movement options with their cycle settings, pitch shift, input and output
levels, wet solo.

| Program type | Decay low / mid / high | First sound | Energy in first 80 ms | Level |
|---|---|---|---|---|
| Small halls (two) | 3.2 / 2.5 / 1.8 s | 4 ms | 73-75 % | -9 to -12 dB |
| Large hall | 3.2 / 2.4 / 1.7 s | 4 ms | 63 % | -14 dB |
| Room | 2.9 / 2.1 / 1.3 s | 4 ms | 73 % | -9 dB |
| Chamber | 2.8 / 2.2 / 1.7 s | 16 ms | 11 % | -15 dB |
| Plates (three) | 2.8-3.2 / 2.1-2.5 / 1.6-1.7 s | 0-5 ms | 24-30 % | -7 to -8 dB |
| Chorus | 0.1 s (not a reverb) | 1 ms | 99 % | -9 dB |

Left and right are fully different on every program (0 within 0.08). Low frequencies ring longest, highs shortest.

Controls on the default program:
| Control | At minimum | At maximum |
|---|---|---|
| Bass decay | low band 0.7 s | low band 28 s (mid rises to 4.0 s) |
| Mid decay | mid 1.1 s, high 0.6 s | mid 14.7 s, high 7.4 s |
| Treble decay | mid and high fall to about 0.45 s | no extra damping (high 1.8 s) |
| Crossover | low and mid nearly equal (2.3 / 2.2 s) | everything follows the bass time (3.4 / 3.2 s) |
| Depth | sound arrives at 4 ms, 79 % early | sound arrives at 45 ms, 10 % early |
| Predelay | 4 ms | 260 ms |
| Diffusion | first sound at 10 ms | first sound at 4 ms |

The two slow-movement options did not change these numbers; they act on ringing inside the tail, which this test
does not show.

## XXL-480R (94 programs in ten banks)
Controls (68): program; reverb time, shape, spread, size, HF cutoff, predelay, bass multiply, crossover, HF decay cut,
diffusion; six pre-echoes with level and delay; random-hall extras (size random, spin, wander); four delays with level,
feedback, pan and rolloff for the delay programs; ambience and effects pages (size, rolloff, shelf, slope, length,
voices, feedback); input, output, blend, mute.

| Bank | Programs | Decay mid | First sound | Energy in first 80 ms | Left/right alike | Level |
|---|---|---|---|---|---|---|
| Halls | 10 | 1.8-2.4 s | 23-65 ms | 0-30 % (one at 74 %) | 0 | -7 to -15 dB |
| Rooms | 10 | 2.0-2.6 s | 23-26 ms | 9-93 % | 0 | -11 to -14 dB |
| Unusual spaces | 10 | 1.7-2.7 s | 23-58 ms | 0-88 % | 0 to -0.26 | -4 to -13 dB |
| Plates | 5 | 2.0-2.3 s | 23-42 ms | 21-84 % | 0 | -8 to -11 dB |
| Random halls | 10 | 2.1-2.6 s, highs shorter (1.2-1.6 s) | 23-33 ms | 2-41 % | 0 | -7 to -12 dB |
| Random spaces | 10 | 2.2-2.9 s | 23-31 ms | 15-90 % | 0 | -5 to -10 dB |
| Ambience | 10 | 1.2-1.6 s (two near 2.6-3.1 s) | 26-46 ms | 3-80 % | 0.05-0.15 | +1 to -7 dB |
| Post ambience | 9 | 0.04-2.3 s | 23-49 ms | mostly 82-100 % | up to 0.36 | 0 to -12 dB |
| Twin delays | 10 | none (discrete echoes) | 31 ms | 100 % | 0 | +3 dB |
| Effects | 10 | 0.05-0.25 s | 25 ms | 97-100 % | 0 | -11 to -15 dB |

What separates the banks:
- Halls build slowly: little energy in the first 80 ms, first sound as late as 65 ms.
- Rooms and plates arrive sooner and more densely.
- Random halls and random spaces have the same shapes with a moving tail and shorter highs.
- Ambience is short and slightly narrower in stereo; post ambience is mostly early sound with left and right more alike.
- Twin delays and effects are echo and modulation programs, not reverbs.
- Every program has a built-in delay of about 23 ms before any sound.

## Not measured
- Each program's own factory decay settings (see the caveat).
- The 480R's controls one by one (68 of them).
- The moving-tail behaviour (spin, wander, the 224's slow-movement options).
- Echo times and feedback of the delay and effects programs.
- Density of the tail over time, which is a large part of how a reverb sounds.
