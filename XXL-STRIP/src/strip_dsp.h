// SPDX-License-Identifier: GPL-3.0-or-later
// XXL STRIP -- our own DSP blocks (L'Cronx). Host-free: plain numbers in, plain numbers out.
//   OwnEq      : filters + four bands from plain biquads. Used (a) as the G-mode equaliser and (b) as the cheap
//                detector copy for the FILTERS / EQ side-chain options in every mode.
//   Compressor : channel compressor. The E law (soft knee, RMS-style detector) is a table fitted to our own
//                measurements of reference behaviour (docs/measured-targets.md); the G law is a harder knee
//                with a peak detector.
//   Gate       : expander / gate with range, hold and release.
//   VuMeter    : VU ballistics (about 300 ms to full reading), 0 VU = -18 dBFS RMS.
// Every constant that shapes the sound is in the tables at the top of each block so it can be re-tuned in one place.
// Numbers marked UNVERIFIED are engineering choices not yet checked against published console data.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstring>

namespace xxl {

static const float kSR = 44100.0f;
static const float kPi = 3.14159265358979f;

inline float DbToLin(float db) { return std::exp(db * 0.115129255f); }
inline float LinToDb(float x) { return 8.68588964f * std::log(x > 1e-9f ? x : 1e-9f); }
inline float Clampf(float x, float lo, float hi) { return x < lo ? lo : (x > hi ? hi : x); }
inline float PoleCoef(float seconds) { return 1.0f - std::exp(-1.0f / (seconds * kSR)); }

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

// ---------------------------------------------------------------------------------------------------- own EQ
struct EqSettings {
  bool hpf_in = false, lpf_in = false, eq_in = true;
  float hpf = 16, lpf = 22000;
  float lf_gain = 0, lf_freq = 100; bool lf_bell = false;
  float lmf_gain = 0, lmf_freq = 600, lmf_q = 1.5f; bool lmf_d3 = false;
  float hmf_gain = 0, hmf_freq = 3000, hmf_q = 1.5f; bool hmf_x3 = false;
  float hf_gain = 0, hf_freq = 8000; bool hf_bell = false;
};

// G-mode voicing (UNVERIFIED against console data: the published character is "bandwidth narrows as gain rises,
// shelves overshoot a little, HPF 18 dB/octave, LPF 12 dB/octave").
static const float kGShelfSlope = 1.25f;    // > 1: a small dip/bump next to the shelf
static const float kGBellQ = 1.3f;          // LF / HF in BELL
static const float kGQGainLo = 0.6f;        // mid Q multiplier at 0 dB
static const float kGQGainHi = 1.5f;        // mid Q multiplier at full gain (18 dB)

class OwnEq {
 public:
  void Reset() { for (auto& b : bq_) b.Reset(); }
  // filters_only: the FILTERS side-chain option (no bands)
  void Configure(const EqSettings& s, bool filters_only) {
    if (s.hpf_in) { bq_[0].HighPass1(s.hpf); bq_[1].HighPass2(s.hpf, 1.0f); }   // 3rd-order Butterworth
    else { bq_[0].Identity(); bq_[1].Identity(); }
    if (s.lpf_in) bq_[2].LowPass2(s.lpf, 0.7071f); else bq_[2].Identity();
    if (!s.eq_in || filters_only) { for (int i = 3; i < 7; ++i) bq_[i].Identity(); return; }
    if (s.lf_bell) bq_[3].Peak(s.lf_freq, s.lf_gain, kGBellQ); else bq_[3].LowShelf(s.lf_freq, s.lf_gain, kGShelfSlope);
    float lmf = s.lmf_d3 ? s.lmf_freq / 3.0f : s.lmf_freq, hmf = s.hmf_x3 ? s.hmf_freq * 3.0f : s.hmf_freq;
    bq_[4].Peak(lmf, s.lmf_gain, s.lmf_q * QScale(s.lmf_gain));
    bq_[5].Peak(hmf, s.hmf_gain, s.hmf_q * QScale(s.hmf_gain));
    if (s.hf_bell) bq_[6].Peak(s.hf_freq, s.hf_gain, kGBellQ); else bq_[6].HighShelf(s.hf_freq, s.hf_gain, kGShelfSlope);
  }
  inline float Tick(float x, int c) {
    for (int i = 0; i < 7; ++i) x = bq_[i].Tick(x, c);
    return x;
  }

 private:
  static float QScale(float gain_db) {
    float t = std::fabs(gain_db) / 18.0f;
    return kGQGainLo + (kGQGainHi - kGQGainLo) * (t > 1.0f ? 1.0f : t);
  }
  Biquad bq_[7];
};

// ---------------------------------------------------------------------------------------------------- drive (G mode)
// Level-matched soft saturation, mostly 2nd harmonic at low settings, 3rd taking over when pushed.
inline float DriveShape(float x, float amount) {   // amount 0..1
  if (amount <= 0.0f) return x;
  float g = 1.0f + 2.0f * amount;                         // unit gain for small signals at every setting
  float y = x * g;
  y = y + 0.18f * amount * y * y;                         // even harmonics
  y = y / (1.0f + std::fabs(y) * (0.2f + 0.3f * amount));   // soft limit
  return y / g;
}

// ---------------------------------------------------------------------------------------------------- compressor
// E law: fitted to docs/measured-targets.md. Columns are 1 - 1/ratio.
//   slope  : dB of reduction per dB above the knee, far above threshold
//   offset : where the straight part crosses 0 dB reduction, relative to the threshold knob (dBFS RMS)
//   knee   : knee width in dB (reduction starts knee/2 below the crossing point)
static const int kLawN = 5;
static const float kLawX[kLawN] = {0.0f, 0.5f, 0.75f, 0.9f, 1.0f};
static const float kELawSlope[kLawN] = {0.0f, 0.34f, 0.675f, 0.80f, 1.0f};
static const float kELawOffset[kLawN] = {-3.0f, -6.2f, -9.4f, -11.9f, -12.6f};
static const float kELawKnee[kLawN] = {34.0f, 30.0f, 24.0f, 18.5f, 18.6f};
// G law (UNVERIFIED): textbook slope, harder knee, same level alignment as the E law at LIMIT.
static const float kGLawOffset = -12.6f;
static const float kGLawKnee = 6.0f;
// Timing. AUTO: about 10 dB of reduction in 20 ms (between our 33 ms measurement and the 11 ms the published
// card description gives). FAST: about 1 ms. Release knob = time for 90 % of the reduction to recover.
static const float kAttackAuto = 0.022f, kAttackFast = 0.001f;
static const float kDetAuto = 0.005f, kDetFast = 0.0004f;       // RMS detector time constants
static const float kPeakRelease = 0.005f;                        // G mode peak detector fall time
static const float kRatioLimit = 19.9f;                          // knob at or above this = LIMIT

struct CompLaw { float slope, cross, knee; };

inline float LawLerp(const float* tab, float x) {
  for (int i = 1; i < kLawN; ++i) {
    if (x <= kLawX[i]) {
      float t = (x - kLawX[i - 1]) / (kLawX[i] - kLawX[i - 1]);
      return tab[i - 1] + t * (tab[i] - tab[i - 1]);
    }
  }
  return tab[kLawN - 1];
}

inline CompLaw MakeLaw(float thr_db, float ratio, bool g_mode) {
  float x = ratio >= kRatioLimit ? 1.0f : 1.0f - 1.0f / (ratio < 1.0f ? 1.0f : ratio);
  CompLaw l;
  if (g_mode) { l.slope = x; l.cross = thr_db + kGLawOffset; l.knee = kGLawKnee; }
  else { l.slope = LawLerp(kELawSlope, x); l.cross = thr_db + LawLerp(kELawOffset, x); l.knee = LawLerp(kELawKnee, x); }
  return l;
}

// dB of gain reduction (>= 0) for a detector level in dBFS
inline float StaticReduction(const CompLaw& l, float level_db) {
  float over = level_db - l.cross, half = l.knee * 0.5f;
  if (over <= -half) return 0.0f;
  if (over >= half) return l.slope * over;
  float t = over + half;
  return l.slope * t * t / (2.0f * l.knee);
}

class Compressor {
 public:
  void Reset() { ms_ = 0; peak_ = 0; gr_ = 0; }
  void Configure(float thr_db, float ratio, bool fast, float release_s, bool auto_makeup, bool g_mode) {
    law_ = MakeLaw(thr_db, ratio, g_mode);
    g_mode_ = g_mode;
    det_c_ = PoleCoef(fast ? kDetFast : kDetAuto);
    att_c_ = PoleCoef(fast ? kAttackFast : kAttackAuto);
    rel_c_ = PoleCoef(Clampf(release_s, 0.05f, 8.0f) / 2.3026f);
    peak_rel_ = PoleCoef(kPeakRelease);
    // AUTO make-up (our own rule): 60 % of what the law takes off a -10 dBFS signal
    makeup_db_ = auto_makeup ? 0.6f * StaticReduction(law_, -10.0f) : 0.0f;
  }
  // key: the larger of the two side-chain channels (stereo linked). Returns reduction in dB (>= 0).
  inline float Tick(float key) {
    float level_db;
    if (g_mode_) {
      float a = std::fabs(key);
      peak_ = a > peak_ ? a : peak_ + peak_rel_ * (a - peak_);
      level_db = LinToDb(peak_) - 3.01f;             // a sine's peak reads as its RMS
    } else {
      ms_ += det_c_ * (key * key - ms_);
      level_db = 4.34294482f * std::log(ms_ > 1e-12f ? ms_ : 1e-12f);
    }
    float target = StaticReduction(law_, level_db);
    gr_ += (target > gr_ ? att_c_ : rel_c_) * (target - gr_);
    return gr_;
  }
  float makeup_db() const { return makeup_db_; }
  float reduction_db() const { return gr_; }

 private:
  CompLaw law_ = {0, 0, 1};
  bool g_mode_ = false;
  float det_c_ = 0.01f, att_c_ = 0.01f, rel_c_ = 0.001f, peak_rel_ = 0.01f, makeup_db_ = 0;
  float ms_ = 0, peak_ = 0, gr_ = 0;
};

// ---------------------------------------------------------------------------------------------------- gate / expander
// Measured alignment: the knob reads about 20 dB above the dBFS level where the gate acts. EXPAND is 2:1 downward
// (1 dB extra loss per dB below threshold), limited by RANGE. GATE is a switch with hysteresis (UNVERIFIED: 3 dB).
static const float kGateOffset = -20.0f;
static const float kGateHysteresis = 3.0f;
static const float kGateAttackNormal = 0.0015f, kGateAttackFast = 0.0001f;
static const float kGateDet = 0.002f;

class Gate {
 public:
  void Reset() { env_ = 0; att_ = 0; open_ = true; hold_left_ = 0; }
  void Configure(bool gate_mode, float thr_db, float range_db, float hold_s, float release_s, bool fast) {
    gate_mode_ = gate_mode;
    thr_ = thr_db + kGateOffset;
    range_ = range_db < 0 ? 0 : range_db;
    hold_ = static_cast<int>(hold_s * kSR);
    open_c_ = PoleCoef(fast ? kGateAttackFast : kGateAttackNormal);
    close_c_ = PoleCoef(Clampf(release_s, 0.05f, 8.0f));
    det_rel_ = PoleCoef(kGateDet);
  }
  // returns attenuation in dB (>= 0)
  inline float Tick(float key) {
    float a = std::fabs(key);
    env_ = a > env_ ? a : env_ + det_rel_ * (a - env_);
    float level = LinToDb(env_) - 3.01f;
    float target;
    if (gate_mode_) {
      if (level > thr_) { open_ = true; hold_left_ = hold_; }
      else if (level < thr_ - kGateHysteresis) {
        if (hold_left_ > 0) --hold_left_; else open_ = false;
      }
      target = open_ ? 0.0f : range_;
    } else {
      float under = thr_ - level;
      if (under <= 0.0f) { hold_left_ = hold_; target = 0.0f; }
      else if (hold_left_ > 0) { --hold_left_; target = 0.0f; }
      else target = under < range_ ? under : range_;
    }
    att_ += (target < att_ ? open_c_ : close_c_) * (target - att_);
    return att_;
  }
  float attenuation_db() const { return att_; }

 private:
  bool gate_mode_ = false, open_ = true;
  float thr_ = -50, range_ = 20, open_c_ = 0.1f, close_c_ = 0.001f, det_rel_ = 0.01f;
  int hold_ = 0, hold_left_ = 0;
  float env_ = 0, att_ = 0;
};

// ---------------------------------------------------------------------------------------------------- VU meter
// Rectified average with a 65 ms time constant: reaches 99 % of a steady tone in about 300 ms, the VU standard.
// 0 VU = -18 dBFS RMS (sine). Scale -20 .. +3 VU.
static const float kVuTau = 0.065f;
static const float kVuRefDb = -18.0f;
static const float kVuMin = -20.0f, kVuMax = 3.0f;

class VuMeter {
 public:
  void Reset() { avg_ = 0; }
  inline void Tick(float l, float r) {
    float a = 0.5f * (std::fabs(l) + std::fabs(r));
    avg_ += c_ * (a - avg_);
  }
  // VU reading in VU units (dB relative to 0 VU), clamped to the scale
  float Vu() const {
    float rms_db = LinToDb(avg_ * 1.11072f);    // rectified average of a sine -> its RMS
    return Clampf(rms_db - kVuRefDb, kVuMin, kVuMax);
  }
  static float ToUnit(float vu) { return (Clampf(vu, kVuMin, kVuMax) - kVuMin) / (kVuMax - kVuMin); }

 private:
  float c_ = PoleCoef(kVuTau);
  float avg_ = 0;
};

}  // namespace xxl
