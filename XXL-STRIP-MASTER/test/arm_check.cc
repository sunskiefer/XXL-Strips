// SPDX-License-Identifier: GPL-3.0-or-later
// XXL STRIP MASTER engine check, built for ARM (static) and run under an ARM emulator.
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
// stereo sine: right = left * rscale. Returns output RMS dB of left; side_db gets the L-R level
static double Run(void* s, double hz, double rms_db, double seconds, double rscale = 1.0, double* side_db = 0) {
  static double ph = 0;
  int total = (int)(seconds * 44100), done = 0;
  double amp = pow(10.0, (rms_db + 3.0103) / 20.0) * 32767.0, acc = 0, sacc = 0; long n_acc = 0;
  int16_t in[256], out[256];
  while (done < total) {
    for (int i = 0; i < 128; ++i) { double v = amp * sin(ph); ph += 2 * M_PI * hz / 44100.0; if (ph > 2 * M_PI) ph -= 2 * M_PI; in[2 * i] = (int16_t)v; in[2 * i + 1] = (int16_t)(v * rscale); }
    E->process(s, in, out, 128); done += 128;
    if (done > total / 2) for (int i = 0; i < 128; ++i) { double x = out[2 * i] / 32768.0, d = (out[2 * i] - out[2 * i + 1]) / 65536.0; acc += x * x; sacc += d * d; ++n_acc; }
  }
  if (side_db) { double r = sqrt(sacc / (n_acc ? n_acc : 1)); *side_db = 20.0 * log10(r > 1e-9 ? r : 1e-9); }
  double rms = sqrt(acc / (n_acc ? n_acc : 1));
  return 20.0 * log10(rms > 1e-9 ? rms : 1e-9);
}
int main() {
  E = mpc_engine();
  void* s = E->create(0);
  double u = Run(s, 1000, -18, 1.0) + 18; printf("everything Out: %+.2f dB at 1 kHz\n", u); CHECK(fabs(u) < 0.1, "unity when all stages are out");
  Set(s, "hpf", 3); double h = Run(s, 20, -18, 1.5) + 18; printf("HPF 50 Hz: 20 Hz tone %+.1f dB\n", h); CHECK(h < -15, "HPF"); Set(s, "hpf", 0);
  Set(s, "eq_in", 1); Set(s, "lf_gain", 9); Set(s, "lf_freq", 1); double lf = Run(s, 30, -24, 1.5) + 24, mid = Run(s, 1000, -24, 1.0) + 24;
  Set(s, "lf_gain", 0); Set(s, "hf_gain", 9); Set(s, "hf_freq", 0); double hf = Run(s, 16000, -24, 1.0) + 24;
  printf("EQ: LF +9 at 50 Hz -> 30 Hz tone %+.1f dB, 1 kHz %+.1f dB; HF +9 at 8 kHz -> 16 kHz tone %+.1f dB\n", lf, mid, hf);
  CHECK(lf > 6 && fabs(mid) < 1.5 && hf > 6, "shelves"); Set(s, "hf_gain", 0); Set(s, "eq_in", 0);
  printf("DRIVE (1 kHz), level change in dB:   -30 dBFS  -18 dBFS   -6 dBFS\n");
  for (int d = 0; d <= 10; d += 5) {
    Set(s, "drive_in", 1); Set(s, "drive", d);
    double a = Run(s, 1000, -30, 1.0) + 30, b = Run(s, 1000, -18, 1.0) + 18, c = Run(s, 1000, -6, 1.0) + 6;
    printf("   drive %2d                         %+7.2f  %+7.2f  %+7.2f\n", d, a, b, c);
    CHECK(fabs(a) < 0.7 && c == c && c > -9 && c < 1, "drive is level-matched when quiet and sane when loud");
  }
  Set(s, "drive_in", 0);
  Set(s, "hfc_in", 1); Set(s, "hfc_thr", -10); Set(s, "hfc_xover", 5000);
  double hq = Run(s, 10000, -40, 1.0) + 40, hl = Run(s, 10000, -10, 1.0) + 10, lo = Run(s, 200, -10, 1.0) + 10;
  printf("HF COMP thr -10, x-over 5 kHz: 10 kHz quiet %+.1f dB, 10 kHz loud %+.1f dB, 200 Hz loud %+.1f dB\n", hq, hl, lo);
  CHECK(fabs(hq) < 1.0 && hl < -3 && fabs(lo) < 1.0, "HF comp turns down loud highs only"); Set(s, "hfc_in", 0);
  double sd0, sd1, sd2; Run(s, 1000, -18, 1.0, 0.0, &sd0);
  Set(s, "img_in", 1); Set(s, "width", 4); Run(s, 1000, -18, 1.0, 0.0, &sd1);
  Set(s, "width", -4); Run(s, 1000, -18, 1.0, 0.0, &sd2);
  printf("IMAGE: side level change, width +4: %+.1f dB, width -4: %+.1f dB\n", sd1 - sd0, sd2 - sd0);
  CHECK(fabs(sd1 - sd0 - 4) < 0.5 && fabs(sd2 - sd0 + 4) < 0.5, "width moves the side signal"); Set(s, "img_in", 0);
  Set(s, "trafo", 1); double tq = Run(s, 60, -30, 1.5) + 30, tl = Run(s, 60, -6, 1.5) + 6, th = Run(s, 2000, -6, 1.0) + 6;
  printf("TRANSFORMER: 60 Hz quiet %+.2f dB, 60 Hz loud %+.2f dB, 2 kHz loud %+.2f dB\n", tq, tl, th);
  CHECK(fabs(tq) < 0.3 && tl < -0.2 && tl > -6 && fabs(th) < 0.5, "transformer saturates loud lows only");
  char st[2048], st2[2048];
  E->get_param(s, "state", st, sizeof st); void* t = E->create(0); E->set_param(t, "state", st); E->get_param(t, "state", st2, sizeof st2);
  printf("state restores identically: %s\n", strcmp(st, st2) ? "NO" : "yes"); CHECK(!strcmp(st, st2), "state round-trip");
  printf("%s\n", fails ? "FAILED" : "PASSED");
  return fails ? 1 : 0;
}
