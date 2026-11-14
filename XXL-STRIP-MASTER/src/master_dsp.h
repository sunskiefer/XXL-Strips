// SPDX-License-Identifier: GPL-3.0-or-later
// XXL STRIP MASTER -- our own master colour stages (L'Cronx). Host-free.
// Five stages in the order of a mix-bus colour processor: DRIVE (harmonics, with DENSITY), a two-band shelving EQ,
// an HF compressor (only the band above X-OVER is turned down), a stereo IMAGE stage (WIDTH and SPACE on the side
// signal) and a TRANSFORMER stage (low-frequency saturation). Written from the published descriptions of that kind of
// unit; nothing was measured, so every constant below is UNVERIFIED and lives here to be re-tuned.
#pragma once
#include "strip_dsp.h"

namespace xxl {

static const float kHpfHz[4] = {0, 30, 40, 50};
static const float kLfHz[4] = {30, 50, 70, 90};
static const float kHfHz[4] = {8000, 12000, 16000, 20000};
static const float kShelfSlope = 0.7f;            // gentle, wide shelves
static const float kHfcRatioSlope = 0.6f;         // dB of high-band reduction per dB over threshold
static const float kHfcKnee = 8.0f;
static const float kHfcThrOffset = -24.0f;        // knob 0 = high band at -24 dBFS
static const float kHfcAttack = 0.001f, kHfcRelease = 0.06f;
static const float kSpaceHz = 250.0f;             // SPACE: a low shelf on the side signal
static const float kTrafoHz = 110.0f;             // TRANSFORMER: saturation below this
static const float kTrafoAmount = 0.5f;

// DRIVE 0..10 with DENSITY 0..10: unit gain for small signals; density moves the curve from mostly even harmonics
// with late limiting (0) to earlier, denser limiting (10).
inline float MasterDrive(float x, float drive, float density) {
  float a = drive * 0.1f, d = density * 0.1f;
  if (a <= 0.0f) return x;
  float g = 1.0f + 2.5f * a;
  float y = x * g;
  y = y + (0.22f - 0.12f * d) * a * y * y;
  y = y / (1.0f + std::fabs(y) * (0.15f + 0.45f * d) * a);
  return y / g;
}

class HfComp {
 public:
  void Reset() { lp_[0] = lp_[1] = 0; env_ = 0; gr_ = 0; }
  void Configure(float thr_db, float xover_hz) {
    thr_ = thr_db + kHfcThrOffset;
    lp_c_ = 1.0f - std::exp(-2.0f * kPi * Clampf(xover_hz, 500.0f, 20000.0f) / kSR);
    att_c_ = PoleCoef(kHfcAttack); rel_c_ = PoleCoef(kHfcRelease);
  }
  inline void Tick(float& l, float& r, bool on) {
    lp_[0] += lp_c_ * (l - lp_[0]); lp_[1] += lp_c_ * (r - lp_[1]);
    float hl = l - lp_[0], hr = r - lp_[1];
    float a = std::fabs(hl), b = std::fabs(hr);
    if (b > a) a = b;
    env_ = a > env_ ? a : env_ + rel_c_ * (a - env_);
    float over = LinToDb(env_) - 3.01f - thr_, half = kHfcKnee * 0.5f, target;
    if (over <= -half) target = 0.0f;
    else if (over >= half) target = kHfcRatioSlope * over;
    else { float t = over + half; target = kHfcRatioSlope * t * t / (2.0f * kHfcKnee); }
    gr_ += (target > gr_ ? att_c_ : rel_c_) * (target - gr_);
    if (on && gr_ > 0.001f) { float g = DbToLin(-gr_); l = lp_[0] + hl * g; r = lp_[1] + hr * g; }
  }
  float reduction_db() const { return gr_; }

 private:
  float thr_ = -24, lp_c_ = 0.5f, att_c_ = 0.1f, rel_c_ = 0.001f;
  float lp_[2] = {0, 0}, env_ = 0, gr_ = 0;
};

class Transformer {
 public:
  void Reset() { lp_[0] = lp_[1] = 0; }
  inline float Tick(float x, int c) {
    lp_[c] += c_ * (x - lp_[c]);
    float lo = lp_[c], s = lo * 3.0f;
    float sat = s / (1.0f + s * s * 0.5f) * (1.0f / 3.0f);   // odd harmonics as the low end gets loud, unit gain when quiet
    return x + kTrafoAmount * (sat - lo);
  }

 private:
  float c_ = 1.0f - std::exp(-2.0f * kPi * kTrafoHz / kSR);
  float lp_[2] = {0, 0};
};

}  // namespace xxl
