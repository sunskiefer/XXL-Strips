// SPDX-License-Identifier: GPL-3.0-or-later
// XXL STRIP BUS engine check, built for ARM (static) and run under an ARM emulator.
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
static double Run(void* s, double hz, double rms_db, double seconds) {
  static double ph = 0;
  int total = (int)(seconds * 44100), done = 0;
  double amp = pow(10.0, (rms_db + 3.0103) / 20.0) * 32767.0, acc = 0; long n_acc = 0;
  int16_t in[256], out[256];
  while (done < total) {
    for (int i = 0; i < 128; ++i) { double v = amp * sin(ph); ph += 2 * M_PI * hz / 44100.0; if (ph > 2 * M_PI) ph -= 2 * M_PI; in[2 * i] = in[2 * i + 1] = (int16_t)v; }
    E->process(s, in, out, 128); done += 128;
    if (done > total / 2) for (int i = 0; i < 128; ++i) { double x = out[2 * i] / 32768.0; acc += x * x; ++n_acc; }
  }
  double rms = sqrt(acc / (n_acc ? n_acc : 1));
  return 20.0 * log10(rms > 1e-9 ? rms : 1e-9);
}
int main() {
  E = mpc_engine();
  const double lv[7] = {-40, -30, -24, -18, -12, -6, -3};
  printf("== static curve, gain change in dB (1 kHz), threshold 0 (= -18 dBFS), release 0.3 s\n   in dBFS:   -40    -30    -24    -18    -12     -6     -3\n");
  for (int r = 0; r < 4; ++r) {
    void* s = E->create(0);
    Set(s, "mode", 1); Set(s, "ratio", r); Set(s, "release", 1);
    printf("   ratio %d ", r);
    double last = 0, first = 0;
    for (int i = 0; i < 7; ++i) { last = Run(s, 1000, lv[i], 1.5) - lv[i]; if (!i) first = last; printf(" %+6.1f", last); }
    printf("\n");
    CHECK(fabs(first) < 0.3 && last < -3.0, "quiet passes, loud is reduced");
    E->destroy(s);
  }
  void* s = E->create(0);
  Set(s, "comp_in", 0); double off = Run(s, 1000, -6, 1.0) + 6; printf("   COMP Out: %+.2f dB\n", off); CHECK(fabs(off) < 0.1, "COMP Out is unity");
  E->destroy(s); s = E->create(0);
  Set(s, "thr", -10); Set(s, "ratio", 3); Set(s, "makeup", 6);
  double a = Run(s, 1000, -40, 1.0) + 40; printf("   make-up 6 dB on a quiet signal: %+.2f dB\n", a); CHECK(fabs(a - 6) < 0.3, "make-up");
  Set(s, "makeup", 0); Set(s, "release", 1); Set(s, "mode", 1); Set(s, "mix", 0);
  double dry = Run(s, 1000, -6, 1.0) + 6; printf("   Modern, MIX 0 %%: %+.2f dB (dry)\n", dry); CHECK(fabs(dry) < 0.2, "MIX 0 is dry");
  Set(s, "mix", 100); Set(s, "sc_hpf_in", 1); Set(s, "sc_hpf", 300);
  double lo = Run(s, 50, -6, 1.5) + 6, hi = Run(s, 2000, -6, 1.5) + 6;
  printf("   side-chain HPF 300 Hz: 50 Hz tone %+.1f dB, 2 kHz tone %+.1f dB\n", lo, hi); CHECK(lo > hi + 3, "SC HPF spares the low end");
  Set(s, "mode", 0);
  double cl = Run(s, 50, -6, 1.5) + 6; printf("   Classic ignores SC HPF: 50 Hz tone %+.1f dB\n", cl); CHECK(cl < lo - 3, "Classic has no SC HPF");
  // release: after a loud burst, how much reduction is left 0.5 s later (0.1 s vs AUTO)
  for (int rel = 0; rel < 5; rel += 4) {
    void* t = E->create(0); char b[32];
    Set(t, "thr", -10); Set(t, "ratio", 3); Set(t, "release", rel);
    Run(t, 1000, -3, 3.0); Run(t, 1000, -50, 0.5);
    E->get_param(t, "gr", b, sizeof b);
    printf("   release %s: %.1f dB of reduction left 0.5 s after a 3 s loud burst\n", rel ? "AUTO" : "0.1 s", atof(b) * 20);
    if (!rel) CHECK(atof(b) * 20 < 0.5, "0.1 s release has recovered"); else CHECK(atof(b) * 20 > 1.0, "AUTO holds longer after sustained level");
    E->destroy(t);
  }
  char st[2048], st2[2048];
  E->get_param(s, "state", st, sizeof st); void* u = E->create(0); E->set_param(u, "state", st); E->get_param(u, "state", st2, sizeof st2);
  printf("   state restores identically: %s\n", strcmp(st, st2) ? "NO" : "yes"); CHECK(!strcmp(st, st2), "state round-trip");
  printf("%s\n", fails ? "FAILED" : "PASSED");
  return fails ? 1 : 0;
}
