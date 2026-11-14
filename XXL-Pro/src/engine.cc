// SPDX-License-Identifier: GPL-3.0-or-later
// XXL Pro ("Pro" is for Process) -- fifteen process modules in one effect for MPC OS / Force (mpc-vst-plugins engine).
//
//   IN -> [any modules, any order, summed where cables meet] -> OUT -> output level
//
// Any module's output can be patched into any other module's input and into OUT; one cable carries left and right;
// an input sums its cables; a loop is refused. There is NO built-in dry path: dry runs only while IN is patched to OUT.
// A module runs only while it sits in the signal path (fed from IN and reaching OUT).
//
// The limit rule: (1) every module has a known cost; a cable that would bring the cost of the modules in the path over
// the budget is refused. (2) A live guard measures the audio work; if it stays over the limit, the module that joined
// the path last is taken out with a fade (a reverb goes silent, anything else passes its input) until the patch changes.
//
// The UI side lives here too (the page, the patch bay's tap-tap patching, the status texts, 16 Q-Link knobs that
// follow the page): that structure and the patch bay are PhyXXL's. The DSP is src/pro_dsp.h.
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <new>

extern "C" {
#include "engine.h"
}
#include "param_ids.h"
#include "denormals.h"
#include "pro_dsp.h"

namespace {

using namespace xxl;

const int kMaxBlock = 128;
const float kGuardLoad = 0.80f;      // the audio work may not stay above this share of real time ...
const int kGuardBlocks = 150;        // ... for this many blocks in a row (about 0.4 s)

inline float clampf(float x, float lo, float hi) { return x < lo ? lo : (x > hi ? hi : x); }
inline bool bad(float x) { return !(x == x) || x > 1e6f || x < -1e6f; }

struct Plug {
  float pv[P_COUNT];
  int view = 0;
  // patch bay UI
  int pk = 0;                       // 0 off, 1 choose, 2 an output waits, 3 an input waits, 4 connected
  int held_out = -1, held_in = -1;
  unsigned rev = 1;
  char info[96], touch[96];
  int last_touch = -1;
  int nav_cool = 0;
  // graph
  bool acc[N_AO][N_AI];             // accepted cables (loop-free, within the cost budget)
  int order[N_MOD], n_order = 0;
  bool active[N_MOD], was_active[N_MOD];
  int cost = 0;
  unsigned act_seq[N_MOD], seq = 0;  // when each module joined the path (the guard takes out the latest)
  bool tripped[N_MOD];
  float wet[N_MOD];                 // 1 = running, glides to 0 when the guard takes the module out
  bool dirty = true;
  // modules
  M2A m2a; M1B m1b; M16 m16; M76 m76; M67 m67; MDiss mds; M73 m73; M55 m55; M56 m56; MEq1 mq1; MMq5 mq5;
  Tape ma8, mat; Reverb m22, m48;
  float buf[N_MOD][2][kMaxBlock];
  // output, meters, guard
  Glide out_gain, dry_gain;
  float meter_in = 0, meter_out = 0, cpu = 0;
  int lamp_in = 0, lamp_out = 0, lamp_cpu = 0, lamp_gr = -1, lamp_clock = 0, lamp_vu = 0;
  float view_ms = 0;   // mean square of the viewed module's output (the VU of the tape machines)
  int over_blocks = 0;
  bool guard_on = true;

  void init() {
    for (int i = 0; i < P_COUNT; i++) pv[i] = P_DEF[i];
    memset(active, 0, sizeof active); memset(was_active, 0, sizeof was_active);
    memset(tripped, 0, sizeof tripped); memset(act_seq, 0, sizeof act_seq);
    for (int m = 0; m < N_MOD; m++) wet[m] = 1.0f;
    snprintf(info, sizeof info, "Tap a socket, then the other end of the cable.");
    touch[0] = 0;
    reset_all();
    rebuild();
    configure();
  }
  inline int Pi(int i) const { return (int)lroundf(pv[i]); }
  inline bool on(int i) const { return Pi(i) != 0; }
  void bump() { rev++; }

  void reset_module(int m) {
    switch (m) {
      case M_2A: m2a.Reset(); break;  case M_1B: m1b.Reset(); break;  case M_16: m16.Reset(); break;
      case M_76: m76.Reset(); break;  case M_67: m67.Reset(); break;  case M_DS: mds.Reset(); break;
      case M_73: m73.Reset(); break;  case M_55: m55.Reset(); break;  case M_56: m56.Reset(); break;
      case M_Q1: mq1.Reset(); break;  case M_Q5: mq5.Reset(); break;  case M_A8: ma8.Reset(); break;
      case M_AT: mat.Reset(); break;  case M_22: m22.Reset(); break;  default: m48.Reset(); break;
    }
  }
  void reset_all() { for (int m = 0; m < N_MOD; m++) reset_module(m); }

  // ---- the controls -> the modules ------------------------------------------------------------------------------------
  static float log_knob(float k, float lo, float hi) { return lo * powf(hi / lo, k * 0.01f); }
  void configure() {
    const float *p = pv;
    m2a.Set(p[P_M2A_PEAK], p[P_M2A_GAIN], on(P_M2A_MODE), p[P_M2A_EMPH], on(P_M2A_LINK));
    m1b.Set(p[P_M1B_THR], p[P_M1B_GAIN], p[P_M1B_RATIO], Pi(P_M1B_TIME), p[P_M1B_ATT], p[P_M1B_REL], on(P_M1B_LINK));
    m16.Set(p[P_M16_THR], p[P_M16_RATIO], p[P_M16_OUT], on(P_M16_LINK));
    m76.Set(p[P_M76_IN], p[P_M76_OUT], Pi(P_M76_ATT), Pi(P_M76_REL), Pi(P_M76_RATIO), on(P_M76_REV), on(P_M76_LINK));
    m67.Set(p[P_M67_IN], p[P_M67_THR], Pi(P_M67_TC), p[P_M67_OUT], on(P_M67_MS), on(P_M67_LINK));
    mds.Set(p[P_MDS_IN], p[P_MDS_ATT], p[P_MDS_REL], p[P_MDS_OUT], Pi(P_MDS_RATIO), Pi(P_MDS_DET), Pi(P_MDS_AUD), on(P_MDS_LINK));
    m73.Set(p[P_M73_GAIN], p[P_M73_OUT], Pi(P_M73_HPF), Pi(P_M73_LF), p[P_M73_LG], Pi(P_M73_MF), p[P_M73_MG], p[P_M73_HG],
            on(P_M73_EQ), on(P_M73_PH));
    m55.Set(Pi(P_M55_LF), Pi(P_M55_LG), on(P_M55_LB), Pi(P_M55_MF), Pi(P_M55_MG), Pi(P_M55_HF), Pi(P_M55_HG), on(P_M55_HB),
            on(P_M55_FLT), on(P_M55_EQ), on(P_M55_PH), p[P_M55_OUT]);
    m56.Set(p + P_M56_B1, on(P_M56_EQ), on(P_M56_RNG), p[P_M56_OUT]);
    mq1.Set(Pi(P_MQ1_LF), p[P_MQ1_LB], p[P_MQ1_LA], Pi(P_MQ1_HF), p[P_MQ1_HB], p[P_MQ1_BW], Pi(P_MQ1_AF), p[P_MQ1_HA],
            on(P_MQ1_IN), p[P_MQ1_OUT]);
    mq5.Set(Pi(P_MQ5_LF), p[P_MQ5_LB], Pi(P_MQ5_DF), p[P_MQ5_DP], Pi(P_MQ5_HF), p[P_MQ5_HB], on(P_MQ5_IN), p[P_MQ5_OUT]);
    ma8.Set(false, p[P_MA8_IN], p[P_MA8_OUT], Pi(P_MA8_SPD), Pi(P_MA8_TYPE), p[P_MA8_BIAS], p[P_MA8_RHF], p[P_MA8_PHF],
            p[P_MA8_PLF], p[P_MA8_WOW], p[P_MA8_FLUT], on(P_MA8_HISS), on(P_MA8_PATH), 1);
    mat.Set(true, p[P_MAT_IN], p[P_MAT_OUT], Pi(P_MAT_SPD), Pi(P_MAT_TYPE), p[P_MAT_BIAS], p[P_MAT_RHF], p[P_MAT_PHF],
            p[P_MAT_PLF], p[P_MAT_WOW], p[P_MAT_FLUT], on(P_MAT_HISS), on(P_MAT_PATH), Pi(P_MAT_HEAD));
    ReverbSettings a;
    a.prog = &kProg224[Pi(P_M22_PROG)]; a.chorus = Pi(P_M22_PROG) == 8;
    a.rt_low = log_knob(p[P_M22_BASS], 0.6f, 70.0f); a.rt_mid = log_knob(p[P_M22_MID], 0.6f, 70.0f);
    a.xover_hz = log_knob(p[P_M22_XOV], 100.0f, 10900.0f);
    a.damp_hz = log_knob(p[P_M22_TREB], 100.0f, 10900.0f); a.damp = p[P_M22_TREB] < 99.5f;
    float depth = p[P_M22_DEPTH] / 71.0f;
    a.predelay_ms = p[P_M22_PRE] + depth * 41.0f; a.early_scale = 1.0f - 0.9f * depth;
    a.diffusion = (p[P_M22_DIFF] - 1.0f) / 62.0f;
    a.move_depth = on(P_M22_MOD) ? 1.0f : 0.0f; a.move_hz = 0.7f;
    a.level_db = p[P_M22_LVL];
    m22.Set(a);
    ReverbSettings b;
    b.prog = &kProg480[Pi(P_M48_PROG)];
    b.rt_mid = log_knob(p[P_M48_RT], 0.3f, 30.0f); b.rt_low = b.rt_mid * log_knob(p[P_M48_BM], 0.25f, 4.0f);
    b.xover_hz = log_knob(p[P_M48_XOV], 100.0f, 5000.0f);
    b.damp_hz = log_knob(p[P_M48_RTHC], 500.0f, 20000.0f); b.damp = p[P_M48_RTHC] < 99.5f;
    b.out_lp_hz = log_knob(p[P_M48_HFC], 500.0f, 20000.0f);
    b.predelay_ms = p[P_M48_PRE];
    b.late_ms = p[P_M48_SPREAD] * 0.6f * b.prog->scale;                 // SPREAD: how long the tail takes to arrive
    b.early_scale = 2.0f * (1.0f - p[P_M48_SHAPE] * 0.01f); b.late_scale = 0.5f + p[P_M48_SHAPE] * 0.01f;   // SHAPE: early against late
    b.size = 0.5f + p[P_M48_SIZE] * 0.01f * 0.8333f;                    // 60 = x1
    b.diffusion = p[P_M48_DIFF] * 0.01f;
    b.move_hz = 0.15f + p[P_M48_SPIN] * 0.02f; b.move_depth = p[P_M48_WAND] * 0.03f;
    b.level_db = p[P_M48_LVL];
    m48.Set(b);
    dry_gain.Set(pv[P_DRY_LEVEL] <= -59.5f ? 0.0f : DbToLin(pv[P_DRY_LEVEL]));
    out_gain.Set(on(P_BYPASS) ? 1.0f : (pv[P_OUT_LEVEL] <= -23.9f ? 0.0f : DbToLin(pv[P_OUT_LEVEL])));
    dirty = false;
  }

  void run_module(int m, float *l, float *r, int n) {
    switch (m) {
      case M_2A: m2a.Process(l, r, n); break;  case M_1B: m1b.Process(l, r, n); break;  case M_16: m16.Process(l, r, n); break;
      case M_76: m76.Process(l, r, n); break;  case M_67: m67.Process(l, r, n); break;  case M_DS: mds.Process(l, r, n); break;
      case M_73: m73.Process(l, r, n); break;  case M_55: m55.Process(l, r, n); break;  case M_56: m56.Process(l, r, n); break;
      case M_Q1: mq1.Process(l, r, n); break;  case M_Q5: mq5.Process(l, r, n); break;  case M_A8: ma8.Process(l, r, n); break;
      case M_AT: mat.Process(l, r, n); break;  case M_22: m22.Process(l, r, n); break;  default: m48.Process(l, r, n); break;
    }
  }
  float module_gr(int m) const {
    switch (m) {
      case M_2A: return m2a.core.max_gr();  case M_1B: return m1b.core.max_gr();  case M_16: return m16.core.max_gr();
      case M_76: return m76.core.max_gr();  case M_67: return m67.core.max_gr();  case M_DS: return mds.core.max_gr();
      default: return 0;
    }
  }

  // ---- the graph -----------------------------------------------------------------------------------------------------
  bool reach(int from, int to) const {   // can module `from` reach module `to` through accepted cables
    if (from == to) return true;
    bool seen[N_MOD] = {};
    int stack[N_MOD], sp = 0;
    stack[sp++] = from; seen[from] = true;
    while (sp) {
      int x = stack[--sp];
      for (int y = 0; y < N_MOD; y++)
        if (acc[x + 1][y] && !seen[y]) { if (y == to) return true; seen[y] = true; stack[sp++] = y; }
    }
    return false;
  }
  bool would_loop(int a, int b) const { return b < N_MOD && a >= 1 && (a - 1 == b || reach(b, a - 1)); }

  // which modules are in the signal path (fed from IN and reaching OUT) for the accepted cables; returns their cost
  int path(bool *act) const {
    bool fed[N_MOD] = {}, to_out[N_MOD] = {};
    for (int pass = 0; pass < N_MOD; pass++)
      for (int f = 0; f < N_MOD; f++) {
        if (fed[f]) continue;
        if (acc[0][f]) fed[f] = true;
        for (int a = 1; a < N_AO && !fed[f]; a++) if (acc[a][f] && fed[a - 1]) fed[f] = true;
      }
    for (int pass = 0; pass < N_MOD; pass++)
      for (int f = 0; f < N_MOD; f++) {
        if (to_out[f]) continue;
        if (acc[f + 1][N_MOD]) to_out[f] = true;
        for (int b = 0; b < N_MOD && !to_out[f]; b++) if (acc[f + 1][b] && to_out[b]) to_out[f] = true;
      }
    int c = 0;
    for (int f = 0; f < N_MOD; f++) { act[f] = fed[f] && to_out[f]; if (act[f]) c += MOD_COST[f]; }
    return c;
  }
  // would this cable bring the path over the cost budget?
  bool would_overload(int a, int b) {
    if (acc[a][b]) return false;
    bool act[N_MOD];
    acc[a][b] = true;
    int c = path(act);
    acc[a][b] = false;
    return c > COST_BUDGET;
  }

  void rebuild() {
    memset(acc, 0, sizeof acc);
    bool act[N_MOD];
    for (int a = 0; a < N_AO; a++)
      for (int b = 0; b < N_AI; b++) {
        if (!on(F_AC + a * N_AI + b) || would_loop(a, b)) continue;
        acc[a][b] = true;
        if (path(act) > COST_BUDGET) acc[a][b] = false;   // the limit rule, part 1
      }
    bool done[N_MOD] = {};
    n_order = 0;
    for (int pass = 0; pass < N_MOD; pass++)
      for (int f = 0; f < N_MOD; f++) {
        if (done[f]) continue;
        bool ready = true;
        for (int a = 1; a < N_AO; a++) if (acc[a][f] && !done[a - 1]) ready = false;
        if (ready) { done[f] = true; order[n_order++] = f; }
      }
    cost = path(act);
    for (int f = 0; f < N_MOD; f++) {
      if (act[f] && !active[f]) act_seq[f] = ++seq;
      active[f] = act[f];
    }
  }
  // the patch changed by hand (or a state was loaded): modules the guard took out get another go
  void clear_trips() { memset(tripped, 0, sizeof tripped); over_blocks = 0; }

  void set_cable(int a, int b, bool v) {
    if (v && a == b + 1) return;
    pv[F_AC + a * N_AI + b] = v ? 1.0f : 0.0f;
    clear_trips(); rebuild(); bump();
  }
  void clear_audio() {
    for (int i = 0; i < N_AO * N_AI; i++) pv[F_AC + i] = 0;
    clear_trips(); rebuild(); bump();
  }

  // the limit rule, part 2: take the module that joined the path last out of it
  bool trip_latest() {
    int best = -1;
    for (int m = 0; m < N_MOD; m++)
      if (active[m] && !tripped[m] && (best < 0 || act_seq[m] > act_seq[best])) best = m;
    if (best < 0) return false;
    tripped[best] = true;
    snprintf(info, sizeof info, "LIMIT: %s taken out of the path. Change the patch to bring it back.", MOD_NAME[best]);
    snprintf(touch, sizeof touch, "LIMIT: %s OUT", MOD_NAME[best]);
    bump();
    return true;
  }

  // ---- audio ----------------------------------------------------------------------------------------------------------
  void block(const int16_t *in, int16_t *out, int n) {
    if (dirty) configure();
    float inb[2][kMaxBlock], dry[2][kMaxBlock], ol[kMaxBlock], orr[kMaxBlock];
    float pk = 0;
    for (int i = 0; i < n; i++) {
      float l = in[i * 2] * (1.0f / 32768.0f), r = in[i * 2 + 1] * (1.0f / 32768.0f);
      inb[0][i] = l; inb[1][i] = r;
      float a = fmaxf(fabsf(l), fabsf(r));
      if (a > pk) pk = a;
    }
    if (pk > meter_in) meter_in = pk;
    for (int k = 0; k < n_order; k++) {
      int m = order[k];
      if (!active[m]) { was_active[m] = false; continue; }
      if (!was_active[m]) { reset_module(m); was_active[m] = true; wet[m] = tripped[m] ? 0.0f : 1.0f; }
      float *l = buf[m][0], *r = buf[m][1];
      memset(l, 0, sizeof(float) * n); memset(r, 0, sizeof(float) * n);
      for (int a = 0; a < N_AO; a++) {
        if (!acc[a][m]) continue;
        const float *sl = a == 0 ? inb[0] : buf[a - 1][0], *sr = a == 0 ? inb[1] : buf[a - 1][1];
        if (a > 0 && !active[a - 1]) continue;
        for (int i = 0; i < n; i++) { l[i] += sl[i]; r[i] += sr[i]; }
      }
      float target = tripped[m] ? 0.0f : 1.0f;
      bool fading = wet[m] != target;
      if (target == 0.0f && !fading) {                       // out of the path: a reverb is silent, anything else passes
        if (MOD_IS_REVERB[m]) { memset(l, 0, sizeof(float) * n); memset(r, 0, sizeof(float) * n); }
        continue;
      }
      if (fading) { memcpy(dry[0], l, sizeof(float) * n); memcpy(dry[1], r, sizeof(float) * n); }
      run_module(m, l, r, n);
      bool broken = false;
      for (int i = 0; i < n; i++) if (bad(l[i]) || bad(r[i])) broken = true;
      if (broken) { reset_module(m); memset(l, 0, sizeof(float) * n); memset(r, 0, sizeof(float) * n); }
      if (m == view - 1) {                                    // the viewed module's level, with a VU's 300 ms rise
        float e = 0;
        for (int i = 0; i < n; i++) e += l[i] * l[i] + r[i] * r[i];
        view_ms += (e / (2.0f * n) - view_ms) * (1.0f - expf(-(float)n / (0.3f * kSR)));
      }
      if (fading) {
        float w = wet[m], step = (target > w ? 1.0f : -1.0f) / (0.02f * kSR), d = MOD_IS_REVERB[m] ? 0.0f : 1.0f;
        for (int i = 0; i < n; i++) {
          w = clampf(w + step, 0.0f, 1.0f);
          l[i] = l[i] * w + dry[0][i] * (1.0f - w) * d; r[i] = r[i] * w + dry[1][i] * (1.0f - w) * d;
        }
        wet[m] = w;
      }
    }
    for (int i = 0; i < n; i++) { ol[i] = 0; orr[i] = 0; }
    for (int a = 0; a < N_AO; a++) {
      if (!acc[a][N_MOD]) continue;
      if (a == 0) for (int i = 0; i < n; i++) { float d = dry_gain.Tick(); ol[i] += inb[0][i] * d; orr[i] += inb[1][i] * d; }   // the dry cable, at DRY LEVEL
      else if (active[a - 1]) for (int i = 0; i < n; i++) { ol[i] += buf[a - 1][0][i]; orr[i] += buf[a - 1][1][i]; }
    }
    bool byp = on(P_BYPASS);
    float po = 0;
    for (int i = 0; i < n; i++) {
      float g = out_gain.Tick();
      float s[2] = {byp ? inb[0][i] : ol[i] * g, byp ? inb[1][i] : orr[i] * g};
      for (int c = 0; c < 2; c++) {
        float x = s[c], a = fabsf(x);
        if (a > 1.0f) { a = 1.0f; x = x < 0 ? -1.0f : 1.0f; }   // full scale is the ceiling
        if (a > po) po = a;
        out[i * 2 + c] = (int16_t)lrintf(x * 32767.0f);
      }
    }
    if (po > meter_out) meter_out = po;
  }

  void process(const int16_t *in, int16_t *out, int frames) {
    ScopedDenormalDisable dg;
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int off = 0; off < frames; off += kMaxBlock) {
      int n = frames - off < kMaxBlock ? frames - off : kMaxBlock;
      block(in + off * 2, out + off * 2, n);
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double dt = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) * 1e-9;
    float load = (float)(dt / (frames / (double)kSR));
    cpu += (load - cpu) * 0.05f;
    if (guard_on && cpu > kGuardLoad) {
      if (++over_blocks >= kGuardBlocks) { over_blocks = 0; trip_latest(); }
    } else over_blocks = 0;
    lamp_clock += frames;
    if (lamp_clock >= 2205) {      // lamps, needles and texts: at most every 50 ms
      lamp_clock = 0;
      auto seg = [](float p) { float db = 20.0f * log10f(fmaxf(p, 1e-5f)); return (int)clampf((db + 54.0f) / 6.0f, 0, 8.0f); };
      int mi = seg(meter_in), mo = seg(meter_out), cp = (int)(cpu * 100.0f);
      meter_in *= 0.5f; meter_out *= 0.5f;
      bool ch = false;
      if (view == V_OVERVIEW && (mi != lamp_in || mo != lamp_out || cp != lamp_cpu)) ch = true;
      lamp_in = mi; lamp_out = mo; lamp_cpu = cp;
      if (view >= 1 && view <= N_MOD && MOD_IS_COMP[view - 1]) {
        int g = (int)lroundf(module_gr(view - 1) * 10.0f);
        if (g != lamp_gr) { lamp_gr = g; ch = true; }
      }
      int vu = 0;                    // the module page's meter: 0..31
      if (view >= 1 && view <= N_MOD && active[view - 1] && !tripped[view - 1]) {
        int m = view - 1;
        if (m == M_DS) vu = (int)clampf(lroundf(module_gr(m)), 0, 16);                       // lamps: 1 dB each
        else if (MOD_IS_COMP[m] || MOD_IS_TAPE[m]) {                                          // needle: voltage on a VU scale
          float v = MOD_IS_COMP[m] ? powf(10.0f, -module_gr(m) / 20.0f) : sqrtf(view_ms) / 0.126f;   // 0 VU = no reduction / -18 dBFS
          vu = (int)lroundf(clampf((v - 0.1f) / 1.3125f, 0, 1) * 31.0f);
        }
      } else view_ms = 0;
      if (vu != lamp_vu) { lamp_vu = vu; ch = true; }
      if (nav_cool > 0) nav_cool--;
      if (ch) bump();
    }
  }

  // ---- UI: views ------------------------------------------------------------------------------------------------------
  void set_view(int v) {
    if (v < 0 || v >= N_VIEWS || v == view) return;
    view = v;
    touch[0] = 0;
    held_out = held_in = -1;
    pk = v == V_BAY ? 1 : 0;
    lamp_gr = -1;
    if (v == V_BAY) snprintf(info, sizeof info, "Tap a socket, then the other end of the cable.");
    bump();
  }
  void cancel_pick() {
    held_out = held_in = -1;
    pk = view == V_BAY ? 1 : 0;
    snprintf(info, sizeof info, "Tap a socket, then the other end of the cable.");
    bump();
  }
  void unplug_pair() {
    if (pk == 4 && view == V_BAY && held_out >= 0 && held_in >= 0) {
      set_cable(held_out, held_in, false);
      snprintf(info, sizeof info, "%s to %s unplugged", AO_LABEL[held_out], AI_LABEL[held_in]);
      held_out = held_in = -1; pk = 1; bump();
    } else cancel_pick();
  }
  // 0 free, 1 a loop, 2 over the limit
  int aud_blocked(int a, int b) { return (a == b + 1 || would_loop(a, b)) ? 1 : (would_overload(a, b) ? 2 : 0); }
  void connect_audio(int a, int b) {
    bool had = on(F_AC + a * N_AI + b);
    if (!had) set_cable(a, b, true);
    held_out = a; held_in = b; pk = 4;
    snprintf(info, sizeof info, "%s  >  %s%s", AO_LABEL[a], AI_LABEL[b], had ? "   (already patched)" : "");
    bump();
  }
  void refuse(int why) {
    snprintf(info, sizeof info, why == 2 ? "LIMIT: that cable would overload the plugin. Unplug a module first."
                                         : "That cable would make a loop.");
    bump();
  }
  void pick_aud(bool is_out, int idx) {
    if (view != V_BAY || pk < 1 || pk > 3) return;
    if (pk == 1) {
      if (is_out) { held_out = idx; pk = 2; snprintf(info, sizeof info, "%s: now tap an input", AO_LABEL[idx]); }
      else { held_in = idx; pk = 3; snprintf(info, sizeof info, "%s: now tap an output", AI_LABEL[idx]); }
      bump();
      return;
    }
    if (pk == 2) {
      if (is_out) { if (idx == held_out) cancel_pick(); else { held_out = idx; snprintf(info, sizeof info, "%s: now tap an input", AO_LABEL[idx]); bump(); } return; }
      int why = aud_blocked(held_out, idx);
      if (why) { refuse(why); return; }
      connect_audio(held_out, idx);
      return;
    }
    if (!is_out) { if (idx == held_in) cancel_pick(); else { held_in = idx; snprintf(info, sizeof info, "%s: now tap an output", AI_LABEL[idx]); bump(); } return; }
    int why = aud_blocked(idx, held_in);
    if (why) { refuse(why); return; }
    connect_audio(idx, held_in);
  }
  // a socket: 0 plain, 1 fits (ring), 2 blocked (dim)
  int jack_state(bool is_out, int idx) {
    if (view != V_BAY) return 0;
    if (pk == 2) { if (is_out) return idx == held_out ? 0 : 2; return aud_blocked(held_out, idx) ? 2 : 1; }
    if (pk == 3) { if (!is_out) return idx == held_in ? 0 : 2; return aud_blocked(idx, held_in) ? 2 : 1; }
    return 0;
  }

  // ---- value text -----------------------------------------------------------------------------------------------------
  static void hz_text(float hz, char *b, int n) {
    if (hz >= 1000.0f) snprintf(b, n, "%.1f kHz", hz / 1000.0f); else snprintf(b, n, "%d Hz", (int)lroundf(hz));
  }
  static void sec_text(float s, char *b, int n) { if (s < 10.0f) snprintf(b, n, "%.1f s", s); else snprintf(b, n, "%d s", (int)lroundf(s)); }
  void display(int p, char *buf, int n) const {
    float v = pv[p];
    if (P_VALS[p]) { snprintf(buf, n, "%s", P_VALS[p][(int)clampf(roundf(v), 0, P_MAX[p])]); return; }
    switch (p) {
      case P_DRY_LEVEL: if (v <= -59.5f) snprintf(buf, n, "Off"); else snprintf(buf, n, "%+.1f dB", v); return;
      case P_M1B_THR: if (v >= k1bOff) snprintf(buf, n, "Off"); else snprintf(buf, n, "%+.0f dBu", v); return;
      case P_M1B_RATIO: snprintf(buf, n, "%.1f:1", v); return;
      case P_M16_THR: snprintf(buf, n, "%.2f V", M16Volts(v)); return;
      case P_M16_RATIO: if (v >= 99.5f) snprintf(buf, n, "Inf:1"); else snprintf(buf, n, "%.1f:1", 1.0f / (1.0f - v * 0.01f)); return;
      case P_M22_BASS: case P_M22_MID: sec_text(log_knob(v, 0.6f, 70.0f), buf, n); return;
      case P_M22_XOV: case P_M22_TREB: hz_text(log_knob(v, 100.0f, 10900.0f), buf, n); return;
      case P_M48_RT: sec_text(log_knob(v, 0.3f, 30.0f), buf, n); return;
      case P_M48_BM: snprintf(buf, n, "x%.2f", log_knob(v, 0.25f, 4.0f)); return;
      case P_M48_XOV: hz_text(log_knob(v, 100.0f, 5000.0f), buf, n); return;
      case P_M48_HFC: case P_M48_RTHC: hz_text(log_knob(v, 500.0f, 20000.0f), buf, n); return;
      default: break;
    }
    const char *u = P_UNIT[p];
    if (P_INT[p]) snprintf(buf, n, "%d%s%s", (int)lroundf(v), *u ? " " : "", u);
    else if (!strcmp(u, "dB")) snprintf(buf, n, "%+.1f dB", v);
    else snprintf(buf, n, "%.1f%s%s", v, *u ? " " : "", u);
  }
  void note_touch(int p) {
    char val[48];
    display(p, val, sizeof val);
    last_touch = p;
    snprintf(touch, sizeof touch, "%s  %s", P_NAME[p], val);
    bump();
  }
  const char *status(int m) const { return tripped[m] && active[m] ? "LIMIT: OUT" : (active[m] ? "IN PATH" : "NOT PATCHED"); }
  void tile_text(int t, char *buf, int n) const {
    if (t < N_MOD) { snprintf(buf, n, "%s", status(t)); return; }
    int c = 0;
    for (int a = 0; a < N_AO; a++) for (int b = 0; b < N_AI; b++) c += acc[a][b];
    snprintf(buf, n, "%d CABLE%s  %s", c, c == 1 ? "" : "S", acc[0][N_MOD] ? "DRY ON" : "NO DRY");
  }

  int get_owned(int p, char *buf, int n) {
    auto num = [&](int v) { return snprintf(buf, n, "%d", v); };
    if (p == P_VIEW) return num(view);
    if (p >= F_PG && p < F_PG + N_PG) return num(view == p - F_PG);
    if (p == P_IN_SEC) return num(view != V_OVERVIEW);
    if (p == P_IN_MOD) return num(view >= 1 && view <= N_MOD);
    if (p == P_IN_BAY) return num(view == V_BAY);
    if (p == P_HDR_TI) return num(view != V_OVERVIEW && view != V_BAY);
    if (p >= F_FAO && p < F_FAO + N_FAO) return num(jack_state(true, p - F_FAO));
    if (p >= F_FAI && p < F_FAI + N_FAI) return num(jack_state(false, p - F_FAI));
    if (p >= F_HAO && p < F_HAO + N_HAO) {
      int g = p - F_HAO;
      if (view != V_BAY || pk != 2 || held_out < 0 || held_out / JACK_GROUP != g) return num(0);
      return num(1 + held_out % JACK_GROUP);
    }
    if (p >= F_HAI && p < F_HAI + N_HAI) {
      int g = p - F_HAI;
      if (view != V_BAY || pk != 3 || held_in < 0 || held_in / JACK_GROUP != g) return num(0);
      return num(1 + held_in % JACK_GROUP);
    }
    if (p == P_PK) return num(view == V_BAY ? pk : 0);
    if (p == P_PK_TA) return num(view == V_BAY && pk >= 1 && pk <= 3);
    if (p == P_PK_C) return num(view == V_BAY && (pk == 2 || pk == 3));
    if (p == P_M_IN) return num(view == V_OVERVIEW ? lamp_in : 0);
    if (p == P_M_OUT) return num(view == V_OVERVIEW ? lamp_out : 0);
    if (p == P_M_VU) return num(lamp_vu);
    if (p == P_PATCH_INFO) return snprintf(buf, n, "%s", info);
    if (p == P_TOUCH_INFO) return snprintf(buf, n, "%s", touch[0] ? touch : " ");
    if (p == P_MOD_INFO) {
      if (view < 1 || view > N_MOD) return snprintf(buf, n, " ");
      int m = view - 1;
      if (MOD_IS_COMP[m] && active[m] && !tripped[m]) return snprintf(buf, n, "IN PATH  GR %.1f dB", module_gr(m));
      return snprintf(buf, n, "%s", status(m));
    }
    if (p == P_CPU_INFO) return snprintf(buf, n, "LOAD %d%%  COST %d", (int)lroundf(cpu * 100.0f), cost);
    if (p >= F_TS && p < F_TS + N_TS) { tile_text(p - F_TS, buf, n); return (int)strlen(buf); }
    return -1;
  }

  // ---- state ----------------------------------------------------------------------------------------------------------
  int save(char *buf, int n) const {
    int len = snprintf(buf, n, "xxlpro 1;");
    for (int i = 0; i < N_CONTROLS && len < n - 40; i++)
      if (pv[i] != P_DEF[i]) len += snprintf(buf + len, n - len, "%s=%g;", P_KEY[i], pv[i]);
    for (int i = 0; i < N_AC && len < n - 40; i++)
      if (pv[F_AC + i] != 0) len += snprintf(buf + len, n - len, "%s=1;", P_KEY[F_AC + i]);
    if (len < n - 20) len += snprintf(buf + len, n - len, "view=%d;end=1;", view);
    return len < n ? len : -1;
  }
};

int find_key(const char *k) {
  static int table[4096];
  static bool built = false;
  auto h = [](const char *s) { uint32_t x = 2166136261u; while (*s) x = (x ^ (unsigned char)*s++) * 16777619u; return x; };
  if (!built) {
    for (int i = 0; i < 4096; i++) table[i] = -1;
    for (int i = 0; i < P_COUNT; i++) {
      uint32_t s = h(P_KEY[i]) & 4095;
      while (table[s] >= 0) s = (s + 1) & 4095;
      table[s] = i;
    }
    built = true;
  }
  uint32_t s = h(k) & 4095;
  while (table[s] >= 0) {
    if (!strcmp(P_KEY[table[s]], k)) return table[s];
    s = (s + 1) & 4095;
  }
  return -1;
}

void set_control(Plug *s, int p, float v) {
  v = clampf(v, P_MIN[p], P_MAX[p]);
  if (P_NOPTS[p] || P_INT[p]) v = roundf(v);
  if (s->pv[p] != v) { s->pv[p] = v; s->dirty = true; }
}

void load_state(Plug *s, const char *st) {
  if (strncmp(st, "xxlpro", 6)) return;
  for (int i = 0; i < N_CONTROLS; i++) s->pv[i] = P_DEF[i];
  for (int i = 0; i < N_AC; i++) s->pv[F_AC + i] = 0;
  const char *q = strchr(st, ';');
  int view = 0;
  while (q && *++q) {
    const char *e = strchr(q, ';');
    if (!e) break;
    char item[64];
    int len = (int)(e - q) < 63 ? (int)(e - q) : 63;
    memcpy(item, q, len);
    item[len] = 0;
    char *eq = strchr(item, '=');
    if (eq) {
      *eq = 0;
      if (!strcmp(item, "view")) view = (int)clampf((float)atoi(eq + 1), 0, N_VIEWS - 1);
      else {
        int p = find_key(item);
        if (p >= 0 && p < N_CONTROLS) set_control(s, p, (float)atof(eq + 1));
        else if (p >= F_AC && p < F_AC + N_AC) s->pv[p] = atof(eq + 1) > 0.5 ? 1.0f : 0.0f;
      }
    }
    q = e;
  }
  s->held_out = s->held_in = -1;
  s->dirty = true;
  s->clear_trips();
  s->rebuild();
  s->view = -1;
  s->set_view(view);
  s->bump();
}

void *create(const char *) {
  void *mem = calloc(1, sizeof(Plug));
  if (!mem) return nullptr;
  Plug *s = new (mem) Plug();
  s->init();
  return s;
}
void destroy(void *inst) {
  Plug *s = (Plug *)inst;
  s->~Plug();
  free(s);
}
void midi(void *, const uint8_t *, int) {}

static bool in_family(int p, int first, int n) { return p >= first && p < first + n; }

void set_param(void *inst, const char *key, const char *val) {
  Plug *s = (Plug *)inst;
  float v = (float)atof(val);
  if (!strcmp(key, "state")) { load_state(s, val); return; }
  if (!strcmp(key, "guard")) { s->guard_on = v > 0.5f; s->over_blocks = 0; return; }       // test hooks (not VST parameters)
  if (!strcmp(key, "guard_trip")) { if (v > 0.5f) s->trip_latest(); return; }
  int p = find_key(key);
  if (p < 0) return;
  if (p < N_CONTROLS) {
    float before = s->pv[p];
    set_control(s, p, v);
    if (s->pv[p] != before) s->note_touch(p);
    s->bump();
    return;
  }
  if (p == P_VIEW) { s->set_view((int)lroundf(v)); return; }
  if (in_family(p, F_AC, N_AC)) {
    float nv = v > 0.5f ? 1.0f : 0.0f;
    if (s->pv[p] != nv) { s->pv[p] = nv; s->clear_trips(); s->rebuild(); s->bump(); }
    return;
  }
  if (p >= P_QL1 && p <= P_QL16) {
    int t = VIEW_QLINKS[s->view][p - P_QL1];
    if (t < 0) return;
    float x = clampf(v, 0, 1), before = s->pv[t];
    set_control(s, t, P_MIN[t] + x * (P_MAX[t] - P_MIN[t]));
    if (s->pv[t] != before) s->note_touch(t);
    s->bump();
    return;
  }
  if (v < 0.5f) return;   // everything else engine-owned is read-only, or a trigger firing on 1
  if (p == P_NAV_ZOOM) { s->set_view(V_OVERVIEW); return; }
  if (p == P_NAV_PREV || p == P_NAV_NEXT) {
    if (s->nav_cool > 0) return;
    s->nav_cool = 6;
    int v2 = s->view <= 0 ? (p == P_NAV_NEXT ? 1 : N_VIEWS - 1) : s->view + (p == P_NAV_NEXT ? 1 : -1);
    if (v2 < 1) v2 = N_VIEWS - 1;
    if (v2 >= N_VIEWS) v2 = 1;
    s->set_view(v2);
    return;
  }
  if (in_family(p, F_GO, N_GO)) { s->set_view(1 + p - F_GO); return; }
  if (p == P_FM_BAY) { s->set_view(V_BAY); return; }
  if (p == P_BAY_CLEAR) { s->clear_audio(); s->cancel_pick(); snprintf(s->info, sizeof s->info, "All cables removed: the plugin is silent until you patch."); s->bump(); return; }
  if (in_family(p, F_TAO, N_TAO)) { s->pick_aud(true, p - F_TAO); return; }
  if (in_family(p, F_TAI, N_TAI)) { s->pick_aud(false, p - F_TAI); return; }
  if (p == P_PK_CANCEL || p == P_PK_DONE) { s->cancel_pick(); return; }
  if (p == P_PK_UNPLUG) { s->unplug_pair(); return; }
}

int get_param(void *inst, const char *key, char *buf, int n) {
  Plug *s = (Plug *)inst;
  if (!strcmp(key, "display_rev")) return snprintf(buf, n, "%u", s->rev);
  if (!strcmp(key, "state")) return s->save(buf, n);
  if (!strcmp(key, "cost")) return snprintf(buf, n, "%d", s->cost);
  size_t kl = strlen(key);
  char base[64];
  int suffix = 0;   // 1 = _display, 2 = _name
  if (kl > 8 && !strcmp(key + kl - 8, "_display")) { suffix = 1; kl -= 8; }
  else if (kl > 5 && !strcmp(key + kl - 5, "_name")) { suffix = 2; kl -= 5; }
  if (kl >= sizeof base) return 0;
  memcpy(base, key, kl);
  base[kl] = 0;
  int p = find_key(base);
  if (p < 0) {
    if (!suffix && !strncmp(key, "active_", 7)) { int m = atoi(key + 7); return snprintf(buf, n, "%d", m >= 0 && m < N_MOD && s->active[m] && !s->tripped[m]); }
    if (!suffix && !strncmp(key, "gr_", 3)) { int m = atoi(key + 3); return snprintf(buf, n, "%g", m >= 0 && m < N_MOD ? s->module_gr(m) : 0.0f); }
    return 0;
  }
  if (p >= P_QL1 && p <= P_QL16) {
    int t = VIEW_QLINKS[s->view][p - P_QL1];
    if (suffix == 2) return snprintf(buf, n, "%s", t >= 0 ? P_NAME[t] : "-");
    if (suffix == 1) { if (t < 0) return snprintf(buf, n, " "); s->display(t, buf, n); return (int)strlen(buf); }
    if (t < 0) return snprintf(buf, n, "0");
    float span = P_MAX[t] - P_MIN[t];
    return snprintf(buf, n, "%g", span > 0 ? (s->pv[t] - P_MIN[t]) / span : 0.0f);
  }
  if (suffix == 2) return 0;
  if (suffix == 1) {
    if (p >= N_CONTROLS) return 0;
    s->display(p, buf, n);
    return (int)strlen(buf);
  }
  if (p < N_CONTROLS) {
    if (P_NOPTS[p]) return snprintf(buf, n, "%d", (int)s->pv[p]);
    return snprintf(buf, n, "%g", s->pv[p]);
  }
  if (in_family(p, F_AC, N_AC)) return snprintf(buf, n, "%g", s->pv[p]);
  int r = s->get_owned(p, buf, n);
  if (r >= 0) return r;
  return snprintf(buf, n, "0");   // triggers and navigation read back as 0
}

void process_fn(void *inst, const int16_t *in, int16_t *out, int frames) { ((Plug *)inst)->process(in, out, frames); }
void render_fn(void *inst, int16_t *out, int frames) { memset(out, 0, (size_t)frames * 4); (void)inst; }

const mpc_engine_t API = {create, destroy, midi, set_param, get_param, render_fn, process_fn};

}  // namespace

extern "C" const mpc_engine_t *mpc_engine(void) { return &API; }
