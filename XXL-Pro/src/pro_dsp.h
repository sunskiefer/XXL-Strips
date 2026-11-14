// SPDX-License-Identifier: GPL-3.0-or-later
// XXL Pro -- our own DSP for the fifteen process modules (L'Cronx). Host-free: plain numbers in, plain numbers out.
// Every module was written from measured behaviour targets (docs/measured/*.md): static curves, timing, frequency
// responses, harmonics. The numbers that shape the sound sit in the tables at the top of each module so they can be
// re-tuned in one place. The two reverbs are our own designs tuned to outside behaviour, not rebuilds.
// 44.1 kHz, stereo, in place, any block length. Nothing here allocates.
#pragma once
#include <cmath>
#include <cstdint>
#include <cstring>

namespace xxl {

static const float kSR = 44100.0f;
static const float kPi = 3.14159265358979f;

inline float DbToLin(float db) { return std::exp(db * 0.115129255f); }
inline float LinToDb(float x) { return 8.68588964f * std::log(x > 1e-9f ? x : 1e-9f); }
inline float Clampf(float x, float lo, float hi) { return x < lo ? lo : (x > hi ? hi : x); }
inline float PoleCoef(float seconds) { return 1.0f - std::exp(-1.0f / (seconds * kSR)); }
inline float Lerp(float a, float b, float t) { return a + (b - a) * t; }
// y at x on a table of points (xs rising); flat outside
inline float TableAt(const float* xs, const float* ys, int n, float x) {
  if (x <= xs[0]) return ys[0];
  for (int i = 1; i < n; ++i)
    if (x <= xs[i]) return Lerp(ys[i - 1], ys[i], (x - xs[i - 1]) / (xs[i] - xs[i - 1]));
  return ys[n - 1];
}

// ---------------------------------------------------------------------------------------------------- biquad
struct Biquad {
  float b0 = 1, b1 = 0, b2 = 0, a1 = 0, a2 = 0;
  float z1[2] = {0, 0}, z2[2] = {0, 0};
  inline float Tick(float x, int c) {
    float y = b0 * x + z1[c];
    z1[c] = b1 * x - a1 * y + z2[c];
    z2[c] = b2 * x - a2 * y;
    return y;
  }
  void Reset() { z1[0] = z1[1] = z2[0] = z2[1] = 0; }
  void Identity() { b0 = 1; b1 = b2 = a1 = a2 = 0; }
  void Set(float B0, float B1, float B2, float A0, float A1, float A2) {
    float inv = 1.0f / A0;
    b0 = B0 * inv; b1 = B1 * inv; b2 = B2 * inv; a1 = A1 * inv; a2 = A2 * inv;
  }
  static float W0(float f) { return 2.0f * kPi * Clampf(f, 5.0f, 0.45f * kSR) / kSR; }
  void Peak(float f, float gain_db, float q) {
    if (std::fabs(gain_db) < 0.01f) { Identity(); return; }
    float a = std::exp(gain_db * 0.0575646273f), w = W0(f), cs = std::cos(w), al = std::sin(w) / (2.0f * q);
    Set(1 + al * a, -2 * cs, 1 - al * a, 1 + al / a, -2 * cs, 1 - al / a);
  }
  void LowShelf(float f, float gain_db, float slope) {
    if (std::fabs(gain_db) < 0.01f) { Identity(); return; }
    float a = std::exp(gain_db * 0.0575646273f), w = W0(f), cs = std::cos(w), sn = std::sin(w);
    float al = sn * 0.5f * std::sqrt((a + 1.0f / a) * (1.0f / slope - 1.0f) + 2.0f), sq = 2.0f * std::sqrt(a) * al;
    Set(a * ((a + 1) - (a - 1) * cs + sq), 2 * a * ((a - 1) - (a + 1) * cs), a * ((a + 1) - (a - 1) * cs - sq),
        (a + 1) + (a - 1) * cs + sq, -2 * ((a - 1) + (a + 1) * cs), (a + 1) + (a - 1) * cs - sq);
  }
  void HighShelf(float f, float gain_db, float slope) {
    if (std::fabs(gain_db) < 0.01f) { Identity(); return; }
    float a = std::exp(gain_db * 0.0575646273f), w = W0(f), cs = std::cos(w), sn = std::sin(w);
    float al = sn * 0.5f * std::sqrt((a + 1.0f / a) * (1.0f / slope - 1.0f) + 2.0f), sq = 2.0f * std::sqrt(a) * al;
    Set(a * ((a + 1) + (a - 1) * cs + sq), -2 * a * ((a - 1) + (a + 1) * cs), a * ((a + 1) + (a - 1) * cs - sq),
        (a + 1) - (a - 1) * cs + sq, 2 * ((a - 1) - (a + 1) * cs), (a + 1) - (a - 1) * cs - sq);
  }
  void HighPass2(float f, float q) {
    float w = W0(f), cs = std::cos(w), al = std::sin(w) / (2.0f * q);
    Set((1 + cs) * 0.5f, -(1 + cs), (1 + cs) * 0.5f, 1 + al, -2 * cs, 1 - al);
  }
  void LowPass2(float f, float q) {
    float w = W0(f), cs = std::cos(w), al = std::sin(w) / (2.0f * q);
    Set((1 - cs) * 0.5f, 1 - cs, (1 - cs) * 0.5f, 1 + al, -2 * cs, 1 - al);
  }
  void HighPass1(float f) {
    float k = std::tan(W0(f) * 0.5f), n = 1.0f / (1.0f + k);
    b0 = n; b1 = -n; b2 = 0; a1 = (k - 1.0f) * n; a2 = 0;
  }
};

// a gain that glides to its target (no zipper noise)
struct Glide {
  float cur = 1.0f, target = 1.0f; bool init = false;
  void Set(float t) { target = t; if (!init) { cur = t; init = true; } }
  inline float Tick() { cur += 0.002f * (target - cur); return cur; }
};

// one-pole DC blocker (5 Hz)
struct DcBlock {
  float x1[2] = {0, 0}, y1[2] = {0, 0};
  inline float Tick(float x, int c) { float y = x - x1[c] + 0.9993f * y1[c]; x1[c] = x; y1[c] = y; return y; }
  void Reset() { x1[0] = x1[1] = y1[0] = y1[1] = 0; }
};

// small harmonics: y = x + a x^2 + b x^3 (a: 2nd, b: 3rd)
inline float Harm(float x, float a, float b) { return x + x * x * (a + b * x); }

// ============================================================================================ compressor core
// Detector (mean square, so a level in dBFS RMS) -> static law -> gain envelope. Stereo: linked (the louder side
// drives both) or dual.
struct CompLaw {
  float cross = 0, slope = 0, knee = 1;        // soft-knee law: reduction = slope * (level - cross) above the knee
  const float* table = nullptr;                // or a table: reduction at kTabLv[] levels (XXL-67)
  float bend_at = 1e9f, bend = 1.0f;           // above bend_at dB of reduction the law flattens by this factor
};
static const float kTabLv[7] = {-40, -30, -24, -18, -12, -6, 0};

inline float LawReduction(const CompLaw& l, float level_db) {
  if (l.table) {
    if (level_db >= 0.0f) return l.table[6] + (l.table[6] - l.table[5]) * level_db / 6.0f;
    if (level_db <= -40.0f) { float t = (level_db + 52.0f) / 12.0f; return t > 0 ? l.table[0] * t : 0.0f; }
    return TableAt(kTabLv, l.table, 7, level_db);
  }
  float over = level_db - l.cross, half = l.knee * 0.5f, red;
  if (over <= -half) return 0.0f;
  if (over >= half) red = l.slope * over;
  else { float t = over + half; red = l.slope * t * t / (2.0f * l.knee); }
  return red > l.bend_at ? l.bend_at + (red - l.bend_at) * l.bend : red;
}

enum { kEnvTwoStage, kEnvLinearRelease, kEnvFastOrSlow };
struct CompEnv {
  int mode = kEnvTwoStage;
  float share = 1.0f;                     // two-stage: stage 1's share of the reduction; fast-or-slow: the slow share
  float a1 = 0.01f, r1 = 0.001f, a2 = 0.01f, r2 = 0.001f;   // pole coefficients
  float lin_rate = 0;                     // linear release, dB per sample
};

class CompCore {
 public:
  CompLaw law; CompEnv env; bool linked = true; float det_c = PoleCoef(0.002f);
  void Reset() { for (int c = 0; c < 2; ++c) { ms_[c] = e1_[c] = e2_[c] = gr_[c] = 0; } }
  // kl, kr: detector inputs. Leaves the reduction (dB >= 0) of each side in gr(0), gr(1).
  inline void Tick(float kl, float kr) {
    ms_[0] += det_c * (kl * kl - ms_[0]);
    ms_[1] += det_c * (kr * kr - ms_[1]);
    if (linked) {
      float m = ms_[0] > ms_[1] ? ms_[0] : ms_[1];
      gr_[0] = gr_[1] = Envelope(LawReduction(law, 4.34294482f * std::log(m + 1e-12f)), 0);
    } else {
      for (int c = 0; c < 2; ++c) gr_[c] = Envelope(LawReduction(law, 4.34294482f * std::log(ms_[c] + 1e-12f)), c);
    }
  }
  float gr(int c) const { return gr_[c]; }
  float max_gr() const { return gr_[0] > gr_[1] ? gr_[0] : gr_[1]; }

 private:
  inline float Envelope(float target, int c) {
    if (env.mode == kEnvTwoStage) {
      float t1 = target * env.share, t2 = target - t1;
      e1_[c] += (t1 > e1_[c] ? env.a1 : env.r1) * (t1 - e1_[c]);
      e2_[c] += (t2 > e2_[c] ? env.a2 : env.r2) * (t2 - e2_[c]);
      return e1_[c] + e2_[c];
    }
    if (env.mode == kEnvLinearRelease) {
      float e = e1_[c];
      if (target > e) e += ((target - e) > 0.4f * target ? env.a1 : env.a2) * (target - e);
      else { e -= env.lin_rate; if (e < target) e = target; }
      return e1_[c] = e;
    }
    e1_[c] += (target > e1_[c] ? env.a1 : env.r1) * (target - e1_[c]);
    float st = e1_[c] * env.share;
    e2_[c] += (st > e2_[c] ? env.a2 : env.r2) * (st - e2_[c]);
    return e1_[c] > e2_[c] ? e1_[c] : e2_[c];
  }
  float ms_[2] = {0, 0}, e1_[2] = {0, 0}, e2_[2] = {0, 0}, gr_[2] = {0, 0};
};

// ============================================================================================ XXL-2A
// Targets: docs/measured/XXL-2A-measured-targets.md
static const float k2aCross0 = 5.8f, k2aCrossPerStep = -0.525f;   // where the straight part starts, dBFS RMS
static const float k2aSlopeComp = 0.80f, k2aSlopeLimit = 0.90f, k2aKnee = 6.0f;
static const float k2aBendAt = 24.0f, k2aBend = 0.75f;              // deep reduction flattens
static const float k2aGainPerStep = 0.48f;                          // dB per knob step around 40 (unity)
static const float k2aEmphDb = 11.0f, k2aEmphHz = 3000.0f;          // side-chain emphasis at maximum
class M2A {
 public:
  void Reset() { core.Reset(); sc_.Reset(); }
  void Set(float peak, float gain, bool limit, float emph, bool linked) {
    core.law.cross = k2aCross0 + k2aCrossPerStep * peak;
    core.law.slope = limit ? k2aSlopeLimit : k2aSlopeComp;
    core.law.knee = k2aKnee; core.law.bend_at = k2aBendAt; core.law.bend = k2aBend;
    core.linked = linked;
    core.env.mode = kEnvTwoStage; core.env.share = 0.6f;
    core.env.a1 = PoleCoef(0.005f); core.env.r1 = PoleCoef(0.050f);
    core.env.a2 = PoleCoef(0.030f); core.env.r2 = PoleCoef(0.380f);
    out_.Set(gain <= 0.5f ? 0.0f : DbToLin((gain - 40.0f) * k2aGainPerStep));
    e_ = emph * 0.01f;
    sc_.HighShelf(k2aEmphHz, k2aEmphDb * e_, 0.5f);
    sc_gain_ = DbToLin(-k2aEmphDb * e_);
  }
  void Process(float* l, float* r, int n) {
    for (int i = 0; i < n; ++i) {
      float kl = l[i], kr = r[i];
      if (e_ > 0.001f) { kl = sc_.Tick(kl, 0) * sc_gain_; kr = sc_.Tick(kr, 1) * sc_gain_; }
      core.Tick(kl, kr);
      float o = out_.Tick();
      l[i] *= DbToLin(-core.gr(0)) * o;
      r[i] *= DbToLin(-core.gr(1)) * o;
    }
  }
  CompCore core;
 private:
  Biquad sc_; float sc_gain_ = 1, e_ = 0; Glide out_;
};

// ============================================================================================ XXL-1B
static const float k1bCrossAt22 = -33.5f, k1bCrossPerDb = 1.29f, k1bKnee = 36.0f, k1bOff = 19.5f;   // the law's start against the threshold knob
static const float k1bX[3] = {0.5f, 0.75f, 0.9f}, k1bSlope[3] = {0.567f, 0.73f, 0.93f};
class M1B {
 public:
  void Reset() { core.Reset(); }
  void Set(float thr_dbu, float gain_db, float ratio, int timing, float att, float rel, bool linked) {
    off_ = thr_dbu >= k1bOff;
    core.law.cross = k1bCrossAt22 + k1bCrossPerDb * (thr_dbu + 22.0f);
    core.law.slope = off_ ? 0.0f : TableAt(k1bX, k1bSlope, 3, 1.0f - 1.0f / ratio);
    core.law.knee = k1bKnee;
    core.linked = linked;
    core.env.mode = kEnvTwoStage;
    float man_a = 0.001f * std::pow(45.0f, att * 0.1f), man_r = 0.018f * std::pow(361.0f, rel * 0.1f);
    if (timing == 0) {          // FIXED
      core.env.share = 0.75f;
      core.env.a1 = PoleCoef(0.0022f); core.env.r1 = PoleCoef(0.003f);
      core.env.a2 = PoleCoef(0.025f); core.env.r2 = PoleCoef(0.008f);
    } else {                    // MANUAL, or FIX-MAN: fixed attack with the manual release
      core.env.share = 1.0f;
      core.env.a1 = core.env.a2 = PoleCoef(timing == 1 ? man_a : 0.0013f);
      core.env.r1 = core.env.r2 = PoleCoef(man_r);
    }
    out_.Set(DbToLin(gain_db));
  }
  void Process(float* l, float* r, int n) {
    for (int i = 0; i < n; ++i) {
      core.Tick(l[i], r[i]);
      float o = out_.Tick();
      l[i] *= DbToLin(-core.gr(0)) * o;
      r[i] *= DbToLin(-core.gr(1)) * o;
    }
  }
  CompCore core;
 private:
  bool off_ = false; Glide out_;
};

// ============================================================================================ XXL-16VU
static const float k16RefDb = -27.4f, k16RefV = 0.173f, k16Scale = 1.1f;   // threshold volts -> dBFS RMS
static const float k16ReleaseDbPerS = 125.0f;
inline float M16Volts(float knob) { return 0.01f * std::pow(300.0f, knob * 0.01f); }
class M16 {
 public:
  void Reset() { core.Reset(); }
  void Set(float thr_knob, float ratio_knob, float out_db, bool linked) {
    core.law.cross = k16RefDb + k16Scale * 20.0f * std::log10(M16Volts(thr_knob) / k16RefV);
    core.law.slope = Clampf(ratio_knob * 0.01f, 0.0f, 1.0f);
    core.law.knee = 1.0f;                                   // hard knee
    core.linked = linked;
    core.env.mode = kEnvLinearRelease;
    core.env.a1 = PoleCoef(0.0015f); core.env.a2 = PoleCoef(0.025f);
    core.env.lin_rate = k16ReleaseDbPerS / kSR;
    out_.Set(DbToLin(out_db));
  }
  void Process(float* l, float* r, int n) {
    for (int i = 0; i < n; ++i) {
      core.Tick(l[i], r[i]);
      float o = out_.Tick();
      l[i] *= DbToLin(-core.gr(0)) * o;
      r[i] *= DbToLin(-core.gr(1)) * o;
    }
  }
  CompCore core;
 private:
  Glide out_;
};

// ============================================================================================ XXL-76
// The input knob drives the level into a fixed threshold. Ratio index 0 = amplifier only, 1..4 = 4 / 8 / 12 / 20, 5 = all.
static const float k76Thr[6] = {0, -3.3f, -1.6f, 0.1f, 1.7f, 2.6f};       // dBFS RMS of the driven signal
static const float k76Ratio[6] = {1, 5.7f, 10.0f, 18.0f, 40.0f, 16.0f};    // measured: steeper than the label
static const float k76Knee = 4.0f;
static const float k76RelFast[7] = {1.1f, 0.8f, 0.55f, 0.3f, 0.15f, 0.06f, 0.02f};   // release knob 1..7, seconds
static const float k76H2 = 0.016f, k76H3 = 0.015f;                         // harmonics while limiting
class M76 {
 public:
  void Reset() { core.Reset(); dc_.Reset(); }
  void Set(float in_knob, float out_knob, int attack, int release, int ratio, bool rev_b, bool linked) {
    in_.Set(in_knob <= 0.5f ? 0.0f : DbToLin(0.48f * in_knob - 12.0f));
    out_.Set(DbToLin(0.48f * out_knob - 24.0f + (rev_b ? 1.0f : 0.0f)));
    core.law.cross = k76Thr[ratio];
    core.law.slope = 1.0f - 1.0f / k76Ratio[ratio];
    core.law.knee = k76Knee;
    core.linked = linked;
    core.det_c = PoleCoef(0.0004f);
    float a = 0.0022f - (attack - 1) * 0.0002f, rf = k76RelFast[release - 1], rs = rf * 3.0f < 0.3f ? 0.3f : rf * 3.0f;
    core.env.mode = kEnvTwoStage; core.env.share = 0.8f;
    core.env.a1 = core.env.a2 = PoleCoef(a);
    core.env.r1 = PoleCoef(rf); core.env.r2 = PoleCoef(rs);
  }
  void Process(float* l, float* r, int n) {
    for (int i = 0; i < n; ++i) {
      float g = in_.Tick(), o = out_.Tick();
      float x[2] = {l[i] * g, r[i] * g};
      core.Tick(x[0], x[1]);
      for (int c = 0; c < 2; ++c) {
        float gr = core.gr(c), d = gr > 10.0f ? 1.0f : gr * 0.1f;
        float y = x[c] * DbToLin(-gr);
        y = dc_.Tick(Harm(y, k76H2 * d, k76H3 * d), c);
        (c ? r : l)[i] = y * o;
      }
    }
  }
  CompCore core;
 private:
  Glide in_, out_; DcBlock dc_;
};

// ============================================================================================ XXL-67
// No fixed ratio: reduction against level for five threshold settings (0, 0.25, 0.5, 0.75, 1).
static const float k67Tab[5][7] = {
    {0, 0, 0, 0, 0, 0, 0},
    {0, 0, 0.2f, 0.6f, 1.4f, 2.8f, 4.9f},
    {0, 0.4f, 0.9f, 1.9f, 3.8f, 6.4f, 9.1f},
    {0.1f, 0.7f, 1.5f, 3.0f, 5.5f, 8.3f, 11.2f},
    {0.2f, 0.9f, 1.9f, 3.7f, 6.5f, 9.1f, 12.6f}};
static const float k67Rel[6] = {0.1f, 0.3f, 0.9f, 1.8f, 0.3f, 0.15f};      // time constant 1..6 (5, 6: the fast part)
static const float k67SlowShare[2] = {0.72f, 0.62f}, k67SlowRel[2] = {2.6f, 6.5f}, k67SlowCharge = 0.5f;
class M67 {
 public:
  void Reset() { core.Reset(); }
  void Set(float in_db, float thr, int tc, float out_db, bool lat_vert, bool linked) {
    float t = Clampf(thr * 0.01f, 0.0f, 1.0f) * 4.0f;
    int i = t >= 4.0f ? 3 : static_cast<int>(t);
    for (int k = 0; k < 7; ++k) tab_[k] = Lerp(k67Tab[i][k], k67Tab[i + 1][k], t - i);
    core.law.table = tab_;
    core.linked = linked;
    core.det_c = PoleCoef(0.001f);
    core.env.a1 = PoleCoef(0.0008f);
    core.env.r1 = PoleCoef(k67Rel[tc - 1]);
    if (tc >= 5) {
      core.env.mode = kEnvFastOrSlow; core.env.share = k67SlowShare[tc - 5];
      core.env.a2 = PoleCoef(k67SlowCharge); core.env.r2 = PoleCoef(k67SlowRel[tc - 5]);
    } else {
      core.env.mode = kEnvTwoStage; core.env.share = 1.0f; core.env.a2 = core.env.a1; core.env.r2 = core.env.r1;
    }
    in_.Set(DbToLin(in_db)); out_.Set(DbToLin(out_db)); ms_ = lat_vert;
  }
  void Process(float* l, float* r, int n) {
    for (int i = 0; i < n; ++i) {
      float g = in_.Tick(), o = out_.Tick();
      float a = l[i] * g, b = r[i] * g;
      if (ms_) { float m = (a + b) * 0.5f, s = (a - b) * 0.5f; a = m; b = s; }
      core.Tick(a, b);
      a *= DbToLin(-core.gr(0)); b *= DbToLin(-core.gr(1));
      if (ms_) { float L = a + b, R = a - b; a = L; b = R; }
      l[i] = a * o; r[i] = b * o;
    }
  }
  CompCore core;
 private:
  float tab_[7] = {0}; bool ms_ = false; Glide in_, out_;
};

// ============================================================================================ XXL-DISS
// Ratio index 0..7 = 1:1, 2, 3, 4, 6, 10, 20, MAX. Like XXL-76 the input knob drives into a fixed threshold.
static const float kDsSlope[8] = {0, 0.77f, 0.82f, 0.85f, 0.88f, 0.90f, 0.92f, 0.94f};
static const float kDsCross[8] = {0, -12.2f, -13.5f, -14.2f, -14.8f, -15.4f, -15.6f, -15.8f};
static const float kDsKnee = 10.0f;
static const float kDsH2[4] = {0.0022f, 0.0022f, 0.004f, 0.007f}, kDsH3[4] = {0.012f, 0.012f, 0.028f, 0.11f};
class MDiss {
 public:
  void Reset() { core.Reset(); sc_.Reset(); hp_.Reset(); dc_.Reset(); }
  void Set(float in_knob, float attack, float release, float out_knob, int ratio, int det, int audio, bool linked) {
    in_.Set(DbToLin(3.0f * (in_knob - 5.0f))); out_.Set(DbToLin(3.0f * (out_knob - 5.0f)));
    core.law.cross = kDsCross[ratio]; core.law.slope = kDsSlope[ratio]; core.law.knee = kDsKnee;
    core.linked = linked;
    core.det_c = PoleCoef(0.0005f);
    float ka = attack / 10.5f, kr = release / 10.5f;
    core.env.mode = kEnvTwoStage;
    core.env.share = 0.45f - 0.30f * kr;
    core.env.a1 = core.env.a2 = PoleCoef(0.0002f * std::pow(60.0f, ka));
    core.env.r1 = PoleCoef(0.02f * std::pow(10.0f, kr));
    core.env.r2 = PoleCoef(0.6f * std::pow(16.7f, kr));
    det_ = det; audio_ = audio;
    if (det == 1) sc_.HighPass2(150.0f, 0.7071f); else if (det == 2) sc_.HighShelf(4000.0f, 6.0f, 0.7f); else sc_.Identity();
    if (audio == 1) hp_.HighPass1(80.0f); else hp_.Identity();
  }
  void Process(float* l, float* r, int n) {
    const float h2 = kDsH2[audio_], h3 = kDsH3[audio_];
    for (int i = 0; i < n; ++i) {
      float g = in_.Tick(), o = out_.Tick();
      float x[2] = {l[i] * g, r[i] * g};
      core.Tick(det_ ? sc_.Tick(x[0], 0) : x[0], det_ ? sc_.Tick(x[1], 1) : x[1]);
      for (int c = 0; c < 2; ++c) {
        float y = x[c] * DbToLin(-core.gr(c));
        y = dc_.Tick(Harm(y, h2, h3), c);
        if (audio_ == 1) y = hp_.Tick(y, c);
        (c ? r : l)[i] = y * o;
      }
    }
  }
  CompCore core;
 private:
  Biquad sc_, hp_; DcBlock dc_; Glide in_, out_; int det_ = 0, audio_ = 0;
};

// ============================================================================================ XXL-73
// Fitted to the measured responses (rms error under 0.7 dB): shelf corner, slope and peak Q per position.
static const float k73Hpf[5] = {0, 44.0f, 70.0f, 141.0f, 264.0f};                 // 18 dB per octave
static const float k73LowHz[5] = {0, 110.0f, 173.0f, 267.0f, 416.0f};
static const float k73MidHz[7] = {0, 346.0f, 704.0f, 1465.0f, 3482.0f, 5382.0f, 7468.0f};
static const float k73MidQ[7] = {1, 0.30f, 0.32f, 0.50f, 0.23f, 0.37f, 0.45f};
static const float k73HighBoostHz = 3236.0f, k73HighCutHz = 2180.0f;
static const float k73H2 = 0.0052f, k73H3 = 0.0035f;
class M73 {
 public:
  void Reset() { for (auto& b : bq_) b.Reset(); dc_.Reset(); }
  void Set(float gain_db, float out_db, int hpf, int lf, float lg, int mf, float mg, float hg, bool eq_in, bool phase) {
    in_.Set(DbToLin(gain_db)); out_.Set(DbToLin(out_db) * (phase ? -1.0f : 1.0f));
    if (hpf) { bq_[0].HighPass1(k73Hpf[hpf]); bq_[1].HighPass2(k73Hpf[hpf], 1.0f); } else { bq_[0].Identity(); bq_[1].Identity(); }
    if (eq_in && lf) bq_[2].LowShelf(k73LowHz[lf], lg, 0.9f); else bq_[2].Identity();
    if (eq_in && mf) bq_[3].Peak(k73MidHz[mf], mg * 1.05f, k73MidQ[mf]); else bq_[3].Identity();
    if (eq_in) bq_[4].HighShelf(hg >= 0 ? k73HighBoostHz : k73HighCutHz, hg, hg >= 0 ? 0.75f : 0.95f); else bq_[4].Identity();
  }
  void Process(float* l, float* r, int n) {
    for (int i = 0; i < n; ++i) {
      float g = in_.Tick(), o = out_.Tick();
      for (int c = 0; c < 2; ++c) {
        float x = (c ? r : l)[i] * g;
        x = Harm(x, k73H2, -k73H3);
        x = x / std::sqrt(std::sqrt(1.0f + (x * 0.125f) * (x * 0.125f) * (x * 0.125f) * (x * 0.125f)));   // clips softly near +18 dBFS
        x = dc_.Tick(x, c);
        for (int k = 0; k < 5; ++k) x = bq_[k].Tick(x, c);
        (c ? r : l)[i] = x * o;
      }
    }
  }
 private:
  Biquad bq_[5]; DcBlock dc_; Glide in_, out_;
};

// ============================================================================================ XXL-55A
static const float k55LowHz[5] = {50, 100, 200, 300, 400}, k55MidHz[5] = {400, 800, 1500, 3000, 5000};
static const float k55HighHz[5] = {5000, 7000, 10000, 12500, 15000};
static const float k55Gain[11] = {-12, -9, -6, -4, -2, 0, 2, 4, 6, 9, 12};
static const float k55HighBellQ[5] = {0.49f, 0.45f, 0.42f, 0.38f, 0.34f};
class M55 {
 public:
  void Reset() { for (auto& b : bq_) b.Reset(); }
  void Set(int lf, int lg, bool lbell, int mf, int mg, int hf, int hg, bool hbell, bool filter, bool eq_in, bool phase,
           float out_db) {
    for (auto& b : bq_) b.Identity();
    if (eq_in) {
      if (lbell) bq_[0].Peak(k55LowHz[lf], k55Gain[lg], 0.62f); else bq_[0].LowShelf(k55LowHz[lf] * 3.5f, k55Gain[lg] * 1.1f, 0.5f);
      bq_[1].Peak(k55MidHz[mf], k55Gain[mg], 0.58f);
      if (hbell) bq_[2].Peak(k55HighHz[hf], k55Gain[hg], k55HighBellQ[hf]); else bq_[2].HighShelf(k55HighHz[hf] * 0.3f, k55Gain[hg], 0.5f);
    }
    if (filter) { bq_[3].HighPass2(42.0f, 0.6f); bq_[4].LowPass2(19000.0f, 0.55f); }
    out_.Set(DbToLin(out_db) * (phase ? -1.0f : 1.0f));
  }
  void Process(float* l, float* r, int n) {
    for (int i = 0; i < n; ++i) {
      float o = out_.Tick();
      for (int c = 0; c < 2; ++c) {
        float x = (c ? r : l)[i];
        for (int k = 0; k < 5; ++k) x = bq_[k].Tick(x, c);
        (c ? r : l)[i] = x * o;
      }
    }
  }
 private:
  Biquad bq_[5]; Glide out_;
};

// ============================================================================================ XXL-56
static const float k56Hz[10] = {31, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000};
static const float k56Q = 0.65f, k56GainScale = 1.04f, k56Range6 = 0.41f;
class M56 {
 public:
  void Reset() { for (auto& b : bq_) b.Reset(); }
  void Set(const float* gains, bool eq_in, bool range6, float out_db) {
    for (int k = 0; k < 10; ++k) {
      if (eq_in) bq_[k].Peak(k56Hz[k], gains[k] * k56GainScale * (range6 ? k56Range6 : 1.0f), k56Q); else bq_[k].Identity();
    }
    out_.Set(DbToLin(out_db));
  }
  void Process(float* l, float* r, int n) {
    for (int i = 0; i < n; ++i) {
      float o = out_.Tick();
      for (int c = 0; c < 2; ++c) {
        float x = (c ? r : l)[i];
        for (int k = 0; k < 10; ++k) x = bq_[k].Tick(x, c);
        (c ? r : l)[i] = x * o;
      }
    }
  }
 private:
  Biquad bq_[10]; Glide out_;
};

// ============================================================================================ XXL-EQ1-A
// Low boost and low attenuation are two different shelves (the attenuation reaches further up), so both can be
// used together. High boost is a bell with a bandwidth control that takes a little off everything; high
// attenuation is a shelf.
static const float kQ1LowHz[4] = {20, 30, 60, 100}, kQ1HighHz[7] = {3000, 4000, 5000, 8000, 10000, 12000, 16000};
static const float kQ1AttenHz[3] = {5000, 10000, 20000};
static const float kQ1BoostCorner = 3.1f, kQ1AttenCorner = 4.8f;       // shelf corner = low frequency x this
static const float kQ1LowBoostDb = 13.6f, kQ1LowAttenDb = 18.2f, kQ1HighBoostDb = 12.8f, kQ1HighAttenDb = 15.3f;
static const float kQ1H2 = 0.0045f;                                      // tube-style 2nd harmonic
class MEq1 {
 public:
  void Reset() { for (auto& b : bq_) b.Reset(); dc_.Reset(); }
  void Set(int lf, float lb, float la, int hf, float hb, float bw, int af, float ha, bool in, float out_db) {
    for (auto& b : bq_) b.Identity();
    float trim = 0.0f;
    if (in) {
      bq_[0].LowShelf(kQ1LowHz[lf] * kQ1BoostCorner, kQ1LowBoostDb * lb * 0.1f, 0.5f);
      bq_[1].LowShelf(kQ1LowHz[lf] * kQ1AttenCorner, -kQ1LowAttenDb * la * 0.1f, 0.5f);
      bq_[2].Peak(kQ1HighHz[hf] * 1.09f, kQ1HighBoostDb * hb * 0.1f, 1.2f * std::pow(0.1f, bw * 0.1f));
      bq_[3].HighShelf(kQ1AttenHz[af] * 0.318f, -kQ1HighAttenDb * ha * 0.1f, 0.5f);
      trim = -0.1f * hb;
    }
    in_ = in;
    out_.Set(DbToLin(out_db + trim));
  }
  void Process(float* l, float* r, int n) {
    for (int i = 0; i < n; ++i) {
      float o = out_.Tick();
      for (int c = 0; c < 2; ++c) {
        float x = (c ? r : l)[i];
        for (int k = 0; k < 4; ++k) x = bq_[k].Tick(x, c);
        x = dc_.Tick(Harm(x, kQ1H2, 0.0f), c);
        (c ? r : l)[i] = x * o;
      }
    }
  }
 private:
  Biquad bq_[4]; DcBlock dc_; Glide out_; bool in_ = true;
};

// ============================================================================================ XXL-MQ-5
static const float kQ5LowHz[5] = {200, 300, 500, 700, 1000}, kQ5HighHz[5] = {1500, 2000, 3000, 4000, 5000};
static const float kQ5DipHz[11] = {200, 300, 500, 700, 1000, 1500, 2000, 3000, 4000, 5000, 7000};
class MMq5 {
 public:
  void Reset() { for (auto& b : bq_) b.Reset(); }
  void Set(int lf, float lb, int df, float dip, int hf, float hb, bool in, float out_db) {
    for (auto& b : bq_) b.Identity();
    if (in) {
      bq_[0].Peak(kQ5LowHz[lf], 10.6f * lb * 0.1f, 0.66f);
      bq_[1].Peak(kQ5DipHz[df], -10.9f * dip * 0.1f, 1.04f);
      bq_[2].Peak(kQ5HighHz[hf], 8.5f * hb * 0.1f, 1.2f);
    }
    out_.Set(DbToLin(out_db));
  }
  void Process(float* l, float* r, int n) {
    for (int i = 0; i < n; ++i) {
      float o = out_.Tick();
      for (int c = 0; c < 2; ++c) {
        float x = (c ? r : l)[i];
        for (int k = 0; k < 3; ++k) x = bq_[k].Tick(x, c);
        (c ? r : l)[i] = x * o;
      }
    }
  }
 private:
  Biquad bq_[3]; Glide out_;
};

// ============================================================================================ tape (XXL-A80, XXL-AT12)
// Saturation: y = x (1 - a |x|^0.75), then a soft ceiling. The 0.75 power gives the measured slow rise of the third
// harmonic at low level (about 9 dB per 12 dB of level) and the measured level loss (-0.5 dB at -12, -1.5 at 0 dBFS).
static const float kTapeSat[2][4] = {{0.155f, 0.14f, 0.30f, 0.37f}, {0.10f, 0.08f, 0.06f, 0.08f}};   // per module (A80, AT12) and tape type
static const float kTapeCeil[2] = {2.6f, 1.9f};                         // soft ceiling (A80, AT12: the AT12 stays clean longer, then bends harder)
static const float kTapeEven = 0.002f;
static const float kWowSamples = 24.0f, kFlutterSamples = 0.5f;         // per sine at 100 % (two sines each)
struct TapeVoicing {
  bool at12; int speed; int head;
};
class Tape {
 public:
  void Reset() {
    for (auto& b : bq_) b.Reset();
    std::memset(dl_, 0, sizeof dl_); w_ = 0; dc_.Reset(); dw_ = df_ = 0;
  }
  void Set(bool at12, float in_db, float out_db, int speed, int type, float bias, float rhf, float phf, float plf,
           float wow, float flutter, bool hiss, bool repro, int head) {
    in_.Set(DbToLin(in_db)); out_.Set(DbToLin(out_db));
    a_ = kTapeSat[at12 ? 1 : 0][type]; ceil_inv_ = 1.0f / kTapeCeil[at12 ? 1 : 0]; repro_ = repro;
    wow_t_ = wow * 0.01f * kWowSamples; fl_t_ = flutter * 0.01f * kFlutterSamples;
    hiss_ = hiss ? (at12 ? 5.5e-5f : 1.2e-4f) : 0.0f;
    for (auto& b : bq_) b.Identity();
    bq_[0].HighShelf(10000.0f, rhf, 0.7f);              // record HF trim (before the tape)
    bq_[1].HighShelf(12000.0f, -0.5f * bias, 0.7f);     // bias offset tilts the top
    if (!at12) {                                        // speeds 7.5 / 15 / 30: the low bump moves up with speed
      static const float f[3] = {20, 32, 55}, g[3] = {2.8f, 3.1f, 4.0f};
      bq_[2].Peak(f[speed], g[speed], 0.8f);
      bq_[3].HighShelf(4000.0f, -0.4f, 0.7f);
      if (speed == 2) bq_[4].HighShelf(16000.0f, -0.8f, 0.7f);
    } else {                                            // speeds 3.75 / 7.5 / 15 / 30
      static const float hw[3] = {1.15f, 1.0f, 0.85f};
      if (speed == 0) { bq_[2].HighPass2(17.0f, 0.7f); bq_[3].Peak(3000.0f, 1.4f, 0.7f); bq_[4].LowPass2(10500.0f, 0.6f); }
      else if (speed == 1) { bq_[2].Peak(30.0f, 2.2f * hw[head], 1.2f); bq_[3].HighShelf(8000.0f, 1.0f, 0.7f); bq_[4].HighShelf(17000.0f, -2.6f, 1.0f); }
      else if (speed == 2) { bq_[2].Peak(30.0f, 3.3f * hw[head], 1.2f); bq_[3].Peak(8000.0f, 0.8f, 0.5f); bq_[4].HighShelf(17000.0f, -3.0f, 1.0f); }
      else { bq_[2].HighPass2(26.0f, 0.75f); bq_[3].HighShelf(6000.0f, -0.6f, 0.7f); }
    }
    bq_[5].HighShelf(6000.0f, phf, 0.7f);               // repro HF trim
    bq_[6].LowShelf(100.0f, plf, 0.7f);                 // repro LF trim
  }
  void Process(float* l, float* r, int n) {
    for (int i = 0; i < n; ++i) {
      float g = in_.Tick(), o = out_.Tick();
      dw_ += 0.0005f * (wow_t_ - dw_); df_ += 0.0005f * (fl_t_ - df_);
      float d = 0.0f;
      if (dw_ > 0.01f || df_ > 0.005f) {
        pw1_ += 2 * kPi * 0.6f / kSR; pw2_ += 2 * kPi * 0.93f / kSR; pf1_ += 2 * kPi * 7.0f / kSR; pf2_ += 2 * kPi * 11.3f / kSR;
        if (pw1_ > 2 * kPi) pw1_ -= 2 * kPi; if (pw2_ > 2 * kPi) pw2_ -= 2 * kPi;
        if (pf1_ > 2 * kPi) pf1_ -= 2 * kPi; if (pf2_ > 2 * kPi) pf2_ -= 2 * kPi;
        d = dw_ * (2.0f + std::sin(pw1_) + std::sin(pw2_)) + df_ * (2.0f + std::sin(pf1_) + std::sin(pf2_));
      }
      int di = static_cast<int>(d); float fr = d - di;
      seed_ = seed_ * 1664525u + 1013904223u;
      float noise = hiss_ * (static_cast<int32_t>(seed_) * (1.0f / 2147483648.0f));
      for (int c = 0; c < 2; ++c) {
        float x = (c ? r : l)[i];
        if (repro_) {
          x *= g;
          x = bq_[1].Tick(bq_[0].Tick(x, c), c);
          float ax = std::fabs(x), p = std::sqrt(ax * std::sqrt(ax)), k = 1.0f - a_ * p;
          if (k < 0.3f) k = 0.3f;
          x = x * k + kTapeEven * x * x;
          float q = x * ceil_inv_; q *= q;
          x = x / std::sqrt(std::sqrt(1.0f + q * q));
          x = dc_.Tick(x, c);
          for (int b = 2; b < 7; ++b) x = bq_[b].Tick(x, c);
          dl_[c][w_] = x;
          if (d > 0.0f) x = dl_[c][(w_ - di) & 255] * (1.0f - fr) + dl_[c][(w_ - di - 1) & 255] * fr;
          x = (x + (c ? -noise : noise)) * o;
        }
        (c ? r : l)[i] = x;
      }
      w_ = (w_ + 1) & 255;
    }
  }
 private:
  Biquad bq_[7]; DcBlock dc_; Glide in_, out_;
  float a_ = 0.14f, ceil_inv_ = 0.385f, hiss_ = 0, wow_t_ = 0, fl_t_ = 0, dw_ = 0, df_ = 0;
  float pw1_ = 0, pw2_ = 1.0f, pf1_ = 0, pf2_ = 2.0f;
  bool repro_ = true; uint32_t seed_ = 22222;
  float dl_[2][256]; int w_ = 0;
};

// ============================================================================================ reverb (XXL-224, XXL-480R)
// Our own design: predelay -> early taps + four input diffusers -> eight delay lines mixed by a Hadamard matrix. Each
// line carries its own decay gains (bass / mid, split at the crossover) and a treble damper, so the decay times in
// seconds are what the controls say. Two lines are read with slow movement. Fully wet: dry is a patch cable.
struct ReverbProgram {
  float scale;        // delay line lengths x this (room size)
  int pattern;        // early taps: 0 hall, 1 room, 2 plate, 3 chamber
  float early, late;  // levels
  float first_ms;     // when the first sound arrives
  float level_db;
  float move;         // movement depth x this
};
static const float kRevLineMs[8] = {29.7f, 37.1f, 41.1f, 43.7f, 53.3f, 59.9f, 67.3f, 73.1f};
static const float kRevEarlyMs[4][6] = {
    {5, 12, 19, 27, 38, 51}, {3, 7, 11, 16, 22, 29}, {1, 3, 6, 9, 13, 18}, {4, 9, 15, 22, 30, 39}};
static const float kRevEarlyGain[6] = {1.0f, -0.8f, 0.7f, -0.55f, 0.45f, 0.35f};
static const float kRevApMs[2][4] = {{4.7f, 3.6f, 12.7f, 9.3f}, {5.1f, 3.9f, 11.9f, 9.9f}};
static const ReverbProgram kProg224[9] = {
    {0.80f, 0, 0.45f, 0.65f, 0, -4.0f, 1.0f},    // Small Hall
    {0.85f, 0, 0.48f, 0.62f, 0, -3.5f, 1.0f},    // Bright Hall
    {1.25f, 0, 0.40f, 0.75f, 0, -8.5f, 1.0f},    // Large Hall
    {0.55f, 1, 0.45f, 0.62f, 1, -3.0f, 0.7f},    // Room
    {0.70f, 3, 0.015f, 1.00f, 12, -10.0f, 0.7f}, // Chamber
    {0.60f, 2, 0.09f, 0.95f, 0, -2.5f, 0.5f},    // Plate A
    {0.50f, 2, 0.09f, 0.95f, 2, -3.0f, 0.5f},    // Plate B
    {0.70f, 2, 0.10f, 0.90f, 4, -2.0f, 0.5f},    // Plate C
    {0.50f, 2, 0, 0, 1, 0.0f, 1.0f}};            // Chorus (its own path)
static const ReverbProgram kProg480[16] = {
    {0.75f, 0, 0.55f, 0.90f, 12, 0.0f, 0.6f},    // Small Hall
    {1.00f, 0, 0.45f, 1.00f, 20, 0.0f, 0.6f},    // Medium Hall
    {1.35f, 0, 0.30f, 1.00f, 30, -1.0f, 0.6f},   // Large Hall
    {1.20f, 0, 0.30f, 1.00f, 26, 0.0f, 0.5f},    // Dark Hall
    {0.40f, 1, 1.00f, 0.50f, 2, -2.0f, 0.4f},    // Small Room
    {0.65f, 1, 0.80f, 0.70f, 4, -2.0f, 0.4f},    // Large Room
    {0.50f, 1, 0.90f, 0.60f, 3, -2.0f, 0.3f},    // Wood Room
    {0.70f, 3, 0.50f, 0.90f, 8, -1.0f, 0.5f},    // Chamber
    {0.55f, 2, 0.60f, 0.90f, 0, 0.0f, 0.4f},     // Bright Plate
    {0.60f, 2, 0.50f, 0.90f, 2, 0.0f, 0.4f},     // Dark Plate
    {1.00f, 0, 0.40f, 1.00f, 10, 1.0f, 2.5f},    // Random Hall
    {0.85f, 1, 0.70f, 0.90f, 6, 2.0f, 2.5f},     // Random Space
    {0.45f, 1, 1.00f, 0.55f, 3, 4.0f, 0.5f},     // Ambience
    {0.30f, 1, 1.00f, 0.35f, 2, 4.0f, 0.4f},     // Tight Amb
    {0.35f, 2, 1.00f, 0.25f, 4, 3.0f, 0.3f},     // Post Amb
    {1.50f, 3, 0.35f, 1.00f, 18, 0.0f, 1.2f}};   // Wide Space
static const float kRevTankOut = 0.42f;        // tank output scale
static const float kRevDampMix = 0.20f;        // how much of each pass goes through the treble damper

struct ReverbSettings {
  const ReverbProgram* prog = &kProg224[0];
  bool chorus = false;
  float rt_low = 3.0f, rt_mid = 2.4f;      // seconds
  float xover_hz = 650.0f;                  // bass / mid split
  float damp_hz = 6000.0f; bool damp = true;   // treble damper corner
  float predelay_ms = 0, late_ms = 0;       // extra delay of everything / of the tail only
  float early_scale = 1.0f, late_scale = 1.0f;
  float diffusion = 0.6f;                   // 0..1
  float size = 1.0f;
  float move_hz = 0.7f, move_depth = 1.0f;  // samples of movement x prog->move
  float out_lp_hz = 20000.0f;
  float level_db = 0;
};

class Reverb {
 public:
  static const int kLMask = 16383, kPMask = 32767, kAMask = 1023;
  void Reset() {
    std::memset(line_, 0, sizeof line_); std::memset(pre_, 0, sizeof pre_); std::memset(ap_, 0, sizeof ap_);
    std::memset(lpx_, 0, sizeof lpx_); std::memset(lpx2_, 0, sizeof lpx2_); std::memset(lpt_, 0, sizeof lpt_);
    w_ = 0; olp_[0] = olp_[1] = 0; ph_ = 0; cph_ = 0;
  }
  void Set(const ReverbSettings& s) {
    const ReverbProgram& p = *s.prog;
    chorus_ = s.chorus;
    float scale = p.scale * s.size;
    for (int i = 0; i < 8; ++i) {
      float L = Clampf(kRevLineMs[i] * scale * 0.001f * kSR, 64.0f, 16000.0f);
      len_[i] = static_cast<int>(L);
      float secs = L / kSR;
      float gm = std::pow(10.0f, -3.0f * secs / s.rt_mid), gl = std::pow(10.0f, -3.0f * secs / s.rt_low);
      g_mid_[i] = gm; g_lowx_[i] = gl - gm;
    }
    cx_ = 1.0f - std::exp(-2.0f * kPi * Clampf(s.xover_hz, 40.0f, 12000.0f) / kSR);
    ct_ = 1.0f - std::exp(-2.0f * kPi * Clampf(s.damp_hz, 200.0f, 20000.0f) / kSR);
    dmix_ = s.damp ? kRevDampMix : 0.0f;
    float first = p.first_ms + s.predelay_ms;
    pre_n_ = static_cast<int>(Clampf(first * 0.001f * kSR, 0.0f, 20000.0f));
    late_n_ = pre_n_ + static_cast<int>(Clampf(s.late_ms * 0.001f * kSR, 0.0f, 9000.0f));
    for (int c = 0; c < 2; ++c)
      for (int k = 0; k < 6; ++k) {
        et_[c][k] = pre_n_ + static_cast<int>(kRevEarlyMs[p.pattern][k] * (c ? 1.13f : 1.0f) * (0.6f + 0.4f * scale) * 0.001f * kSR);
        eg_[c][k] = kRevEarlyGain[k] * ((c && (k & 1)) ? -1.0f : 1.0f);
      }
    for (int c = 0; c < 2; ++c)
      for (int k = 0; k < 4; ++k) apn_[c][k] = static_cast<int>(kRevApMs[c][k] * (0.5f + 0.5f * scale) * 0.001f * kSR) & kAMask;
    apg_ = 0.72f * Clampf(s.diffusion, 0.0f, 1.0f);
    early_ = p.early * s.early_scale; late_ = p.late * s.late_scale;
    move_inc_ = 2.0f * kPi * s.move_hz / kSR; move_ = s.move_depth * p.move * 6.0f;
    co_ = 1.0f - std::exp(-2.0f * kPi * Clampf(s.out_lp_hz, 300.0f, 20000.0f) / kSR);
    out_.Set(DbToLin(s.level_db + p.level_db));
  }
  void Process(float* l, float* r, int n) {
    for (int i = 0; i < n; ++i) {
      float o = out_.Tick();
      pre_[0][w_ & kPMask] = l[i]; pre_[1][w_ & kPMask] = r[i];
      float yl, yr;
      if (chorus_) {
        cph_ += 2.0f * kPi * 0.55f / kSR; if (cph_ > 2 * kPi) cph_ -= 2 * kPi;
        yl = yr = 0;
        for (int v = 0; v < 3; ++v) {
          float dl = (0.012f + 0.007f * v + 0.0018f * std::sin(cph_ * (1.0f + 0.31f * v) + v * 2.1f)) * kSR;
          float dr = (0.014f + 0.007f * v + 0.0018f * std::sin(cph_ * (1.0f + 0.27f * v) + v * 2.1f + 1.6f)) * kSR;
          yl += Frac(pre_[0], w_, dl, kPMask); yr += Frac(pre_[1], w_, dr, kPMask);
        }
        yl *= 0.45f; yr *= 0.45f;
      } else {
        // early taps
        float el = 0, er = 0;
        for (int k = 0; k < 6; ++k) { el += eg_[0][k] * pre_[0][(w_ - et_[0][k]) & kPMask]; er += eg_[1][k] * pre_[1][(w_ - et_[1][k]) & kPMask]; }
        // the tail's input, diffused
        float x[2] = {pre_[0][(w_ - late_n_) & kPMask], pre_[1][(w_ - late_n_) & kPMask]};
        for (int c = 0; c < 2; ++c)
          for (int k = 0; k < 4; ++k) {
            float* b = ap_[c][k];
            float d = b[(w_ - apn_[c][k]) & kAMask], v = x[c] + apg_ * d;
            b[w_ & kAMask] = v; x[c] = d - apg_ * v;
          }
        // eight lines
        ph_ += move_inc_; if (ph_ > 2 * kPi) ph_ -= 2 * kPi;
        float t[8];
        for (int k = 0; k < 8; ++k) {
          float v;
          if (k == 0 && move_ > 0.01f) v = Frac(line_[0], w_, len_[0] + move_ * (1.0f + std::sin(ph_)), kLMask);
          else if (k == 4 && move_ > 0.01f) v = Frac(line_[4], w_, len_[4] + move_ * (1.0f + std::cos(ph_ * 0.83f)), kLMask);
          else v = line_[k][(w_ - len_[k]) & kLMask];
          t[k] = v;
        }
        yl = (t[0] - t[2] + t[4] - t[6]) * kRevTankOut * late_ + el * early_ * 0.5f;
        yr = (t[1] - t[3] + t[5] - t[7]) * kRevTankOut * late_ + er * early_ * 0.5f;
        for (int k = 0; k < 8; ++k) {       // decay: bass and mid gains, treble damper
          float v = t[k];
          lpx_[k] += cx_ * (v - lpx_[k]); lpx2_[k] += cx_ * (lpx_[k] - lpx2_[k]);
          v = g_mid_[k] * v + g_lowx_[k] * lpx2_[k];
          lpt_[k] += ct_ * (v - lpt_[k]);
          t[k] = v + dmix_ * (lpt_[k] - v);
        }
        // Hadamard mix (8 x 8, orthonormal)
        for (int h = 1; h < 8; h <<= 1)
          for (int a = 0; a < 8; a += h << 1)
            for (int b = a; b < a + h; ++b) { float u = t[b], v = t[b + h]; t[b] = u + v; t[b + h] = u - v; }
        for (int k = 0; k < 8; ++k) line_[k][w_ & kLMask] = t[k] * 0.35355339f + ((k & 1) ? x[1] : x[0]) * 0.5f;
      }
      olp_[0] += co_ * (yl - olp_[0]); olp_[1] += co_ * (yr - olp_[1]);
      l[i] = olp_[0] * o; r[i] = olp_[1] * o;
      ++w_;
    }
  }
 private:
  static inline float Frac(const float* b, unsigned w, float d, int mask) {
    int di = static_cast<int>(d); float fr = d - di;
    return b[(w - di) & mask] * (1.0f - fr) + b[(w - di - 1) & mask] * fr;
  }
  float line_[8][16384], pre_[2][32768], ap_[2][4][1024];
  float lpx_[8], lpx2_[8], lpt_[8], g_mid_[8], g_lowx_[8];
  int len_[8], et_[2][6], apn_[2][4], pre_n_ = 0, late_n_ = 0;
  float eg_[2][6];
  float cx_ = 0.1f, ct_ = 0.5f, dmix_ = 0.5f, apg_ = 0.5f, early_ = 1, late_ = 1, move_inc_ = 0, move_ = 0, co_ = 1;
  float ph_ = 0, cph_ = 0, olp_[2] = {0, 0};
  bool chorus_ = false; unsigned w_ = 0; Glide out_;
};

}  // namespace xxl
