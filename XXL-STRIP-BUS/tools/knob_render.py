import numpy as np, math, sys
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

S = 3                      # supersample
W = 400                    # final knob tile
N = W * S
C = N / 2.0
LOBES = 16
RS, AMP = 164.7 * S, 6.0 * S
RC = 141.5 * S
BG = np.array([36, 34, 30], float) / 255

yy, xx = np.mgrid[0:N, 0:N].astype(float)
X = xx - C + 0.5
Y = yy - C + 0.5

# knob-frame micro texture (rotates with the knob)
rng = np.random.default_rng(7)
TEX = ndi.gaussian_filter(rng.standard_normal((N, N)), 1.8)
TEX /= TEX.std()


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


SKIRT_BLACK = (0.050, 0.050, 0.055)
SKIRT_OFFWHITE = (0.90, 0.88, 0.82)   # off-white ring


def render(albedo, angle_deg, skirt=SKIRT_BLACK):
    a = math.radians(angle_deg)
    # world -> knob frame (knob turned clockwise by angle)
    ca, sa = math.cos(a), math.sin(a)
    kx = X * ca + Y * sa
    ky = -X * sa + Y * ca
    r = np.hypot(X, Y)
    th = np.arctan2(kx, -ky)            # angle from "up" in knob frame

    rim = RS + AMP * np.cos(LOBES * th)
    # --- heightfield (px units, scaled by S) ---
    d_sk = rim - r
    t = np.clip(d_sk / (16 * S), 0, 1)
    h_sk = 26 * S * np.sqrt(1 - (1 - t) ** 2)
    h_sk = np.where(d_sk > 0, h_sk, 0)

    d_cp = RC - r
    t2 = np.clip(d_cp / (11 * S), 0, 1)
    edge = np.sqrt(1 - (1 - t2) ** 2)
    dome = 7 * S * (1 - np.clip(r / RC, 0, 1) ** 2)
    h_cp = np.where(d_cp > 0, (22 * S) * edge + dome, 0)
    # fine lathe rings + rubber grain, only on the cap
    rings = 0.35 * S * np.sin(2 * math.pi * r / (2.6 * S))
    # grain sampled from the knob-frame texture so it turns with the knob
    gx = kx + C
    gy = ky + C
    grain = ndi.map_coordinates(TEX, [gy, gx], order=1, mode='reflect')
    h_cp += np.where(d_cp > 2 * S, rings * 0.5 + grain * 0.10 * S, 0)
    h = h_sk + h_cp
    h = ndi.gaussian_filter(h, 0.7 * S)

    # --- normals ---
    gy_, gx_ = np.gradient(h)
    nz = 1.0
    nx, ny = -gx_, -gy_
    nl = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / nl, ny / nl, nz / nl

    # neutral overhead key light (fixed in world space: from the top)
    L = np.array([0.0, -0.50, 0.866])
    L /= np.linalg.norm(L)
    Hh = L + np.array([0, 0, 1.0])
    Hh /= np.linalg.norm(Hh)
    ndl = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    ndh = np.clip(nx * Hh[0] + ny * Hh[1] + nz * Hh[2], 0, 1)

    # soft fill from the front so the bottom never goes dead
    amb = 0.33 + 0.10 * nz
    # cavity / ambient occlusion from height
    blur = ndi.gaussian_filter(h, 10 * S)
    ao = np.clip(1 - 0.020 * np.clip(blur - h, 0, None) / S * 3, 0.55, 1)
    # contact darkening where the cap meets the skirt
    ao *= 1 - 0.45 * np.exp(-(np.abs(d_cp + 1.5 * S) / (5 * S)) ** 2) * (d_cp < 3 * S)

    on_cap = d_cp > 0
    # materials
    alb = np.where(on_cap[..., None], albedo[None, None, :], np.array(skirt, float)[None, None, :])
    kd = np.where(on_cap, 0.52, 0.55)
    ks = np.where(on_cap, 0.10, 0.30)
    sh = np.where(on_cap, 38.0, 70.0)
    spec = ks * ndh ** sh

    # painted pointer (flat ink, rotation-safe)
    px = np.abs(kx)
    along_top = -RC + 2 * S            # y of cap top in knob frame
    y0, y1 = -RC + 0 * S, -52 * S
    cap_line = np.clip(6 * S - np.maximum(px, 0), -1, 1)
    # rounded-capsule distance
    dy = np.clip(ky, y0, y1) - ky
    dist = np.hypot(kx, dy)
    ink = smooth((6.0 * S - dist) / (1.2 * S)) * on_cap
    ink = ink * smooth((RC - 1.5 * S - r) / (1.0 * S) + 1)  # keep inside the cap edge
    ink_alb = np.array([0.045, 0.045, 0.05])
    alb = alb * (1 - ink[..., None]) + ink_alb[None, None, :] * ink[..., None]
    spec = spec * (1 - 0.6 * ink)

    lit = alb * (amb + kd * ndl)[..., None] * ao[..., None]
    lit += spec[..., None] * 0.9 * ao[..., None]
    lit = np.clip(lit, 0, 1)

    # coverage mask of the knob
    cov = smooth(d_sk / (1.2 * S) + 0.5)

    # static drop shadow on the panel (does not rotate: symmetric blob, offset down)
    sh_mask = ((np.hypot(X, Y - 9 * S) < RS + 1 * S)).astype(float)
    sh_mask = ndi.gaussian_filter(sh_mask, 9 * S) * 0.60
    bgc = BG[None, None, :] * (1 - sh_mask[..., None])
    out = bgc * (1 - cov[..., None]) + lit * cov[..., None]

    # fixed top rim light on the skirt edge (world space, never rotates)
    rim_l = np.clip((-Y / RS) - 0.55, 0, 1) ** 2 * smooth((rim - r) / (5 * S)) * (1 - smooth((rim - r) / (14 * S)))
    out += (rim_l * 0.10)[..., None] * cov[..., None]
    out = np.clip(out, 0, 1)
    img = Image.fromarray((out * 255 + 0.5).astype(np.uint8))
    return img.resize((W, W), Image.LANCZOS)


COL = {
    'RED': (204, 51, 45),
    'GREEN': (46, 161, 80),
    'BLUE': (47, 113, 205),
    'BROWN': (124, 75, 43),
    'BLACK': (53, 53, 56),
    'GREY': (225, 225, 233),
}
ANG = [0, -135, -60, 40, 95, 150]
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30)
SMALL = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)


def lin(c):
    return (np.array(c, float) / 255.0)


def main(out):
    TW, PITCH = 2300, 380
    H1, H2 = 470, 470
    sheet = Image.new('RGB', (TW, H1 + H2), tuple(int(v * 255) for v in BG))
    d = ImageDraw.Draw(sheet)
    for i, (name, c) in enumerate(COL.items()):
        cx = 192 + PITCH * i
        k0 = render(lin(c), 0)
        sheet.paste(k0, (cx - W // 2, 192 - W // 2))
        label = name
        w = d.textlength(label, font=FONT)
        d.text((cx - w / 2, 395), label, font=FONT, fill=(232, 232, 228))
        k1 = render(lin(c), ANG[i], SKIRT_OFFWHITE)
        sheet.paste(k1, (cx - W // 2, H1 + 192 - W // 2))
        label = f'{ANG[i]:+d}°' if ANG[i] else '0°'
        label = 'turned ' + label
        w = d.textlength(label, font=SMALL)
        d.text((cx - w / 2, H1 + 400), label, font=SMALL, fill=(170, 170, 165))
    sheet.save(out)




def main_single(out, skirt):
    sheet = Image.new('RGB', (2300, 470), tuple(int(v * 255) for v in BG))
    d = ImageDraw.Draw(sheet)
    for i, (name, c) in enumerate(COL.items()):
        cx = 192 + 380 * i
        sheet.paste(render(lin(c), 0, skirt), (cx - W // 2, 192 - W // 2))
        w = d.textlength(name, font=FONT)
        d.text((cx - w / 2, 395), name, font=FONT, fill=(232, 232, 228))
    sheet.save(out)


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[2] == 'offwhite':
        main_single(sys.argv[1], SKIRT_OFFWHITE)
    else:
        main(sys.argv[1])
