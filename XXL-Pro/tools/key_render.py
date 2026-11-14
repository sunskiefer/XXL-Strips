"""The DIN key (keycap with a lamp) rendered with the same light as tools/knob_render.py: the same key light from the top,
the same fill, cavity shading, highlights and drop shadow. Shape taken from the DIN panel's keys (76 x 104: a flat upper
part with the lamp, a raised square cap below). Output: RGBA, transparent background.

    key(colour_rgb, on, w, h) -> PIL image
"""
import math
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

KW, KH = 76, 104          # the key's own size (DIN panel pixels)
PAD = 10                   # room for the drop shadow
S = 8                      # render scale
COL = {"RED": (204, 51, 45), "GREEN": (46, 161, 80), "BLUE": (47, 113, 205), "BROWN": (124, 75, 43),
       "BLACK": (53, 53, 56), "GREY": (225, 225, 233)}          # the knob script's six cap colours
LAMP = (38.0, 22.0, 8.5)   # centre x, y and radius


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def rrect_dist(x, y, x0, y0, x1, y1, r):
    """signed distance to a rounded rectangle, positive inside"""
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    qx = np.abs(x - cx) - ((x1 - x0) / 2.0 - r)
    qy = np.abs(y - cy) - ((y1 - y0) / 2.0 - r)
    out = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
    return -out


_cache = {}


def key_big(colour, on):
    if (colour, on) in _cache:
        return _cache[(colour, on)]
    Wp, Hp = (KW + 2 * PAD) * S, (KH + 2 * PAD) * S
    yy, xx = np.mgrid[0:Hp, 0:Wp].astype(float)
    x = (xx + 0.5) / S - PAD
    y = (yy + 0.5) / S - PAD
    rng = np.random.default_rng(7)
    tex = ndi.gaussian_filter(rng.standard_normal((Hp, Wp)), 1.8)
    tex /= tex.std()

    d_body = rrect_dist(x, y, 0, 0, KW, KH, 4.0)
    h = np.where(d_body > 0, 6.0 * np.sqrt(1 - (1 - np.clip(d_body / 3.0, 0, 1)) ** 2), 0)          # the key's body
    d_cap = rrect_dist(x, y, 5, 42, KW - 5, KH - 5, 3.0)
    h += np.where(d_cap > 0, 12.0 * smooth(d_cap / 9.0), 0)                                            # the raised cap, sloped sides
    lx, ly, lr = LAMP
    rl = np.hypot(x - lx, y - ly)
    h -= 2.5 * smooth((lr + 3.0 - rl) / 1.5)                                                          # the lamp's recess
    on_lamp = rl < lr
    h += np.where(on_lamp, 2.5 + 5.0 * np.sqrt(np.clip(1 - (rl / lr) ** 2, 0, 1)), 0)                  # the lamp's dome
    h += np.where((d_body > 2) & ~on_lamp, tex * 0.05, 0)                                              # the same fine grain as the knob cap
    h = ndi.gaussian_filter(h * S, 0.7 * S / 3.0)

    gy_, gx_ = np.gradient(h)
    nx, ny, nz = -gx_, -gy_, np.ones_like(h)
    nl = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / nl, ny / nl, nz / nl
    L = np.array([0.0, -0.50, 0.866]); L /= np.linalg.norm(L)                  # knob_render.py's key light: from the top
    Hh = L + np.array([0, 0, 1.0]); Hh /= np.linalg.norm(Hh)
    ndl = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    ndh = np.clip(nx * Hh[0] + ny * Hh[1] + nz * Hh[2], 0, 1)
    amb = 0.33 + 0.10 * nz
    blur = ndi.gaussian_filter(h, 10 * S / 3.0)
    ao = np.clip(1 - 0.020 * np.clip(blur - h, 0, None) / (S / 3.0) * 3, 0.55, 1)

    alb = np.empty(h.shape + (3,))
    alb[...] = np.array(colour, float) / 255.0
    ring = (rl >= lr) & (rl < lr + 2.5)
    alb[ring] = (0.03, 0.03, 0.035)                                             # the lamp's dark surround
    lamp_alb = np.array([1.0, 0.16, 0.08]) if on else np.array([0.42, 0.02, 0.04])
    alb[on_lamp] = lamp_alb
    kd = np.where(on_lamp, 0.55, 0.52)
    ks = np.where(on_lamp, 0.55, 0.10)
    shn = np.where(on_lamp, 60.0, 38.0)
    spec = ks * ndh ** shn
    lit = alb * (amb + kd * ndl)[..., None] * ao[..., None] + spec[..., None] * 0.9 * ao[..., None]
    if on:                                                                      # the lamp glows and lights the key around it
        core = np.clip(1 - rl / lr, 0, 1)
        lit += on_lamp[..., None] * (np.array([1.0, 0.42, 0.10])[None, None, :] * (0.35 + 0.65 * core[..., None]))
        glow = np.exp(-(rl / (lr * 2.4)) ** 2) * (~on_lamp)
        lit += glow[..., None] * np.array([0.55, 0.10, 0.04])[None, None, :] * (0.25 + 0.75 * alb.mean(axis=2, keepdims=True))
    lit = np.clip(lit, 0, 1)

    cov = smooth(d_body * S / 3.0 / 1.2 + 0.5)
    shadow = ndi.gaussian_filter((rrect_dist(x, y - 3.0, 0, 0, KW, KH, 4.0) > 0).astype(float), 3.0 * S) * 0.60   # the knob's shadow: straight down
    alpha = cov + shadow * (1 - cov)
    rgb = lit * (cov / np.maximum(alpha, 1e-4))[..., None]
    out = np.concatenate([rgb, alpha[..., None]], axis=2)
    im = Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
    _cache[(colour, on)] = im
    return im


def key(colour, on, w, h):
    """the key at w x h (the key itself; the picture is a little larger for its shadow: see pad(w))"""
    big = key_big(tuple(colour), bool(on))
    k = w / float(KW)
    return big.resize((int(round((KW + 2 * PAD) * k)), int(round((KH + 2 * PAD) * h / float(KH)))), Image.LANCZOS)


if __name__ == "__main__":
    import sys
    sheet = Image.new("RGBA", (6 * 300, 2 * 380), (36, 34, 30, 255))
    for i, c in enumerate(COL):
        for j in (0, 1):
            im = key(COL[c], j, 228, 312)
            sheet.alpha_composite(im, (i * 300 + 6, j * 380 + 4))
    sheet.convert("RGB").save(sys.argv[1])
