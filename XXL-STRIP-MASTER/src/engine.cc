// SPDX-License-Identifier: GPL-3.0-or-later
// XXL STRIP MASTER for MPC OS / Force -- the engine behind mpc_engine(). 44.1 kHz, int16 stereo, 1..128 frames.
// INPUT trim -> HPF -> DRIVE -> EQ (LF / HF shelves) -> HF COMP -> IMAGE (width, space) -> TRANSFORMER -> OUTPUT trim.
// Nothing allocates or waits.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <new>
#include "master_dsp.h"
#include "denormals.h"
extern "C" {
#include "engine.h"
}
#include "param_ids.h"

namespace {
const int kMaxBlock = 128;
const int kStateVersion = 1;

struct Instance {
  float param[P_COUNT];
  volatile int display_rev;
  bool dirty, smooth_init;
  xxl::Biquad hp1, hp2, lf, hf, space;
  xxl::HfComp hfc;
  xxl::Transformer trafo;
  xxl::VuMeter vu_in, vu_out;
  float s_in, s_out, s_drive, s_width;
  int meter_q[2];
};
inline int Option(const Instance* s, int p) { return static_cast<int>(s->param[p] + 0.5f); }
int FindParam(const char* key, size_t len) {
  for (int p = 0; p < P_COUNT; ++p) if (strlen(kParamKeys[p]) == len && !strncmp(key, kParamKeys[p], len)) return p;
  return -1;
}
void Configure(Instance* s) {
  const float* p = s->param;
  int h = Option(s, P_HPF);
  if (h > 0) { s->hp1.HighPass1(xxl::kHpfHz[h]); s->hp2.HighPass2(xxl::kHpfHz[h], 1.0f); } else { s->hp1.Identity(); s->hp2.Identity(); }
  bool eq = Option(s, P_EQ_IN) != 0;
  s->lf.LowShelf(xxl::kLfHz[Option(s, P_LF_FREQ)], eq ? p[P_LF_GAIN] : 0.0f, xxl::kShelfSlope);
  s->hf.HighShelf(xxl::kHfHz[Option(s, P_HF_FREQ)], eq ? p[P_HF_GAIN] : 0.0f, xxl::kShelfSlope);
  s->space.LowShelf(xxl::kSpaceHz, Option(s, P_IMG_IN) ? p[P_SPACE] : 0.0f, xxl::kShelfSlope);
  s->hfc.Configure(p[P_HFC_THR], p[P_HFC_XOVER]);
  s->dirty = false;
}
int SaveState(const Instance* s, char* buf, int buf_len) {
  int len = snprintf(buf, buf_len, "v=%d;", kStateVersion);
  for (int p = 0; p < P_COUNT && len < buf_len; ++p) {
    if (kParamReadOnly[p]) continue;
    len += snprintf(buf + len, buf_len - len, "%s=%g;", kParamKeys[p], s->param[p]);
  }
  return len < buf_len ? len : buf_len - 1;
}
void SetValue(Instance* s, int p, float v) {
  if (kParamReadOnly[p] || v != v) return;
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
      memcpy(item, state, n); item[n] = 0;
      char* eq = strchr(item, '=');
      if (eq) { *eq = 0; int p = FindParam(item, strlen(item)); if (p >= 0) SetValue(s, p, static_cast<float>(atof(eq + 1))); }
    }
    state += n;
    if (*state == ';') ++state;
  }
  __atomic_add_fetch(&s->display_rev, 1, __ATOMIC_RELAXED);
}
void* Create(const char*) {
  Instance* s = new (std::nothrow) Instance();
  if (!s) return NULL;
  for (int p = 0; p < P_COUNT; ++p) s->param[p] = kParamDef[p];
  s->display_rev = 0; s->smooth_init = false; s->s_in = s->s_out = s->s_width = 1.0f; s->s_drive = 0.0f;
  s->meter_q[0] = s->meter_q[1] = -1;
  s->hfc.Reset(); s->trafo.Reset(); s->vu_in.Reset(); s->vu_out.Reset();
  Configure(s);
  return s;
}
void Destroy(void* inst) { delete static_cast<Instance*>(inst); }
void Midi(void*, const uint8_t*, int) {}
void SetParam(void* inst, const char* key, const char* val) {
  Instance* s = static_cast<Instance*>(inst);
  if (!strcmp(key, "state")) { LoadState(s, val); return; }
  int p = FindParam(key, strlen(key));
  if (p >= 0) SetValue(s, p, static_cast<float>(atof(val)));
}
int Display(const Instance* s, int p, char* buf, int len) {
  float v = s->param[p];
  switch (p) {
    case P_IN_GAIN: case P_OUT_GAIN: case P_LF_GAIN: case P_HF_GAIN: case P_HFC_THR: case P_WIDTH: case P_SPACE:
      return snprintf(buf, len, "%+.1f dB", v);
    case P_DRIVE: case P_DENSITY: return snprintf(buf, len, "%.1f", v);
    case P_HFC_XOVER: return snprintf(buf, len, "%.1f kHz", v * 0.001f);
    case P_VU: return snprintf(buf, len, "%+.1f VU", xxl::kVuMin + v * (xxl::kVuMax - xxl::kVuMin));
    case P_GR: return snprintf(buf, len, "-%.1f dB", v * 12.0f);
    default: return 0;
  }
}
int GetParam(void* inst, const char* key, char* buf, int buf_len) {
  const Instance* s = static_cast<const Instance*>(inst);
  if (!strcmp(key, "state")) return SaveState(s, buf, buf_len);
  if (!strcmp(key, "display_rev")) return snprintf(buf, buf_len, "%d", s->display_rev);
  size_t len = strlen(key);
  if (len > 8 && !strcmp(key + len - 8, "_display")) { int p = FindParam(key, len - 8); return p < 0 ? 0 : Display(s, p, buf, buf_len); }
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
void ProcessBlock(Instance* s, const int16_t* in_lr, int16_t* out_lr, int n) {
  if (s->dirty) Configure(s);
  const float* p = s->param;
  const bool drive_on = Option(s, P_DRIVE_IN) != 0, hfc_on = Option(s, P_HFC_IN) != 0, img_on = Option(s, P_IMG_IN) != 0;
  const bool trafo_on = Option(s, P_TRAFO) != 0;
  const float t_in = xxl::DbToLin(p[P_IN_GAIN]), t_out = xxl::DbToLin(p[P_OUT_GAIN]);
  const float t_drive = drive_on ? p[P_DRIVE] : 0.0f, t_width = img_on ? xxl::DbToLin(p[P_WIDTH]) : 1.0f;
  if (!s->smooth_init) { s->s_in = t_in; s->s_out = t_out; s->s_drive = t_drive; s->s_width = t_width; s->smooth_init = true; }
  const float a = xxl::PoleCoef(0.005f), density = p[P_DENSITY];
  for (int i = 0; i < n; ++i) {
    s->s_in += a * (t_in - s->s_in); s->s_out += a * (t_out - s->s_out);
    s->s_drive += a * (t_drive - s->s_drive); s->s_width += a * (t_width - s->s_width);
    float l = in_lr[2 * i] * (1.0f / 32768.0f) * s->s_in, r = in_lr[2 * i + 1] * (1.0f / 32768.0f) * s->s_in;
    s->vu_in.Tick(l, r);
    l = s->hp2.Tick(s->hp1.Tick(l, 0), 0); r = s->hp2.Tick(s->hp1.Tick(r, 1), 1);
    l = xxl::MasterDrive(l, s->s_drive, density); r = xxl::MasterDrive(r, s->s_drive, density);
    l = s->hf.Tick(s->lf.Tick(l, 0), 0); r = s->hf.Tick(s->lf.Tick(r, 1), 1);
    s->hfc.Tick(l, r, hfc_on);
    float mid = 0.5f * (l + r), side = 0.5f * (l - r);
    side = s->space.Tick(side, 0) * s->s_width;
    l = mid + side; r = mid - side;
    if (trafo_on) { l = s->trafo.Tick(l, 0); r = s->trafo.Tick(r, 1); }
    l *= s->s_out; r *= s->s_out;
    s->vu_out.Tick(l, r);
    out_lr[2 * i] = ToShort(l);
    out_lr[2 * i + 1] = ToShort(r);
  }
  const int src = Option(s, P_VU_SRC);            // 0 Output, 1 Input, 2 HF Red
  float gr = hfc_on ? s->hfc.reduction_db() : 0.0f;
  float vu = src == 0 ? s->vu_out.Vu() : (src == 1 ? s->vu_in.Vu() : -gr);
  float val[2] = {xxl::VuMeter::ToUnit(vu), xxl::Clampf(gr / 12.0f, 0.0f, 1.0f)};
  const int idx[2] = {P_VU, P_GR};
  bool moved = false;
  for (int m = 0; m < 2; ++m) {
    int q = static_cast<int>(val[m] * 127.0f + 0.5f);
    if (q != s->meter_q[m]) { s->meter_q[m] = q; s->param[idx[m]] = q / 127.0f; moved = true; }
  }
  if (moved) __atomic_add_fetch(&s->display_rev, 1, __ATOMIC_RELAXED);
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
