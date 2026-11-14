// SPDX-License-Identifier: GPL-3.0-or-later
// XXL STRIP (channel) for MPC OS / Force -- the engine behind mpc_engine() (mpc-vst-plugins wrapper/engine.h).
// 44.1 kHz, interleaved int16 stereo, blocks of 1..128 frames. Nothing here allocates, locks or waits in Process().
//
// Signal path:  INPUT gain / phase -> [DYNAMICS -> CARD]  (POSITION = Pre EQ, the default)
//                                     [CARD -> DYNAMICS]  (POSITION = Post EQ)
//               -> OUTPUT gain -> out
//   CARD     = high-pass, low-pass, four-band equaliser, drive.
//              MODEL E Brown / E Black: Dusk Audio's FourKEQDSP (GPL-3.0-or-later, third_party/dusk).
//              MODEL G: our own OwnEq + DriveShape (strip_dsp.h).
//   DYNAMICS = our own gate/expander and compressor (strip_dsp.h), stereo linked, one gain for both.
//              Side chain: INPUT (flat), FILTERS or EQ (a detector copy through OwnEq).
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <new>

#include "FourKEQDSP.hpp"
#include "denormals.h"
extern "C" {
#include "engine.h"
}
#include "param_ids.h"
#include "strip_dsp.h"

namespace {

const int kMaxBlock = 128;
const int kStateVersion = 1;
const float kGainSmooth = 0.005f;   // seconds, input / output gain glide

struct Instance {
  float param[P_COUNT];
  volatile int display_rev;
  bool dirty;

  duskaudio::FourKEQDSP card;       // E Brown / E Black
  xxl::OwnEq g_eq;                  // G
  xxl::OwnEq sc_eq;                 // side-chain detector copy
  xxl::Compressor comp;
  xxl::Gate gate;
  xxl::VuMeter vu_in, vu_out;

  float s_in, s_out, s_drive;       // smoothed linear gains and G-mode drive amount
  bool smooth_init;
  float l[kMaxBlock], r[kMaxBlock];
  int meter_q[3];                   // last reported meter steps (vu, gr, gate_gr)
};

inline int Option(const Instance* s, int p) { return static_cast<int>(s->param[p] + 0.5f); }

int FindParam(const char* key, size_t len) {
  for (int p = 0; p < P_COUNT; ++p) {
    if (strlen(kParamKeys[p]) == len && !strncmp(key, kParamKeys[p], len)) return p;
  }
  return -1;
}

// ------------------------------------------------------------------------------------------------ configuration
xxl::EqSettings ReadEq(const Instance* s) {
  const float* p = s->param;
  xxl::EqSettings e;
  e.hpf_in = Option(s, P_HPF_IN) != 0;
  e.lpf_in = Option(s, P_LPF_IN) != 0;
  e.eq_in = Option(s, P_EQ_IN) != 0;
  e.hpf = p[P_HPF_FREQ];
  e.lpf = p[P_LPF_FREQ];
  e.lf_gain = p[P_LF_GAIN]; e.lf_freq = p[P_LF_FREQ]; e.lf_bell = Option(s, P_LF_BELL) != 0;
  e.lmf_gain = p[P_LMF_GAIN]; e.lmf_freq = p[P_LMF_FREQ]; e.lmf_q = p[P_LMF_Q]; e.lmf_d3 = Option(s, P_LMF_D3) != 0;
  e.hmf_gain = p[P_HMF_GAIN]; e.hmf_freq = p[P_HMF_FREQ]; e.hmf_q = p[P_HMF_Q]; e.hmf_x3 = Option(s, P_HMF_X3) != 0;
  e.hf_gain = p[P_HF_GAIN]; e.hf_freq = p[P_HF_FREQ]; e.hf_bell = Option(s, P_HF_BELL) != 0;
  return e;
}

void Configure(Instance* s) {
  const float* p = s->param;
  const int model = Option(s, P_MODEL);            // 0 E Brown, 1 E Black, 2 G
  const bool g_mode = model == 2;
  xxl::EqSettings e = ReadEq(s);

  // the card (E modes). The /3 and x3 switches belong to the G console: ignored here.
  duskaudio::FourKEQDSP& c = s->card;
  c.setEqType(model == 1 ? 1 : 0);
  c.setHpfEnabled(e.hpf_in);
  c.setLpfEnabled(e.lpf_in);
  c.setHpfFreqHz(e.hpf);
  c.setLpfFreqHz(e.lpf);
  c.setLfGain(e.eq_in ? e.lf_gain : 0.0f);
  c.setLmGain(e.eq_in ? e.lmf_gain : 0.0f);
  c.setHmGain(e.eq_in ? e.hmf_gain : 0.0f);
  c.setHfGain(e.eq_in ? e.hf_gain : 0.0f);
  c.setLfFreqHz(e.lf_freq);
  c.setLmFreqHz(e.lmf_freq);
  c.setHmFreqHz(e.hmf_freq);
  c.setHfFreqHz(e.hf_freq);
  c.setLfBell(e.lf_bell);
  c.setHfBell(e.hf_bell);
  c.setLmQ(e.lmf_q);
  c.setHmQ(e.hmf_q);
  c.setSaturation(p[P_DRIVE]);
  c.setOversampling(Option(s, P_OS));              // 0 = 1x, 1 = 2x
  c.setInputGainDb(0.0f);
  c.setOutputGainDb(0.0f);
  c.setMsMode(false);
  c.setAutoGain(false);
  c.setBypass(false);

  s->g_eq.Configure(e, false);
  const int sc = Option(s, P_SC_SRC);              // 0 Input, 1 Filters, 2 EQ
  if (sc != 0) {
    xxl::EqSettings d = e;
    if (g_mode == false) { d.lmf_d3 = false; d.hmf_x3 = false; }
    s->sc_eq.Configure(d, sc == 1);
  }

  s->comp.Configure(p[P_COMP_THR], p[P_COMP_RATIO], Option(s, P_COMP_ATTACK) == 1, p[P_COMP_RELEASE],
                    Option(s, P_MAKEUP) == 1, g_mode);
  s->gate.Configure(Option(s, P_GATE_MODE) == 1, p[P_GATE_THR], p[P_GATE_RANGE], p[P_GATE_HOLD], p[P_GATE_RELEASE],
                    Option(s, P_GATE_FAST) == 1);
  s->dirty = false;
}

// ------------------------------------------------------------------------------------------------ state
bool StateSkips(int p) { return kParamReadOnly[p] != 0; }

int SaveState(const Instance* s, char* buf, int buf_len) {
  int len = snprintf(buf, buf_len, "v=%d;", kStateVersion);
  for (int p = 0; p < P_COUNT && len < buf_len; ++p) {
    if (StateSkips(p)) continue;
    len += snprintf(buf + len, buf_len - len, "%s=%g;", kParamKeys[p], s->param[p]);
  }
  return len < buf_len ? len : buf_len - 1;
}

void SetValue(Instance* s, int p, float v) {
  if (kParamReadOnly[p]) return;                   // meters: the engine's, not the host's
  if (v != v) return;
  if (kParamIsOption[p]) v = static_cast<float>(static_cast<int>(v + 0.5f));
  if (v < kParamMin[p]) v = kParamMin[p];
  if (v > kParamMax[p]) v = kParamMax[p];
  if (s->param[p] != v) { s->param[p] = v; s->dirty = true; }
}

void LoadState(Instance* s, const char* state) {
  char item[64];
  while (*state) {
    size_t n = strcspn(state, ";");
    if (n < sizeof item) {
      memcpy(item, state, n);
      item[n] = 0;
      char* eq = strchr(item, '=');
      if (eq) {
        *eq = 0;
        int p = FindParam(item, strlen(item));     // unknown keys ("v", keys of a later version) are skipped
        if (p >= 0) SetValue(s, p, static_cast<float>(atof(eq + 1)));
      }
    }
    state += n;
    if (*state == ';') ++state;
  }
  __atomic_add_fetch(&s->display_rev, 1, __ATOMIC_RELAXED);
}

// ------------------------------------------------------------------------------------------------ engine calls
void* Create(const char*) {
  Instance* s = new (std::nothrow) Instance();
  if (!s) return NULL;
  for (int p = 0; p < P_COUNT; ++p) s->param[p] = kParamDef[p];
  s->display_rev = 0;
  s->smooth_init = false;
  s->s_in = s->s_out = 1.0f;
  s->s_drive = 0.0f;
  s->meter_q[0] = s->meter_q[1] = s->meter_q[2] = -1;
  s->card.setOversampling(0);
  s->card.prepare(44100.0, kMaxBlock);
  s->g_eq.Reset(); s->sc_eq.Reset(); s->comp.Reset(); s->gate.Reset(); s->vu_in.Reset(); s->vu_out.Reset();
  Configure(s);
  return s;
}

void Destroy(void* inst) { delete static_cast<Instance*>(inst); }

void Midi(void*, const uint8_t*, int) {}

void SetParam(void* inst, const char* key, const char* val) {
  Instance* s = static_cast<Instance*>(inst);
  if (!strcmp(key, "state")) { LoadState(s, val); return; }
  int p = FindParam(key, strlen(key));
  if (p < 0) return;
  SetValue(s, p, static_cast<float>(atof(val)));
}

int FormatHz(char* buf, int len, float hz) {
  if (hz < 1000.0f) return snprintf(buf, len, "%.0f Hz", hz);
  return snprintf(buf, len, "%.2f kHz", hz * 0.001f);
}

int Display(const Instance* s, int p, char* buf, int len) {
  float v = s->param[p];
  switch (p) {
    case P_IN_GAIN: case P_OUT_GAIN: case P_HF_GAIN: case P_HMF_GAIN: case P_LMF_GAIN: case P_LF_GAIN:
    case P_COMP_THR: case P_GATE_THR:
      return snprintf(buf, len, "%+.1f dB", v);
    case P_GATE_RANGE: return snprintf(buf, len, "%.1f dB", v);
    case P_DRIVE: return snprintf(buf, len, "%.0f %%", v);
    case P_HPF_FREQ: case P_LPF_FREQ: case P_HF_FREQ: case P_LF_FREQ: return FormatHz(buf, len, v);
    case P_HMF_FREQ: return FormatHz(buf, len, (Option(s, P_MODEL) == 2 && Option(s, P_HMF_X3)) ? v * 3.0f : v);
    case P_LMF_FREQ: return FormatHz(buf, len, (Option(s, P_MODEL) == 2 && Option(s, P_LMF_D3)) ? v / 3.0f : v);
    case P_HMF_Q: case P_LMF_Q: return snprintf(buf, len, "%.2f", v);
    case P_COMP_RATIO:
      if (v >= xxl::kRatioLimit) return snprintf(buf, len, "LIMIT");
      return snprintf(buf, len, "%.1f:1", v);
    case P_COMP_RELEASE: case P_GATE_RELEASE: case P_GATE_HOLD: return snprintf(buf, len, "%.2f s", v);
    case P_VU: return snprintf(buf, len, "%+.1f VU", xxl::kVuMin + v * (xxl::kVuMax - xxl::kVuMin));
    case P_GR: return snprintf(buf, len, "-%.1f dB", v * 20.0f);
    case P_GATE_GR: return snprintf(buf, len, "-%.1f dB", v * 40.0f);
    default: return 0;
  }
}

int GetParam(void* inst, const char* key, char* buf, int buf_len) {
  const Instance* s = static_cast<const Instance*>(inst);
  if (!strcmp(key, "state")) return SaveState(s, buf, buf_len);
  if (!strcmp(key, "display_rev")) return snprintf(buf, buf_len, "%d", s->display_rev);
  size_t len = strlen(key);
  if (len > 8 && !strcmp(key + len - 8, "_display")) {
    int p = FindParam(key, len - 8);
    return p < 0 ? 0 : Display(s, p, buf, buf_len);
  }
  int p = FindParam(key, len);
  if (p < 0) return 0;
  if (kParamIsOption[p]) return snprintf(buf, buf_len, "%d", Option(s, p));
  return snprintf(buf, buf_len, "%g", s->param[p]);
}

void Render(void*, int16_t* out_lr, int frames) { memset(out_lr, 0, sizeof(int16_t) * 2 * frames); }

inline int16_t ToShort(float x) {
  x *= 32768.0f;
  return static_cast<int16_t>(x > 32767.0f ? 32767.0f : (x < -32768.0f ? -32768.0f : x));
}

// gate/expander + compressor on s->l / s->r, in place
void Dynamics(Instance* s, int n) {
  const bool comp_on = Option(s, P_DYN_IN) != 0;
  const bool gate_on = comp_on && Option(s, P_GATE_IN) != 0;
  const int sc = Option(s, P_SC_SRC);
  const float makeup = comp_on ? s->comp.makeup_db() : 0.0f;
  for (int i = 0; i < n; ++i) {
    float kl = s->l[i], kr = s->r[i];
    if (sc != 0) { kl = s->sc_eq.Tick(kl, 0); kr = s->sc_eq.Tick(kr, 1); }
    float al = kl < 0 ? -kl : kl, ar = kr < 0 ? -kr : kr;
    float key = al > ar ? al : ar;
    // both always run so the envelopes are right the moment a switch goes In
    float gr = s->comp.Tick(key), att = s->gate.Tick(key);
    float db = makeup - (comp_on ? gr : 0.0f) - (gate_on ? att : 0.0f);
    if (db != 0.0f) {
      float g = xxl::DbToLin(db);
      s->l[i] *= g;
      s->r[i] *= g;
    }
  }
}

// filters + equaliser + drive on s->l / s->r, in place
void Card(Instance* s, int n) {
  if (Option(s, P_MODEL) != 2) {
    const float* in[2] = {s->l, s->r};
    float* out[2] = {s->l, s->r};
    s->card.processBlock(in, out, 2, n);          // copies its input first, so in place is fine
    return;
  }
  const float drive_t = s->param[P_DRIVE] * 0.01f;
  for (int i = 0; i < n; ++i) {
    s->s_drive += 0.002f * (drive_t - s->s_drive);
    float a = s->g_eq.Tick(s->l[i], 0), b = s->g_eq.Tick(s->r[i], 1);
    s->l[i] = xxl::DriveShape(a, s->s_drive);
    s->r[i] = xxl::DriveShape(b, s->s_drive);
  }
}

void ReportMeters(Instance* s) {
  const int src = Option(s, P_VU_SRC);            // 0 Output, 1 Input, 2 Gain Red
  const bool comp_on = Option(s, P_DYN_IN) != 0;
  float gr = comp_on ? s->comp.reduction_db() : 0.0f;
  float att = (comp_on && Option(s, P_GATE_IN)) ? s->gate.attenuation_db() : 0.0f;
  float vu = src == 0 ? s->vu_out.Vu() : (src == 1 ? s->vu_in.Vu() : -gr);
  float val[3] = {xxl::VuMeter::ToUnit(vu), xxl::Clampf(gr / 20.0f, 0.0f, 1.0f), xxl::Clampf(att / 40.0f, 0.0f, 1.0f)};
  const int idx[3] = {P_VU, P_GR, P_GATE_GR};
  bool moved = false;
  for (int m = 0; m < 3; ++m) {
    int q = static_cast<int>(val[m] * 127.0f + 0.5f);   // MPC filmstrips have 128 frames
    if (q != s->meter_q[m]) { s->meter_q[m] = q; s->param[idx[m]] = q / 127.0f; moved = true; }
  }
  if (moved) __atomic_add_fetch(&s->display_rev, 1, __ATOMIC_RELAXED);
}

void ProcessBlock(Instance* s, const int16_t* in_lr, int16_t* out_lr, int n) {
  if (s->dirty) Configure(s);
  const float* p = s->param;
  const float t_in = xxl::DbToLin(p[P_IN_GAIN]) * (Option(s, P_PHASE) ? -1.0f : 1.0f);
  const float t_out = xxl::DbToLin(p[P_OUT_GAIN]);
  if (!s->smooth_init) { s->s_in = t_in; s->s_out = t_out; s->s_drive = p[P_DRIVE] * 0.01f; s->smooth_init = true; }
  const float a = xxl::PoleCoef(kGainSmooth);
  for (int i = 0; i < n; ++i) {
    s->s_in += a * (t_in - s->s_in);
    s->l[i] = in_lr[2 * i] * (1.0f / 32768.0f) * s->s_in;
    s->r[i] = in_lr[2 * i + 1] * (1.0f / 32768.0f) * s->s_in;
    s->vu_in.Tick(s->l[i], s->r[i]);
  }
  if (Option(s, P_DYN_POS) == 0) { Dynamics(s, n); Card(s, n); }
  else { Card(s, n); Dynamics(s, n); }
  for (int i = 0; i < n; ++i) {
    s->s_out += a * (t_out - s->s_out);
    float ol = s->l[i] * s->s_out, orr = s->r[i] * s->s_out;
    s->vu_out.Tick(ol, orr);
    out_lr[2 * i] = ToShort(ol);
    out_lr[2 * i + 1] = ToShort(orr);
  }
  ReportMeters(s);
}

void Process(void* inst, const int16_t* in_lr, int16_t* out_lr, int frames) {
  Instance* s = static_cast<Instance*>(inst);
  ScopedDenormalDisable no_denormals;
  for (int off = 0; off < frames; off += kMaxBlock) {
    int n = frames - off < kMaxBlock ? frames - off : kMaxBlock;
    ProcessBlock(s, in_lr + 2 * off, out_lr + 2 * off, n);
  }
}

const mpc_engine_t kEngine = {Create, Destroy, Midi, SetParam, GetParam, Render, Process};

}  // namespace

extern "C" const mpc_engine_t* mpc_engine(void) { return &kEngine; }
