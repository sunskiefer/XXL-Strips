// SPDX-License-Identifier: GPL-3.0-or-later
// XXL Pro engine check, built for ARM (static) and run under an ARM emulator. Prints our modules' behaviour next to
// the measured targets (docs/measured) and fails where a module is clearly off.
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
static double Get(void* s, const char* k) { char b[128] = "0"; E->get_param(s, k, b, sizeof b); return atof(b); }
static void* New(const char* module) {   // a fresh plugin with IN > module > OUT and no dry cable
  void* s = E->create(0);
  Set(s, "guard", 0);
  Set(s, "ac_in_out", 0);
  if (module) { char k[40]; snprintf(k, sizeof k, "ac_in_%s", module); Set(s, k, 1); snprintf(k, sizeof k, "ac_%s_out", module); Set(s, k, 1); }
  return s;
}
static double g_ph = 0;
// runs a sine; returns the output level (dBFS RMS, left) over the last `tail` share of the time. scale: the sine is
// sent at 1/scale of its level so levels above full scale can be tested through an input gain (returned level is
// corrected by the caller).
static double Run(void* s, double hz, double rms_db, double seconds, double tail = 0.5) {
  int total = (int)(seconds * 44100), done = 0;
  double amp = pow(10.0, (rms_db + 3.0103) / 20.0) * 32767.0, acc = 0; long n_acc = 0;
  int16_t in[256], out[256];
  while (done < total) {
    for (int i = 0; i < 128; ++i) { double v = amp * sin(g_ph); g_ph += 2 * M_PI * hz / 44100.0; if (g_ph > 2 * M_PI) g_ph -= 2 * M_PI; in[2 * i] = in[2 * i + 1] = (int16_t)v; }
    E->process(s, in, out, 128); done += 128;
    if (done > total * (1.0 - tail)) for (int i = 0; i < 128; ++i) { double x = out[2 * i] / 32768.0; acc += x * x; ++n_acc; }
  }
  double rms = sqrt(acc / (n_acc ? n_acc : 1));
  return 20.0 * log10(rms > 1e-9 ? rms : 1e-9);
}
static const double LV[7] = {-40, -30, -24, -18, -12, -6, -3};
// static curve: gain change against input level; target has 6 values (-40..-6) and the row is checked within tol
static void Curve(const char* name, void* s, const double* target, double tol, double trim = 0) {
  printf("   %-26s", name);
  double worst = 0;
  for (int i = 0; i < 6; ++i) {
    double g = Run(s, 1000, LV[i], 1.2) - LV[i] - trim;
    printf(" %+6.1f", g);
    if (target) { double e = fabs(g - target[i]); if (e > worst) worst = e; }
  }
  if (target) { printf("   target"); for (int i = 0; i < 6; ++i) printf(" %+6.1f", target[i]); printf("   worst %.1f dB", worst); }
  printf("\n");
  if (target) CHECK(worst <= tol, name);
}
// magnitude response at f (dB) of the current patch, low level
static double Resp(void* s, double hz) { return Run(s, hz, -30, hz < 100 ? 0.8 : 0.3) + 30; }
static void EqRow(const char* name, void* s, const double* target, double tol) {
  static const double F[13] = {30, 60, 100, 200, 400, 700, 1000, 2000, 3500, 5000, 8000, 12000, 16000};
  printf("   %-22s", name);
  double worst = 0;
  for (int i = 0; i < 13; ++i) { double g = Resp(s, F[i]); printf(" %+5.1f", g); if (target) { double e = fabs(g - target[i]); if (e > worst) worst = e; } }
  if (target) printf("   worst %.1f dB", worst);
  printf("\n");
  if (target) CHECK(worst <= tol, name);
}
// gain reduction left `ms` after a -6 dBFS tone drops to -40 (after `hold` seconds loud)
static void Timing(const char* name, void* s, int mod, const double* at_ms, int na, const double* rel_ms, int nr, double hold = 1.5) {
  char k[16]; snprintf(k, sizeof k, "gr_%d", mod);
  Run(s, 1000, -40, 0.5);
  printf("   %-22s attack:", name);
  double t = 0;
  for (int i = 0; i < na; ++i) { Run(s, 1000, -6, (at_ms[i] - t) / 1000.0); t = at_ms[i]; printf(" %g ms %.1f", at_ms[i], Get(s, k)); }
  Run(s, 1000, -6, hold); printf("  steady %.1f | release:", Get(s, k));
  t = 0;
  for (int i = 0; i < nr; ++i) { Run(s, 1000, -40, (rel_ms[i] - t) / 1000.0); t = rel_ms[i]; printf(" %g ms %.1f", rel_ms[i], Get(s, k)); }
  printf("\n");
}
// impulse response measurements of a reverb: decay time in three bands, first sound, early energy share
static void Reverb(const char* name, void* s, double seconds, double* rt_out) {
  int total = (int)(seconds * 44100);
  float* h = (float*)calloc(total, sizeof(float));
  int16_t in[256], out[256];
  for (int done = 0; done < total; done += 128) {
    memset(in, 0, sizeof in);
    if (!done) in[0] = in[1] = 30000;
    E->process(s, in, out, 128);
    for (int i = 0; i < 128 && done + i < total; ++i) h[done + i] = out[2 * i] / 30000.0f;
  }
  int first = -1; double e_all = 0, e_early = 0;
  for (int i = 0; i < total; ++i) { double e = (double)h[i] * h[i]; if (first < 0 && fabs(h[i]) > 2e-4) first = i; e_all += e; }
  for (int i = 0; i < total && i < first + 3528; ++i) e_early += (double)h[i] * h[i];
  printf("   %-16s first %5.1f ms  early %3.0f %%  level %+5.1f dB  decay", name, first * 1000.0 / 44100, 100 * e_early / (e_all + 1e-20), 10 * log10(e_all + 1e-20));
  static const double lo[3] = {90, 500, 4000}, hi[3] = {350, 2000, 9000};
  for (int b = 0; b < 3; ++b) {   // band-pass (two one-pole pairs twice), Schroeder integration, -5..-25 dB slope
    double a_lo = 1 - exp(-2 * M_PI * lo[b] / 44100), a_hi = 1 - exp(-2 * M_PI * hi[b] / 44100), l1 = 0, l2 = 0, h1 = 0, h2 = 0;
    double* e = (double*)calloc(total, sizeof(double));
    for (int i = 0; i < total; ++i) {
      double x = h[i];
      h1 += a_hi * (x - h1); h2 += a_hi * (h1 - h2); l1 += a_lo * (h2 - l1); l2 += a_lo * (l1 - l2);
      double y = h2 - l2; e[i] = y * y;
    }
    for (int i = total - 2; i >= 0; --i) e[i] += e[i + 1];
    int i5 = -1, i25 = -1;
    for (int i = 0; i < total; ++i) { double d = 10 * log10(e[i] / (e[0] + 1e-30) + 1e-30); if (i5 < 0 && d <= -5) i5 = i; if (i25 < 0 && d <= -25) { i25 = i; break; } }
    double rt = (i5 >= 0 && i25 > i5) ? 3.0 * (i25 - i5) / 44100.0 : 0;
    printf(" %.2f", rt); if (rt_out) rt_out[b] = rt;
    free(e);
  }
  printf(" s\n");
  free(h);
}
// harmonics of a 1 kHz tone at the output, dBc (Goertzel)
static void Thd(void* s, double rms_db, double* h2, double* h3) {
  Run(s, 1000, rms_db, 0.5);
  const int N = 44100; static double buf[44100]; int16_t in[256], out[256];
  double amp = pow(10.0, (rms_db + 3.0103) / 20.0) * 32767.0;
  for (int done = 0; done < N; done += 128) {
    for (int i = 0; i < 128; ++i) { in[2 * i] = in[2 * i + 1] = (int16_t)(amp * sin(g_ph)); g_ph += 2 * M_PI * 1000 / 44100.0; }
    E->process(s, in, out, 128);
    for (int i = 0; i < 128 && done + i < N; ++i) buf[done + i] = out[2 * i] / 32768.0;
  }
  double m[4];
  for (int k = 1; k <= 3; ++k) { double re = 0, im = 0; for (int i = 0; i < N; ++i) { re += buf[i] * cos(2 * M_PI * 1000 * k * i / 44100.0); im += buf[i] * sin(2 * M_PI * 1000 * k * i / 44100.0); } m[k] = sqrt(re * re + im * im); }
  *h2 = 20 * log10(m[2] / m[1] + 1e-12); *h3 = 20 * log10(m[3] / m[1] + 1e-12);
}

int main(int argc, char** argv) {
  E = mpc_engine();
  bool all = argc < 2;
  const char* only = all ? "" : argv[1];
#define SEC(n) if (all || !strcmp(only, n))
  SEC("meters") {
    printf("== module meters (parameter m_vu, 0..31; 0 VU = position 21)\n");
    void* s = New("m76"); Set(s, "go_m76", 1); Set(s, "m76_in", 60);
    Run(s, 1000, -50, 1.0); double rest = Get(s, "m_vu");
    Run(s, 1000, -3, 1.5); double hit = Get(s, "m_vu"), gr = Get(s, "gr_3");
    printf("   XXL-76 needle: quiet %g, loud %g (gain reduction %.1f dB)\n", rest, hit, gr);
    CHECK(rest == 21 && hit < rest - 2, "VU needle rests at 0 VU and falls with gain reduction");
    Set(s, "go_m2a", 1); Run(s, 1000, -3, 0.3);
    printf("   on a page whose module is not patched: %g\n", Get(s, "m_vu")); CHECK(Get(s, "m_vu") == 0, "unpatched module: needle at rest left");
    E->destroy(s);
    s = New("mds"); Set(s, "go_mds", 1); Set(s, "mds_ratio", 5); Set(s, "mds_in", 8); Run(s, 1000, -50, 1.0); rest = Get(s, "m_vu"); Run(s, 1000, -3, 1.5); hit = Get(s, "m_vu");
    printf("   XXL-DISS lamps: quiet %g, loud %g (gain reduction %.1f dB)\n", rest, hit, Get(s, "gr_5"));
    CHECK(rest == 0 && hit >= 1 && hit <= 16, "DISS lamps follow gain reduction");
    E->destroy(s);
    s = New("ma8"); Set(s, "go_ma8", 1); Run(s, 1000, -50, 1.0); rest = Get(s, "m_vu"); Run(s, 1000, -18, 1.5); hit = Get(s, "m_vu");
    printf("   XXL-A80 needle: -50 dBFS %g, -18 dBFS %g\n", rest, hit);
    CHECK(rest <= 1 && hit >= 17 && hit <= 25, "tape VU: -18 dBFS reads about 0 VU");
    E->destroy(s);
  }
  SEC("graph") {
    printf("== patching\n");
    void* s = E->create(0); Set(s, "guard", 0);
    double d = Run(s, 1000, -12, 0.3) + 12; printf("   fresh plugin (dry cable): %+.2f dB\n", d); CHECK(fabs(d) < 0.1, "default passes sound");
    Set(s, "ac_in_out", 0); d = Run(s, 1000, -12, 0.3); printf("   dry cable unplugged: %.0f dBFS\n", d); CHECK(d < -80, "no cable, no sound");
    Set(s, "ac_in_m56", 1); Set(s, "ac_m56_out", 1); d = Run(s, 1000, -12, 0.3) + 12; printf("   IN > 56 > OUT: %+.2f dB, cost %g\n", d, Get(s, "cost")); CHECK(fabs(d) < 0.2 && Get(s, "cost") == 5, "one module in the path");
    Set(s, "ac_in_out", 1); d = Run(s, 1000, -12, 0.3) + 12; printf("   plus the dry cable (parallel): %+.2f dB\n", d); CHECK(fabs(d - 6.02) < 0.2, "inputs sum");
    Set(s, "dry_level", -60); d = Run(s, 1000, -12, 0.5) + 12; printf("   DRY LEVEL fully down: %+.2f dB (only the module is heard)\n", d); CHECK(fabs(d) < 0.2, "dry level off");
    Set(s, "dry_level", 0); Run(s, 1000, -12, 0.3);
    Set(s, "ac_m56_m55", 1); Set(s, "ac_m55_m56", 1); printf("   56 > 55 and 55 > 56: active 55 = %g (the loop cable is refused)\n", Get(s, "active_7"));
    d = Run(s, 1000, -12, 0.3) + 12; CHECK(d == d && d < 12, "a loop is refused");
    Set(s, "ac_m56_m55", 0); Set(s, "ac_m55_m56", 0);
    Set(s, "ac_in_m22", 1); printf("   224 fed but not patched to OUT: active = %g\n", Get(s, "active_13")); CHECK(Get(s, "active_13") == 0, "a module off the path does not run");
    Set(s, "guard_trip", 1); d = Run(s, 1000, -12, 0.3) + 12; printf("   guard takes 56 out (it passes its input): %+.2f dB, active = %g\n", d, Get(s, "active_8")); CHECK(fabs(d - 6.02) < 0.2 && Get(s, "active_8") == 0, "guard bypass");
    Set(s, "ac_in_m22", 0); printf("   after a patch change 56 is back: active = %g\n", Get(s, "active_8")); CHECK(Get(s, "active_8") == 1, "trip clears on a patch change");
    char st[4096], st2[4096]; E->get_param(s, "state", st, sizeof st);
    void* u = E->create(0); E->set_param(u, "state", st); E->get_param(u, "state", st2, sizeof st2);
    printf("   state restores identically: %s\n", strcmp(st, st2) ? "NO" : "yes"); CHECK(!strcmp(st, st2), "state round-trip");
    E->destroy(u); E->destroy(s);
    // all fifteen in series: stays finite
    s = New(0);
    static const char* M[15] = {"m2a", "m1b", "m16", "m76", "m67", "mds", "m73", "m55", "m56", "mq1", "mq5", "ma8", "mat", "m22", "m48"};
    char k[40]; const char* prev = "in";
    for (int i = 0; i < 15; ++i) { snprintf(k, sizeof k, "ac_%s_%s", prev, M[i]); Set(s, k, 1); prev = M[i]; }
    snprintf(k, sizeof k, "ac_%s_out", prev); Set(s, k, 1);
    d = Run(s, 220, -12, 2.0); printf("   all fifteen in series: output %.1f dBFS, cost %g of 100\n", d, Get(s, "cost")); CHECK(d == d && d > -60 && d < 0, "series of all modules");
    E->destroy(s);
  }
  SEC("2a") {
    printf("== XXL-2A static curve (gain 40), in dBFS: -40 -30 -24 -18 -12 -6\n");
    static const double T[5][6] = {{-.3, -.3, -.3, -.3, -.3, -.3}, {-.3, -.3, -.3, -.3, -.4, -3.5}, {-.3, -.3, -.3, -2.2, -6.9, -11.8}, {-.3, -1.2, -5.4, -10.4, -15.2, -19.9}, {-4.6, -12.9, -17.7, -22.1, -26.4, -30.1}};
    static const int pr[5] = {10, 30, 50, 70, 100};
    for (int i = 0; i < 5; ++i) { void* s = New("m2a"); Set(s, "m2a_peak", pr[i]); char n[32]; snprintf(n, sizeof n, "peak reduction %d", pr[i]); Curve(n, s, T[i], 1.6); E->destroy(s); }
    void* s = New("m2a"); Set(s, "m2a_peak", 60);
    static const double a[6] = {2, 5, 10, 20, 50, 100}, r[8] = {10, 30, 60, 100, 200, 500, 1000, 2000};
    Timing("peak reduction 60", s, 0, a, 6, r, 8);
    printf("      target         attack: 3.0 5.6 9.7 11.9 14.1 15.3 of 15.7 | release: 14.3 10.9 7.8 5.7 3.7 1.8 0.5 0\n");
    E->destroy(s);
    s = New("m2a"); Set(s, "m2a_peak", 60); Set(s, "m2a_emph", 100);
    double lo = Run(s, 200, -12, 1.0) + 12, hi = Run(s, 10000, -12, 1.0) + 12; printf("   emphasis at maximum: 200 Hz %+.1f dB, 10 kHz %+.1f dB (target -1.9, -13.0)\n", lo, hi); CHECK(lo > hi + 6, "2A emphasis");
    E->destroy(s);
  }
  SEC("1b") {
    printf("== XXL-1B static curve\n");
    static const double T[4][6] = {{-.8, -3.1, -5.9, -9.2, -12.6, -16.0}, {-2.1, -5.0, -8.9, -13.7, -19.0, -24.6}, {-.5, -.8, -1.4, -2.9, -5.8, -9.4}, {-.4, -.4, -.5, -.7, -1.1, -2.1}};
    static const double thr[4] = {-22, -22, -10, 2}, ratio[4] = {2, 10, 4, 4};
    for (int i = 0; i < 4; ++i) { void* s = New("m1b"); Set(s, "m1b_thr", thr[i]); Set(s, "m1b_ratio", ratio[i]); char n[32]; snprintf(n, sizeof n, "thr %g dBu, %g:1", thr[i], ratio[i]); Curve(n, s, T[i], 2.2); E->destroy(s); }
    static const double a[5] = {1, 2, 10, 50, 100}, r[5] = {10, 30, 100, 1000, 4000};
    void* s = New("m1b"); Set(s, "m1b_thr", -22); Set(s, "m1b_ratio", 2); Timing("fixed", s, 1, a, 5, r, 5); E->destroy(s);
    s = New("m1b"); Set(s, "m1b_thr", -22); Set(s, "m1b_ratio", 2); Set(s, "m1b_time", 1); Set(s, "m1b_att", 10); Set(s, "m1b_rel", 10); Timing("manual 10 / 10", s, 1, a, 5, r, 5, 4.0); E->destroy(s);
    printf("      target fixed: 5.1 9.6 11.0 13.1 13.4 of 13.5 | 1.7 0.5 0 0 0;  manual 10/10: 0.3 1.0 3.6 10.7 13.5 of 15.5 | 15.5 15.5 15.3 13.5 8.5\n");
  }
  SEC("16") {
    printf("== XXL-16VU static curve\n");
    static const double T[3][6] = {{0, 0, -1.7, -4.7, -7.7, -10.7}, {0, 0, -3.4, -9.4, -15.3, -21.3}, {-2.9, -10.4, -14.9, -19.4, -23.9, -28.4}};
    static const double v[3] = {0.173, 0.173, 0.031}, ratio[3] = {50, 100, 75};
    for (int i = 0; i < 3; ++i) { void* s = New("m16"); Set(s, "m16_thr", 100 * log(v[i] / 0.01) / log(300.0)); Set(s, "m16_ratio", ratio[i]); char n[32]; snprintf(n, sizeof n, "%.3f V, knob %g", v[i], ratio[i]); Curve(n, s, T[i], 1.5); E->destroy(s); }
    void* s = New("m16"); Set(s, "m16_thr", 100 * log(0.173 / 0.01) / log(300.0)); Set(s, "m16_ratio", 100);
    static const double a[3] = {2, 10, 100}, r[3] = {100, 200, 300}; Timing("infinity", s, 2, a, 3, r, 3);
    printf("      target: 10 dB of 19 in 2 ms, settled by 100 ms | 8.3 left of 19.3 after 100 ms, gone by 300 ms\n");
    E->destroy(s);
  }
  SEC("76") {
    printf("== XXL-76: output level against input (input knob set for +16.7 dB of gain)\n");
    static const double T[3][6] = {{16.7, 16.7, 16.7, 14.6, 9.6, 4.7}, {16.7, 16.7, 16.7, 16.7, 13.2, 7.4}, {16.7, 16.7, 16.7, 16.7, 14.2, 8.4}};
    static const int ratio[3] = {1, 4, 5};
    for (int i = 0; i < 3; ++i) {
      void* s = New("m76"); Set(s, "m76_in", (16.7 + 12) / 0.48); Set(s, "m76_out", (24 - 20) / 0.48); Set(s, "m76_ratio", ratio[i]);
      char n[32]; snprintf(n, sizeof n, "ratio step %d (out -20 dB)", ratio[i]); Curve(n, s, T[i], 1.5, -20); E->destroy(s);
    }
    static const double a[3] = {1, 2, 5}, r[6] = {10, 30, 100, 300, 1000, 2000};
    for (int k = 1; k <= 7; k += 3) {
      void* s = New("m76"); Set(s, "m76_in", (29.3 + 12) / 0.48); Set(s, "m76_out", 0); Set(s, "m76_att", k); Set(s, "m76_rel", k);
      char n[32]; snprintf(n, sizeof n, "attack %d / release %d", k, k); Timing(n, s, 3, a, 3, r, 6); E->destroy(s);
    }
    printf("      target 1/1: 13.2 23.3 24.0 of 25.6 | 24.8 25.0 24.9 21.7 12.4 5.0;  7/7: 19.1 26.2 26.3 of 26.8 | 18.7 9.4 3.9 1.9 0.4 0\n");
    void* s = New("m76"); Set(s, "m76_in", (16.7 + 12) / 0.48); Set(s, "m76_out", (24 - 20) / 0.48);
    double h2, h3; Thd(s, -12, &h2, &h3); printf("   harmonics while limiting at -12 dBFS: 2nd %.0f dBc, 3rd %.0f dBc (target about -44, -50)\n", h2, h3);
    E->destroy(s);
  }
  SEC("67") {
    printf("== XXL-67 static curve\n");
    static const double T[3][6] = {{0, 0, -.2, -.6, -1.4, -2.8}, {0, -.4, -.9, -1.9, -3.8, -6.4}, {-.2, -.9, -1.9, -3.7, -6.5, -9.1}};
    static const double thr[3] = {25, 50, 100};
    for (int i = 0; i < 3; ++i) { void* s = New("m67"); Set(s, "m67_thr", thr[i]); char n[32]; snprintf(n, sizeof n, "threshold %g", thr[i]); Curve(n, s, T[i], 0.8); E->destroy(s); }
    static const double a[2] = {2, 10}, r[5] = {100, 300, 1000, 2000, 4000};
    for (int tc = 1; tc <= 6; ++tc) { void* s = New("m67"); Set(s, "m67_thr", 100); Set(s, "m67_tc", tc); char n[32]; snprintf(n, sizeof n, "time constant %d", tc); Timing(n, s, 4, a, 2, r, 5, 2.0); E->destroy(s); }
    printf("      target release 1: 2.9 0.3 0 0 0 | 3: 6.8 5.5 2.4 0.7 0 | 5: 6.8 5.8 4.4 3.1 1.6 | 6: 5.7 4.9 4.2 3.6 2.7  (of about 7.2)\n");
  }
  SEC("ds") {
    printf("== XXL-DISS: level change against input (input knob set for +8.4 dB)\n");
    static const double T[2][6] = {{8.4, 8.2, 7.5, 5.5, 1.6, -2.9}, {8.4, 8.4, 7.2, 2.9, -2.4, -7.8}};
    static const int ratio[2] = {1, 5};
    for (int i = 0; i < 2; ++i) { void* s = New("mds"); Set(s, "mds_in", 5 + 8.4 / 3); Set(s, "mds_ratio", ratio[i]); char n[32]; snprintf(n, sizeof n, "ratio step %d", ratio[i]); Curve(n, s, T[i], 1.5); E->destroy(s); }
    static const double a[4] = {1, 2, 10, 50}, r[5] = {30, 100, 300, 1000, 4000};
    for (int k = 0; k < 3; ++k) { void* s = New("mds"); Set(s, "mds_in", 5 + 17.9 / 3); Set(s, "mds_out", 0); Set(s, "mds_ratio", 5); Set(s, "mds_att", k * 5.25); Set(s, "mds_rel", k * 5.25); char n[32]; snprintf(n, sizeof n, "attack/release %g", k * 5.25); Timing(n, s, 5, a, 4, r, 5, 3.0); E->destroy(s); }
    printf("      target 0/0: 19.7 20.5 20.5 20.5 of 20.8 | 12.4 9.7 4.6 2.6 0.6;  mid: 10.9 18.5 20.4 20.6 | 19.1 16.5 13.4 8.1 2.2;  max: 4.9 6.9 13.5 19.2 | 20.1 18.9 16.8 14.1 12.5\n");
  }
  SEC("eq") {
    printf("== EQ modules, change in dB at 30 60 100 200 400 700 1k 2k 3.5k 5k 8k 12k 16k Hz\n");
    void* s;
    static const double t73a[13] = {15.4, 15.0, 13.2, 6.0, .9, .1, 0, 0, 0, 0, 0, 0, 0};
    s = New("m73"); Set(s, "m73_lf", 2); Set(s, "m73_lg", 15.4); EqRow("73 low 60 Hz max", s, t73a, 1.0); E->destroy(s);
    static const double t73b[13] = {.6, 2.1, 4.4, 9.3, 15.6, 19.2, 17.4, 11, 6.5, 4.2, 2.1, 1, .5};
    s = New("m73"); Set(s, "m73_mf", 2); Set(s, "m73_mg", 18); EqRow("73 presence 700 max", s, t73b, 1.0); E->destroy(s);
    static const double t73c[13] = {0, 0, 0, 0, .2, .6, 1.2, 4.7, 10.2, 13.8, 16.9, 18.2, 18.6};
    s = New("m73"); Set(s, "m73_hg", 18); EqRow("73 high shelf max", s, t73c, 1.2); E->destroy(s);
    static const double t73d[13] = {-25, -5.6, -1.1, -.6, -.2, -.1, 0, 0, 0, 0, 0, 0, 0};
    s = New("m73"); Set(s, "m73_hpf", 2); EqRow("73 high-pass 80", s, t73d, 3.5); E->destroy(s);
    static const double t55a[13] = {12.6, 11.3, 9.3, 5.7, 2.4, 1, .5, .1, 0, 0, 0, 0, 0};
    s = New("m55"); Set(s, "m55_lf", 0); Set(s, "m55_lg", 10); EqRow("55A low 50 shelf +12", s, t55a, 1.0); E->destroy(s);
    static const double t55b[13] = {0, .1, .2, .8, 2.7, 6.3, 9.6, 10, 5, 2.9, 1.3, .6, .3};
    s = New("m55"); Set(s, "m55_mg", 10); EqRow("55A mid 1.5k +12", s, t55b, 1.0); E->destroy(s);
    static const double t55c[13] = {0, 0, 0, .1, .2, .4, .7, 2.3, 4.7, 6.7, 9.1, 10.8, 11.6};
    s = New("m55"); Set(s, "m55_hf", 4); Set(s, "m55_hg", 10); EqRow("55A high 15k shelf +12", s, t55c, 1.0); E->destroy(s);
    static const double t56[13] = {0, 0, .1, .6, 2.6, 9.8, 12.5, 6.3, 1.6, .7, .3, .1, 0};
    s = New("m56"); Set(s, "m56_b6", 12); EqRow("56 1 kHz band +12", s, 0, 0);
    double a = Resp(s, 700), b = Resp(s, 1000), c = Resp(s, 2000); CHECK(fabs(a - 9.8) < 1 && fabs(b - 12.5) < 1 && fabs(c - 6.3) < 1, "56 band shape"); (void)t56;
    Set(s, "m56_rng", 1); printf("   56 same band, 6 dB range: %+.1f dB at 1 kHz (target +5.1)\n", Resp(s, 1000)); E->destroy(s);
    static const double tq1a[13] = {13.1, 11.9, 10.1, 6.4, 2.9, 1.2, .6, .2, 0, 0, 0, 0, 0};
    s = New("mq1"); Set(s, "mq1_lb", 10); EqRow("EQ1-A low boost 10", s, tq1a, 1.0); E->destroy(s);
    static const double tq1b[13] = {-17.9, -16.9, -15.3, -11.6, -6.9, -3.7, -2.2, -.7, -.2, -.1, 0, 0, 0};
    s = New("mq1"); Set(s, "mq1_la", 10); EqRow("EQ1-A low atten 10", s, tq1b, 1.0); E->destroy(s);
    static const double tq1c[13] = {-1.1, -1.1, -1.1, -1, -.9, -.5, .1, 2.5, 6.3, 9.4, 12, 9.3, 6.5};
    s = New("mq1"); Set(s, "mq1_hb", 10); EqRow("EQ1-A high boost 10", s, tq1c, 1.5); E->destroy(s);
    static const double tq1d[13] = {.1, .1, .1, 0, -.3, -.9, -1.8, -4.9, -8.3, -10.5, -13, -14.4, -15.1};
    s = New("mq1"); Set(s, "mq1_ha", 10); EqRow("EQ1-A high atten 10", s, tq1d, 1.2); E->destroy(s);
    s = New("mq1"); Set(s, "mq1_lb", 10); Set(s, "mq1_la", 10); EqRow("EQ1-A boost + atten", s, 0, 0); E->destroy(s);
    static const double tq5a[13] = {.1, .4, 1.1, 3.8, 9.6, 8.6, 5.4, 1.7, .6, .3, .1, 0, 0};
    s = New("mq5"); Set(s, "mq5_lb", 10); EqRow("MQ-5 low peak 500", s, tq5a, 1.0); E->destroy(s);
    static const double tq5b[13] = {0, 0, -.1, -.5, -2, -6.5, -10.9, -3.5, -1.1, -.5, -.2, -.1, 0};
    s = New("mq5"); Set(s, "mq5_dp", 10); EqRow("MQ-5 dip 1 kHz", s, tq5b, 1.0); E->destroy(s);
    s = New("m73"); Set(s, "m73_gain", 2.65); double h2, h3; Thd(s, -6, &h2, &h3); printf("   73 drive at -6 dBFS, gain +2.65: 2nd %.0f dBc, 3rd %.0f dBc (target -52, -62)\n", h2, h3); E->destroy(s);
    s = New("mq1"); Thd(s, -6, &h2, &h3); printf("   EQ1-A flat at -6 dBFS: 2nd %.0f dBc (target -56)\n", h2); E->destroy(s);
  }
  SEC("tape") {
    printf("== tape: level change and harmonics at 1 kHz (input level through REC LEVEL where it passes full scale)\n");
    for (int m = 0; m < 2; ++m) {
      const char* key = m ? "mat" : "ma8";
      static const double lv[4] = {-24, -12, -6, 0}, tg[2][4] = {{-.1, -.5, -.8, -1.5}, {.1, .4, .4, -.5}}, t3[2][4] = {{-50, -41, -37, -29}, {-48, -43, -52, -26}};
      for (int i = 0; i < 4; ++i) {
        void* s = New(key); char k[16];
        snprintf(k, sizeof k, "%s_in", key); Set(s, k, 6); snprintf(k, sizeof k, "%s_out", key); Set(s, k, -12);
        double g = Run(s, 1000, lv[i] - 6, 0.5) - (lv[i] - 6) + 6, h2, h3; Thd(s, lv[i] - 6, &h2, &h3);
        printf("   %s at %+3.0f dBFS: level %+.1f dB (target %+.1f), 2nd %.0f, 3rd %.0f dBc (target %.0f)\n", m ? "AT12" : "A80 ", lv[i], g, tg[m][i], h2, h3, t3[m][i]);
        if (m == 0) CHECK(fabs(g - tg[m][i]) < 1.0 && fabs(h3 - t3[m][i]) < 7, "A80 saturation");
        E->destroy(s);
      }
    }
    static const double F[8] = {20, 30, 50, 100, 1000, 10000, 15000, 20000};
    for (int m = 0; m < 2; ++m) for (int sp = 0; sp < (m ? 4 : 3); ++sp) {
      void* s = New(m ? "mat" : "ma8"); Set(s, m ? "mat_spd" : "ma8_spd", sp);
      double ref = Resp(s, 1000);
      printf("   %s speed %d, dB at 20 30 50 100 1k 10k 15k 20k:", m ? "AT12" : "A80 ", sp);
      for (int i = 0; i < 8; ++i) printf(" %+5.1f", Resp(s, F[i]) - ref);
      printf("\n"); E->destroy(s);
    }
    printf("      target A80: 7.5 +2.6 +1.3 +0.1 -0.2 | 15 +2.2 +3.0 +2.0 +0.2 | 30 +1.4 +2.4 +3.9 +2.4; AT12 3.75 -2.7 .. -3.7 -11.5 -21.2 | 30 -6.5 -4.6 0\n");
  }
  SEC("rev") {
    printf("== XXL-224 (decay in the low / mid / high band)\n");
    static const char* n224[8] = {"Small Hall", "Bright Hall", "Large Hall", "Room", "Chamber", "Plate A", "Plate B", "Plate C"};
    double rt[3];
    for (int p = 0; p < 8; ++p) { void* s = New("m22"); Set(s, "m22_prog", p); Reverb(n224[p], s, 6.0, rt); if (!p) CHECK(rt[0] > 2.2 && rt[0] < 3.8 && rt[1] > 1.8 && rt[1] < 3.0 && rt[2] > 1.0 && rt[2] < 2.4, "224 default decay times"); E->destroy(s); }
    printf("      target: low 2.8-3.2, mid 2.1-2.5, high 1.3-1.9 s; halls first 4 ms, 63-75 %% early; chamber 16 ms, 11 %%; plates 24-30 %%\n");
    void* s = New("m22"); Set(s, "m22_bass", 0); Set(s, "m22_mid", 0); Reverb("bass, mid at 0", s, 4.0, rt); CHECK(rt[1] < 1.3, "224 short decay"); E->destroy(s);
    s = New("m22"); Set(s, "m22_mid", 62); Reverb("mid at 62 (11 s)", s, 14.0, rt); CHECK(rt[1] > 4.5, "224 long decay"); E->destroy(s);
    s = New("m22"); Set(s, "m22_depth", 71); Reverb("depth 71", s, 6.0, rt); E->destroy(s);
    s = New("m22"); Set(s, "m22_prog", 8); double c = Run(s, 440, -12, 0.5); printf("   Chorus: %.1f dBFS out for -12 in\n", c); CHECK(c > -30, "224 chorus"); E->destroy(s);
    printf("== XXL-480R\n");
    static const char* n480[16] = {"Small Hall", "Medium Hall", "Large Hall", "Dark Hall", "Small Room", "Large Room", "Wood Room", "Chamber", "Bright Plate", "Dark Plate", "Random Hall", "Random Space", "Ambience", "Tight Amb", "Post Amb", "Wide Space"};
    for (int p = 0; p < 16; ++p) { s = New("m48"); Set(s, "m48_prog", p); Reverb(n480[p], s, 6.0, rt); if (p == 1) CHECK(rt[1] > 1.4 && rt[1] < 2.6, "480R default decay"); E->destroy(s); }
    printf("      target: halls 1.8-2.4 s with little early energy; rooms and plates sooner and denser; ambience short\n");
  }
  printf("%s\n", fails ? "FAILED" : "PASSED");
  return fails ? 1 : 0;
}
