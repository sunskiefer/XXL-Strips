# XXL Pro inventory

Every control and socket, generated from `tools/spec.py`.

## XXL-2A

| Control | Key | Range |
|---|---|---|
| Peak Red | `m2a_peak` | 0 .. 100 |
| Gain | `m2a_gain` | 0 .. 100 |
| Limit | `m2a_mode` | Compress / Limit |
| SC Emph | `m2a_emph` | 0 .. 100 |
| Linked | `m2a_link` | Dual / Linked |

## XXL-1B

| Control | Key | Range |
|---|---|---|
| Thresh | `m1b_thr` | -40 .. 20 dBu |
| Gain | `m1b_gain` | 0 .. 30 dB |
| Ratio | `m1b_ratio` | 2 .. 10 |
| Timing | `m1b_time` | Fixed / Manual / Fix-Man |
| Attack | `m1b_att` | 0 .. 10 |
| Release | `m1b_rel` | 0 .. 10 |
| Linked | `m1b_link` | Dual / Linked |

## XXL-16VU

| Control | Key | Range |
|---|---|---|
| Thresh | `m16_thr` | 0 .. 100 |
| Ratio | `m16_ratio` | 0 .. 100 |
| Output | `m16_out` | -20 .. 20 dB |
| Linked | `m16_link` | Dual / Linked |

## XXL-76

| Control | Key | Range |
|---|---|---|
| Input | `m76_in` | 0 .. 100 |
| Output | `m76_out` | 0 .. 100 |
| Attack | `m76_att` | 1 .. 7 |
| Release | `m76_rel` | 1 .. 7 |
| Ratio | `m76_ratio` | Amp only / 4:1 / 8:1 / 12:1 / 20:1 / All |
| Rev B | `m76_rev` | Rev A / Rev B |
| Linked | `m76_link` | Dual / Linked |

## XXL-67

| Control | Key | Range |
|---|---|---|
| In Gain | `m67_in` | -10.8 .. 9.2 dB |
| Thresh | `m67_thr` | 0 .. 100 |
| Time Con | `m67_tc` | 1 .. 6 |
| Out Gain | `m67_out` | -12 .. 12 dB |
| Lat-Vert | `m67_ms` | Left-Right / Lat-Vert |
| Linked | `m67_link` | Dual / Linked |

## XXL-DISS

| Control | Key | Range |
|---|---|---|
| Input | `mds_in` | 0 .. 10.5 |
| Attack | `mds_att` | 0 .. 10.5 |
| Release | `mds_rel` | 0 .. 10.5 |
| Output | `mds_out` | 0 .. 10.5 |
| Ratio | `mds_ratio` | 1:1 / 2:1 / 3:1 / 4:1 / 6:1 / 10:1 / 20:1 / MAX |
| Detector | `mds_det` | Norm / HP / Emp |
| Audio | `mds_aud` | Norm / HP / Dist 2 / Dist 3 |
| Linked | `mds_link` | Dual / Linked |

## XXL-73

| Control | Key | Range |
|---|---|---|
| Gain | `m73_gain` | -10 .. 30 dB |
| Output | `m73_out` | -30 .. 10 dB |
| Hi-Pass | `m73_hpf` | Off / 50 Hz / 80 Hz / 160 Hz / 300 Hz |
| Low Frq | `m73_lf` | Off / 35 Hz / 60 Hz / 110 Hz / 220 Hz |
| Low | `m73_lg` | -16 .. 16 dB |
| Mid Frq | `m73_mf` | Off / 360 Hz / 700 Hz / 1.6 kHz / 3.2 kHz / 4.8 kHz / 7.2 kHz |
| Mid | `m73_mg` | -18 .. 18 dB |
| High | `m73_hg` | -18 .. 18 dB |
| EQ In | `m73_eq` | Off / On |
| Phase | `m73_ph` | Off / On |

## XXL-55A

| Control | Key | Range |
|---|---|---|
| Low Frq | `m55_lf` | 50 Hz / 100 Hz / 200 Hz / 300 Hz / 400 Hz |
| Low | `m55_lg` | -12 dB / -9 dB / -6 dB / -4 dB / -2 dB / 0 dB / +2 dB / +4 dB / +6 dB / +9 dB / +12 dB |
| Low Bell | `m55_lb` | Shelf / Bell |
| Mid Frq | `m55_mf` | 400 Hz / 800 Hz / 1.5 kHz / 3 kHz / 5 kHz |
| Mid | `m55_mg` | -12 dB / -9 dB / -6 dB / -4 dB / -2 dB / 0 dB / +2 dB / +4 dB / +6 dB / +9 dB / +12 dB |
| High Frq | `m55_hf` | 5 kHz / 7 kHz / 10 kHz / 12.5 kHz / 15 kHz |
| High | `m55_hg` | -12 dB / -9 dB / -6 dB / -4 dB / -2 dB / 0 dB / +2 dB / +4 dB / +6 dB / +9 dB / +12 dB |
| High Bell | `m55_hb` | Shelf / Bell |
| Filter | `m55_flt` | Off / On |
| EQ In | `m55_eq` | Off / On |
| Phase | `m55_ph` | Off / On |
| Output | `m55_out` | -24 .. 12 dB |

## XXL-56

| Control | Key | Range |
|---|---|---|
| 31 Hz | `m56_b1` | -12 .. 12 dB |
| 63 Hz | `m56_b2` | -12 .. 12 dB |
| 125 Hz | `m56_b3` | -12 .. 12 dB |
| 250 Hz | `m56_b4` | -12 .. 12 dB |
| 500 Hz | `m56_b5` | -12 .. 12 dB |
| 1 kHz | `m56_b6` | -12 .. 12 dB |
| 2 kHz | `m56_b7` | -12 .. 12 dB |
| 4 kHz | `m56_b8` | -12 .. 12 dB |
| 8 kHz | `m56_b9` | -12 .. 12 dB |
| 16 kHz | `m56_b10` | -12 .. 12 dB |
| EQ In | `m56_eq` | Off / On |
| 6 dB Rng | `m56_rng` | 12 dB / 6 dB |
| Output | `m56_out` | -24 .. 12 dB |

## XXL-EQ1-A

| Control | Key | Range |
|---|---|---|
| Low Frq | `mq1_lf` | 20 Hz / 30 Hz / 60 Hz / 100 Hz |
| Low Boost | `mq1_lb` | 0 .. 10 |
| Low Atten | `mq1_la` | 0 .. 10 |
| High Frq | `mq1_hf` | 3 kHz / 4 kHz / 5 kHz / 8 kHz / 10 kHz / 12 kHz / 16 kHz |
| Hi Boost | `mq1_hb` | 0 .. 10 |
| Bandwidth | `mq1_bw` | 0 .. 10 |
| Atten Sel | `mq1_af` | 5 kHz / 10 kHz / 20 kHz |
| Hi Atten | `mq1_ha` | 0 .. 10 |
| EQ In | `mq1_in` | Off / On |
| Output | `mq1_out` | -24 .. 12 dB |

## XXL-MQ-5

| Control | Key | Range |
|---|---|---|
| Low Frq | `mq5_lf` | 200 Hz / 300 Hz / 500 Hz / 700 Hz / 1 kHz |
| Low Peak | `mq5_lb` | 0 .. 10 |
| Dip Frq | `mq5_df` | 200 Hz / 300 Hz / 500 Hz / 700 Hz / 1 kHz / 1.5 kHz / 2 kHz / 3 kHz / 4 kHz / 5 kHz / 7 kHz |
| Dip | `mq5_dp` | 0 .. 10 |
| High Frq | `mq5_hf` | 1.5 kHz / 2 kHz / 3 kHz / 4 kHz / 5 kHz |
| High Peak | `mq5_hb` | 0 .. 10 |
| EQ In | `mq5_in` | Off / On |
| Output | `mq5_out` | -24 .. 12 dB |

## XXL-A80

| Control | Key | Range |
|---|---|---|
| Rec Level | `ma8_in` | -12 .. 12 dB |
| Repro Lvl | `ma8_out` | -12 .. 12 dB |
| Speed | `ma8_spd` | 7.5 ips / 15 ips / 30 ips |
| Tape | `ma8_type` | Type 1 / Type 2 / Type 3 / Type 4 |
| Bias | `ma8_bias` | -6 .. 6 dB |
| Rec HF | `ma8_rhf` | -6 .. 6 dB |
| Repro HF | `ma8_phf` | -6 .. 6 dB |
| Repro LF | `ma8_plf` | -6 .. 6 dB |
| Wow | `ma8_wow` | 0 .. 100 % |
| Flutter | `ma8_flut` | 0 .. 100 % |
| Hiss | `ma8_hiss` | Off / On |
| Tape In | `ma8_path` | Thru / Repro |

## XXL-AT12

| Control | Key | Range |
|---|---|---|
| Rec Level | `mat_in` | -12 .. 12 dB |
| Repro Lvl | `mat_out` | -12 .. 12 dB |
| Speed | `mat_spd` | 3.75 ips / 7.5 ips / 15 ips / 30 ips |
| Tape | `mat_type` | Type 1 / Type 2 / Type 3 / Type 4 |
| Bias | `mat_bias` | -6 .. 6 dB |
| Rec HF | `mat_rhf` | -6 .. 6 dB |
| Repro HF | `mat_phf` | -6 .. 6 dB |
| Repro LF | `mat_plf` | -6 .. 6 dB |
| Wow | `mat_wow` | 0 .. 100 % |
| Flutter | `mat_flut` | 0 .. 100 % |
| Hiss | `mat_hiss` | Off / On |
| Tape In | `mat_path` | Thru / Repro |
| Head | `mat_head` | Narrow / Middle / Wide |

## XXL-224

| Control | Key | Range |
|---|---|---|
| Program | `m22_prog` | Small Hall / Bright Hall / Large Hall / Room / Chamber / Plate A / Plate B / Plate C / Chorus |
| Bass | `m22_bass` | 0 .. 100 |
| Mid | `m22_mid` | 0 .. 100 |
| Crossover | `m22_xov` | 0 .. 100 |
| Treble | `m22_treb` | 0 .. 100 |
| Depth | `m22_depth` | 0 .. 71 |
| Predelay | `m22_pre` | 0 .. 256 ms |
| Diffusion | `m22_diff` | 1 .. 63 |
| Movement | `m22_mod` | Off / On |
| Level | `m22_lvl` | -24 .. 12 dB |

## XXL-480R

| Control | Key | Range |
|---|---|---|
| Program | `m48_prog` | Small Hall / Medium Hall / Large Hall / Dark Hall / Small Room / Large Room / Wood Room / Chamber / Bright Plate / Dark Plate / Random Hall / Random Space / Ambience / Tight Amb / Post Amb / Wide Space |
| Rev Time | `m48_rt` | 0 .. 100 |
| Shape | `m48_shape` | 0 .. 100 |
| Spread | `m48_spread` | 0 .. 100 |
| Size | `m48_size` | 0 .. 100 |
| HF Cut | `m48_hfc` | 0 .. 100 |
| Predelay | `m48_pre` | 0 .. 250 ms |
| Bass Mult | `m48_bm` | 0 .. 100 |
| Crossover | `m48_xov` | 0 .. 100 |
| RT HF Cut | `m48_rthc` | 0 .. 100 |
| Diffusion | `m48_diff` | 0 .. 100 |
| Spin | `m48_spin` | 0 .. 100 |
| Wander | `m48_wand` | 0 .. 100 |
| Level | `m48_lvl` | -24 .. 12 dB |

## PATCH BAY

| Control | Key | Range |
|---|---|---|
| Dry Level | `dry_level` | -60 .. 12 dB |

## Patch bay

Outputs: IN, 2A, 1B, 16VU, 76, 67, DISS, 73, 55A, 56, EQ1-A, MQ-5, A80, AT12, 224, 480R.

Inputs: 2A, 1B, 16VU, 76, 67, DISS, 73, 55A, 56, EQ1-A, MQ-5, A80, AT12, 224, 480R, OUT.

Any output into any input; one cable carries left and right; an input sums its cables; a module into itself, or a loop through other modules, is refused. Cables are parameters `ac_<out>_<in>`, saved with presets.

142 controls, 241 cables possible.
