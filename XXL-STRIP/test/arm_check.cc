// SPDX-License-Identifier: GPL-3.0-or-later
// XXL STRIP engine check, built for ARM (static) and run under an ARM emulator -- never a desktop build of the plugin.
// Drives mpc_engine() the way the wrapper does (int16 stereo, 128-frame blocks) and prints level tables; exits 1 on
// NaN/Inf, silence where there must be sound, or gain where there must be none.
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern "C" {
#include "engine.h"
}
static const mpc_engine_t* E;
static int fails = 0;
#define CHECK(c, what) do { if (!(c)) { printf("  FAIL: %s\n", what); ++fails; } } while (0)

static void Set(void* s, const char* k, double v) { char b[32]; snprintf(b, sizeof b, "%g", v); E->set_param(s, k, b); }

// feed a sine (dBFS peak = rms + 3), return output RMS dB over the last half; phase continues per instance
static double Run(void* s, double hz, double rms_db, double seconds, double* peak_out = 0) {
  static double ph = 0;
  int total = (int)(seconds * 44100), done = 0;
  double amp = pow(10.0, (rms_db + 3.0103) / 20.0) * 32767.0, acc = 0, pk = 0;
  long n_acc = 0;
  int16_t in[256], out[256];
  while (done < total) {
    for (int i = 0; i < 128; ++i) {
      double v = amp * sin(ph);
      ph += 2 * M_PI * hz / 44100.0;
      if (ph > 2 * M_PI) ph -= 2 * M_PI;
      if (v > 32767) v = 32767; if (v < -32768) v = -32768;
      in[2 * i] = in[2 * i + 1] = (int16_t)v;
    }
    E->process(s, in, out, 128);
    done += 128;
    if (done > total / 2) {
      for (int i = 0; i < 128; ++i) { double x = out[2 * i] / 32768.0; acc += x * x; ++n_acc; if (fabs(x) > pk) pk = fabs(x); }
    }
  }
  if (peak_out) *peak_out = pk;
  double rms = sqrt(acc / (n_acc ? n_acc : 1));
  return 20.0 * log10(rms > 1e-9 ? rms : 1e-9);
}

int main() {
  E = mpc_engine();
  const char* models[3] = {"E Brown", "E Black", "G"};
  printf("== unity and EQ, per model (1 kHz at -18 dBFS RMS unless noted)\n");
  for (int m = 0; m < 3; ++m) {
    void* s = E->create(0);
    Set(s, "model", m);
    double flat = Run(s, 1000, -18, 1.0);
    double flat50 = Run(s, 50, -18, 1.0), flat10k = Run(s, 10000, -18, 1.0);
    Set(s, "hf_gain", 12); Set(s, "hf_freq", 8000);
    double hf = Run(s, 12000, -24, 1.0);
    Set(s, "hf_gain", 0); Set(s, "lf_gain", 12); Set(s, "lf_freq", 100);
    double lf = Run(s, 50, -24, 1.0);
    Set(s, "lf_gain", 0); Set(s, "hmf_gain", 12); Set(s, "hmf_freq", 3000); Set(s, "hmf_q", 2.0);
    double hm = Run(s, 3000, -24, 1.0);
    Set(s, "hmf_gain", -12);
    double hmc = Run(s, 3000, -24, 1.0);
    Set(s, "hmf_gain", 0); Set(s, "hpf_in", 1); Set(s, "hpf_freq", 200);
    double hp = Run(s, 50, -18, 1.0);
    Set(s, "hpf_in", 0); Set(s, "lpf_in", 1); Set(s, "lpf_freq", 3200);
    double lp = Run(s, 12000, -18, 1.0);
    Set(s, "lpf_in", 0); Set(s, "eq_in", 0); Set(s, "hf_gain", 12);
    double eqout = Run(s, 12000, -24, 1.0);
    printf("%-8s flat 1k %+.2f  50Hz %+.2f  10k %+.2f | HF+12@12k %+.1f | LF+12@50 %+.1f | HMF+12@3k %+.1f, -12 %+.1f | HPF200@50 %+.1f | LPF3.2k@12k %+.1f | EQ out %+.2f\n",
           models[m], flat + 18, flat50 + 18, flat10k + 18, hf + 24, lf + 24, hm + 24, hmc + 24, hp + 18, lp + 18, eqout + 24);
    CHECK(fabs(flat + 18) < 0.5, "unity at 1 kHz with everything flat");
    CHECK(hf + 24 > 6 && lf + 24 > 6 && hm + 24 > 8, "boosts boost");
    CHECK(hmc + 24 < -8, "cut cuts");
    CHECK(hp + 18 < -12 && lp + 18 < -12, "filters filter");
    CHECK(fabs(eqout + 24) < 0.5, "EQ Out is flat");
    E->destroy(s);
  }
  printf("== compressor static curve, gain change in dB (1 kHz), threshold -10\n   in dBFS:      -40    -30    -24    -20    -16    -12     -8     -4\n");
  const double lv[8] = {-40, -30, -24, -20, -16, -12, -8, -4};
  for (int m = 1; m < 3; ++m) {
    const double ratios[4] = {2, 4, 10, 20};
    for (int r = 0; r < 4; ++r) {
      void* s = E->create(0);
      Set(s, "model", m); Set(s, "comp_thr", -10); Set(s, "comp_ratio", ratios[r]); Set(s, "comp_release", 0.3);
      printf("   %-7s %5.0f:1", models[m], ratios[r]);
      double last = 0;
      for (int i = 0; i < 8; ++i) { last = Run(s, 1000, lv[i], 2.0) - lv[i]; printf(" %+6.1f", last); }
      printf("\n");
      CHECK(last < -1.0, "compressor reduces a loud signal");
      E->destroy(s);
    }
  }
  {
    void* s = E->create(0);
    Set(s, "comp_thr", -10); Set(s, "comp_ratio", 20); Set(s, "dyn_in", 0);
    double off = Run(s, 1000, -4, 1.0) + 4;
    printf("   dynamics Out: %+.2f dB\n", off);
    CHECK(fabs(off) < 0.5, "dynamics Out is unity");
    Set(s, "dyn_in", 1); Set(s, "makeup", 1);
    double mk = Run(s, 1000, -40, 1.0) + 40;
    printf("   auto make-up at LIMIT, thr -10: %+.1f dB on a quiet signal\n", mk);
    E->destroy(s);
  }
  printf("== gate / expander, gain change in dB (1 kHz), threshold -10, range 40\n   in dBFS:        -60    -50    -40    -35    -30    -25    -20\n");
  const double gl[7] = {-60, -50, -40, -35, -30, -25, -20};
  for (int mode = 0; mode < 2; ++mode) {
    void* s = E->create(0);
    Set(s, "gate_in", 1); Set(s, "gate_mode", mode); Set(s, "gate_thr", -10); Set(s, "gate_range", 40); Set(s, "gate_release", 0.1);
    printf("   %-12s", mode ? "Gate" : "Expand");
    double first = 0, lastv = 0;
    for (int i = 0; i < 7; ++i) { double g = Run(s, 1000, gl[i], 2.0) - gl[i]; if (i == 0) first = g; lastv = g; printf(" %+6.1f", g); }
    printf("\n");
    CHECK(first < -20 && fabs(lastv) < 0.5, "gate closes on quiet, opens on loud");
    E->destroy(s);
  }
  printf("== drive, meters, state\n");
  for (int m = 0; m < 3; ++m) {
    void* s = E->create(0);
    Set(s, "model", m); Set(s, "drive", 100);
    double pk, d = Run(s, 1000, -12, 1.0, &pk) + 12;
    printf("   %-8s drive 100 %%: level %+.2f dB, peak %.3f\n", models[m], d, pk);
    CHECK(d == d && fabs(d) < 12, "drive output is finite and sane");
    E->destroy(s);
  }
  {
    void* s = E->create(0);
    char b[64], st[4096], st2[4096];
    Run(s, 1000, -18, 2.0);
    E->get_param(s, "vu_display", b, sizeof b); printf("   VU at -18 dBFS RMS: %s (expect about +0.0 VU)\n", b);
    E->get_param(s, "vu", b, sizeof b); CHECK(fabs(atof(b) - 20.0 / 23.0) < 0.03, "0 VU = -18 dBFS RMS");
    Run(s, 1000, -28, 2.0);
    E->get_param(s, "vu_display", b, sizeof b); printf("   VU at -28 dBFS RMS: %s (expect about -10 VU)\n", b);
    Set(s, "comp_thr", -15); Set(s, "comp_ratio", 20); Run(s, 1000, -6, 2.0);
    E->get_param(s, "gr_display", b, sizeof b); printf("   gain reduction readout, LIMIT thr -15, -6 dBFS in: %s\n", b);
    E->get_param(s, "comp_ratio_display", b, sizeof b); printf("   ratio at max reads: %s\n", b);
    Set(s, "hf_gain", 7.5); Set(s, "model", 2); Set(s, "gate_in", 1);
    int n = E->get_param(s, "state", st, sizeof st);
    void* t = E->create(0);
    E->set_param(t, "state", st);
    E->get_param(t, "state", st2, sizeof st2);
    printf("   state: %d bytes, restores identically: %s\n", n, strcmp(st, st2) ? "NO" : "yes");
    CHECK(!strcmp(st, st2), "state round-trip");
    int rev0, rev1;
    E->get_param(s, "display_rev", b, sizeof b); rev0 = atoi(b);
    Run(s, 1000, -40, 0.5); E->get_param(s, "display_rev", b, sizeof b); rev1 = atoi(b);
    CHECK(rev1 != rev0, "meters report movement (display_rev)");
    E->destroy(s); E->destroy(t);
  }
  printf("%s\n", fails ? "FAILED" : "PASSED");
  return fails ? 1 : 0;
}
