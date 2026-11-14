// SPDX-License-Identifier: GPL-3.0-or-later
// XXL STRIP BUS -- our own stereo bus compressor (L'Cronx). Host-free.
// A stereo-linked VCA-style compressor with stepped ratio, attack and release, an AUTO release made of a fast and a
// slow envelope, and (MODERN mode) a side-chain high-pass and dry/wet mix.
// UNVERIFIED against console data: the knee widths, the threshold alignment (0 on the knob = -18 dBFS) and the
// AUTO release time constants are engineering choices; they are the tables below.
#pragma once
#include "strip_dsp.h"

namespace xxl {

static const float kBusRatio[4] = {1.5f, 2.0f, 4.0f, 10.0f};
static const float kBusKnee[4] = {12.0f, 10.0f, 6.0f, 3.0f};          // softer at low ratios
static const float kBusAttack[6] = {0.0001f, 0.0003f, 0.001f, 0.003f, 0.010f, 0.030f};
static const float kBusRelease[4] = {0.1f, 0.3f, 0.6f, 1.2f};
static const float kBusThrOffset = -18.0f;                             // knob 0 = -18 dBFS (0 VU)
static const float kAutoFast = 0.15f, kAutoSlow = 2.5f, kAutoSlowCharge = 0.4f;
static const float kAutoSlowShare = 0.5f;   // the slow envelope holds at most this share of the reduction
static const float kBusPeakFall = 0.003f;

class BusComp {
 public:
  void Reset() { peak_ = 0; fast_ = 0; slow_ = 0; gr_ = 0; hp_.Reset(); }
  // ratio/attack/release: option indices; release 4 = AUTO; classic: no 1.5:1 (reads as 2:1), no SC HPF
  void Configure(float thr_db, int ratio, int attack, int release, bool classic, bool sc_hpf, float sc_hz) {
    if (classic && ratio == 0) ratio = 1;
    slope_ = 1.0f - 1.0f / kBusRatio[ratio];
    knee_ = kBusKnee[ratio];
    thr_ = thr_db + kBusThrOffset;
    att_c_ = PoleCoef(kBusAttack[attack]);
    auto_ = release >= 4;
    rel_c_ = PoleCoef((auto_ ? kAutoFast : kBusRelease[release]) / 2.3026f);
    slow_rel_c_ = PoleCoef(kAutoSlow / 2.3026f);
    slow_att_c_ = PoleCoef(kAutoSlowCharge);
    fall_c_ = PoleCoef(kBusPeakFall);
    hpf_on_ = sc_hpf && !classic;
    if (hpf_on_) hp_.HighPass2(sc_hz, 0.7071f);
  }
  // returns gain reduction in dB (>= 0); l, r are the side-chain inputs
  inline float Tick(float l, float r) {
    if (hpf_on_) { l = hp_.Tick(l, 0); r = hp_.Tick(r, 1); }
    float a = std::fabs(l), b = std::fabs(r);
    if (b > a) a = b;
    peak_ = a > peak_ ? a : peak_ + fall_c_ * (a - peak_);
    float over = LinToDb(peak_) - 3.01f - thr_, half = knee_ * 0.5f, target;
    if (over <= -half) target = 0.0f;
    else if (over >= half) target = slope_ * over;
    else { float t = over + half; target = slope_ * t * t / (2.0f * knee_); }
    fast_ += (target > fast_ ? att_c_ : rel_c_) * (target - fast_);
    if (auto_) {   // sustained reduction charges a slow envelope that then holds part of the gain down longer
      float st = fast_ * kAutoSlowShare;
      slow_ += (st > slow_ ? slow_att_c_ : slow_rel_c_) * (st - slow_);
      gr_ = fast_ > slow_ ? fast_ : slow_;
    } else gr_ = fast_;
    return gr_;
  }
  float reduction_db() const { return gr_; }

 private:
  float slope_ = 0.75f, knee_ = 6, thr_ = -18, att_c_ = 0.01f, rel_c_ = 0.001f, slow_rel_c_ = 0.0001f, slow_att_c_ = 0.0001f, fall_c_ = 0.01f;
  bool auto_ = true, hpf_on_ = false;
  float peak_ = 0, fast_ = 0, slow_ = 0, gr_ = 0;
  Biquad hp_;
};

}  // namespace xxl
