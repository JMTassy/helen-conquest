"""HELEN · motion showreel, 15 s, 100 % code. NON_SOVEREIGN · authority=false · 0 credits.

Every frame is computed from this file: no generated image, no stock, no AI model. Same timeline drives
picture and sound. The lockup prints this script's own SHA-256, so the film cites what made it.

    python showreel.py --fonts DIR --out DIR [--workers 4]        # frames + audio.wav + render.json
    python showreel.py --fonts DIR --out DIR --only 120 300       # a few frames, for checking

Grammar (helen-design-motion): ink / parchment / gold = witnessed / copper = rejected; Cormorant Garamond for
display, IBM Plex Mono for data; snaps with ease-out, no fades; trails are drawn strokes, never blur; the gold
point at the centre never moves; one refusal scene; 0.3 s of black before the lockup.
"""
import argparse
import hashlib
import json
import math
import pathlib
import wave
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, SS, FPS, N = 1920, 1080, 2, 30, 450
CX, CY = W / 2, H / 2
INK, PARCH, GOLD, COPPER = (10, 10, 12), (232, 222, 200), (201, 160, 74), (168, 88, 58)
DIM, MID = (52, 50, 46), (128, 120, 106)
SCRIPT_SHA = hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()

# scene table: name, first frame, end frame (exclusive)
SCENES = [("OPEN", 0, 36), ("TYPE", 36, 102), ("RULE", 102, 168), ("FIELD", 168, 228), ("GRID", 228, 282),
          ("REFUSAL", 282, 336), ("TIME", 336, 390), ("BLACK", 390, 399), ("LOCKUP", 399, 450)]
FONTS = {}


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def seg(f, a, b):
    return clamp((f - a) / (b - a))


def eo(x):  # ease-out cubic: fast arrival, soft landing
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ei(x):
    x = clamp(x)
    return x ** 3


@lru_cache(maxsize=None)
def font(name, size):
    return ImageFont.truetype(str(FONTS["dir"] / name), int(round(size * SS)))


DISPLAY, DISPLAY_IT, DISPLAY_MED, MONO, MONO_MED = ("Cormorant-SemiBold.ttf", "Cormorant-MediumItalic.ttf",
                                                    "Cormorant-Medium.ttf", "PlexMono-Regular.ttf",
                                                    "PlexMono-Medium.ttf")


class Canvas:
    """Draws in output coordinates on a 2x supersampled image."""

    def __init__(self, bg=INK):
        self.im = Image.new("RGB", (W * SS, H * SS), bg)
        self.d = ImageDraw.Draw(self.im)

    def line(self, pts, col, w=1.0):
        self.d.line([(x * SS, y * SS) for x, y in pts], fill=col, width=max(1, int(round(w * SS))))

    def circle(self, x, y, r, fill=None, outline=None, w=1.0):
        self.d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=fill, outline=outline,
                       width=max(1, int(round(w * SS))))

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, w=1.0):
        if x1 <= x0 or y1 <= y0:
            return
        self.d.rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], fill=fill, outline=outline,
                         width=max(1, int(round(w * SS))))

    def text(self, x, y, s, fname, size, col, anchor="ls", track=0.0, lnum=False):
        """Tracked text; anchor 'ls' left-baseline, 'ms' centre-baseline, 'rs' right-baseline."""
        f = font(fname, size)
        feats = ["lnum"] if lnum else None
        widths = [f.getlength(ch, features=feats) / SS for ch in s]
        total = sum(widths) + track * max(0, len(s) - 1)
        x0 = x - total / 2 if anchor[0] == "m" else x - total if anchor[0] == "r" else x
        cx = x0
        for ch, wd in zip(s, widths):
            self.d.text((cx * SS, y * SS), ch, font=f, fill=col, anchor="ls", features=feats)
            cx += wd + track
        return x0, total

    def width(self, s, fname, size, track=0.0):
        f = font(fname, size)
        return sum(f.getlength(ch) / SS for ch in s) + track * max(0, len(s) - 1)

    def out(self):
        return self.im.resize((W, H), Image.LANCZOS)


def point(c):  # the one element that never moves
    c.circle(CX, CY, 5.5, fill=GOLD)


def hud(c, f, idx, name):
    c.text(48, 52, "HELEN  —  MOTION SHOWREEL 2026", MONO, 13, MID, track=1.5)
    c.text(W - 48, 52, f"F {f:04d} / {N:04d}", MONO, 13, MID, anchor="rs", track=1.5)
    c.text(48, H - 40, f"{idx:02d}", MONO_MED, 13, GOLD, track=1.5)
    c.text(78, H - 40, f"—  {name}", MONO, 13, MID, track=1.5)
    c.text(W - 48, H - 40, f"00:{f // FPS:02d}.{f % FPS:02d}", MONO, 13, MID, anchor="rs", track=1.5)
    for x, y, sx, sy in ((24, 24, 1, 1), (W - 24, 24, -1, 1), (24, H - 24, 1, -1), (W - 24, H - 24, -1, -1)):
        c.line([(x, y), (x + 14 * sx, y)], DIM, 1)
        c.line([(x, y), (x, y + 14 * sy)], DIM, 1)


# ------------------------------------------------------------------ 00 OPEN

def s_open(c, f):
    ext = eo(seg(f, 6, 22)) * (W / 2 - 96)
    if ext > 0:
        c.line([(CX - ext, CY), (CX + ext, CY)], GOLD, 1.2)
        for k in range(1, 15):
            dx = k * 60
            if dx <= ext:
                tall = k % 4 == 0
                for sgn in (-1, 1):
                    c.line([(CX + sgn * dx, CY - (9 if tall else 5)), (CX + sgn * dx, CY + (9 if tall else 5))], MID, 1)
                    if tall:
                        c.text(CX + sgn * dx, CY + 30, f"{sgn * dx:+d}", MONO, 11, MID, anchor="ms")
    word = "HELEN"
    shown = word[:max(0, min(5, f - 9))]
    if shown:
        cx = CX - c.width(word, DISPLAY, 72, 26) / 2
        for i, ch in enumerate(shown):
            c.text(cx, CY - 46, ch, DISPLAY, 72, PARCH)
            cx += c.width(ch, DISPLAY, 72) + 26
    line2 = "MOTION DESIGN, WRITTEN IN CODE"
    n2 = max(0, min(len(line2), 2 * (f - 15)))
    if n2:
        full = c.width(line2, MONO, 17, 3)
        x0 = CX - full / 2
        c.text(x0, CY + 72, line2[:n2], MONO, 17, PARCH, track=3)
        if f % 4 < 2:
            cw = c.width(line2[:n2], MONO, 17, 3)
            c.rect(x0 + cw + 6, CY + 58, x0 + cw + 16, CY + 75, fill=GOLD)


def ev_open():
    return [(t, "click") for t in [(10 + i) / FPS for i in range(5)]] + \
           [((15 + i / 2) / FPS, "tick") for i in range(0, 30, 2)] + [(6 / FPS, "draw")]


# ------------------------------------------------------------------ 01 TYPE

WORD = "MOTION"


def type_layout(c, track, italic_upto):
    xs, cx = [], 0.0
    for i, ch in enumerate(WORD):
        fn = DISPLAY_IT if i < italic_upto else DISPLAY
        xs.append((cx, fn))
        cx += c.width(ch, fn, 300) + track
    total = cx - track
    return [(CX - total / 2 + x, fn) for x, fn in xs], total


def s_type(c, f):
    g = f - 36
    track = 10 + 50 * eo(seg(g, 46, 60))
    italic_upto = int(clamp((g - 44) / 3, 0, 6)) if g >= 44 else 0
    pos, total = type_layout(c, track, italic_upto)
    base = CY + 108
    for i, ((x, fn), ch) in enumerate(zip(pos, WORD)):
        t0 = 2 + 4 * i
        if g < t0:
            continue
        sgn = -1 if i % 2 == 0 else 1
        off = lambda gg: sgn * 760 * (1 - eo((gg - t0) / 7))  # noqa: E731
        y = base + off(g)
        wch = c.width(ch, fn, 300)
        for k in (1, 2, 3):  # trails: three earlier samples drawn as strokes
            if g - k >= t0 and abs(off(g - k)) > 2:
                for fx in (0.2, 0.5, 0.8):
                    c.line([(x + wch * fx, y - 200), (x + wch * fx, base + off(g - k) - 200)], DIM if k > 1 else MID, 1)
        c.text(x, y, ch, fn, 300, PARCH)
    x0, x1 = CX - total / 2 - 40, CX + total / 2 + 40
    guides = [(base, GOLD, "BASELINE  0.00", 30), (base - 189, MID, "CAP  0.63", 33), (base - 120, DIM, "X-HEIGHT  0.40", 36)]
    for y, col, lab, t0 in guides:
        p = eo(seg(g, t0, t0 + 6))
        if p > 0:
            c.line([(x0, y), (x0 + (x1 - x0) * p, y)], col, 1)
            if p >= 1:
                c.text(x1 + 14, y + 4, lab, MONO, 12, col if col != DIM else MID)
    if g >= 44:
        c.text(x0, base + 64, f"TRACKING  +{int(round(track)):02d}    ITALIC  {italic_upto}/6", MONO, 13, MID, track=1.5)


def ev_type():
    ev = [((36 + 2 + 4 * i + 6) / FPS, "hit") for i in range(6)]
    ev += [((36 + t) / FPS, "draw") for t in (30, 33, 36)]
    ev += [((36 + 44 + 3 * i) / FPS, "click") for i in range(6)]
    return ev


# ------------------------------------------------------------------ 02 RULE

S_MAX, NS, R_H = 64.0, 5200, 360.0
_s = np.linspace(0, S_MAX, NS)
_dec = np.exp(-0.011 * _s)
HX = CX + R_H * (0.6 * np.sin(3 * _s + math.pi / 2) + 0.4 * np.sin(5.01 * _s)) * _dec
HY = CY + R_H * (0.6 * np.sin(4 * _s) + 0.4 * np.sin(2.99 * _s + 1.0)) * _dec


def s_rule(c, f):
    g = f - 102
    n = int(NS * clamp(g / 54))
    if n > 1:
        pts = list(zip(HX[:n].tolist(), HY[:n].tolist()))
        c.line(pts, GOLD, 1.0)
        hx, hy = pts[-1]
        if g < 54:
            c.line([(hx - 12, hy), (hx + 12, hy)], PARCH, 1)
            c.line([(hx, hy - 12), (hx, hy + 12)], PARCH, 1)
        c.circle(hx, hy, 3.5, fill=PARCH)
    # x(s) trace panel
    px0, py0, pw, ph = 1490, 250, 360, 110
    c.line([(px0, py0 + ph / 2), (px0 + pw, py0 + ph / 2)], DIM, 1)
    c.text(px0, py0 - 12, "x(s)", MONO, 12, MID)
    if n > 1:
        lo = max(0, n - 900)
        xs = np.linspace(px0, px0 + pw, n - lo)
        ys = py0 + ph / 2 - (HX[lo:n] - CX) / R_H * ph / 2
        c.line(list(zip(xs.tolist(), ys.tolist())), PARCH, 1)
    s_now = S_MAX * clamp(g / 54)
    lines = ["x = 0.6 sin(3s + pi/2) + 0.4 sin(5.01s)", "y = 0.6 sin(4s) + 0.4 sin(2.99s + 1)",
             "x, y  ×  e^(−0.011 s)", f"s = {s_now:05.2f}      samples {n:>4d}"]
    for k, ln in enumerate(lines):
        c.text(96, H - 210 + 28 * k, ln, MONO, 15, PARCH if k < 3 else GOLD, track=0.5)


def ev_rule():
    return [((102 + g) / FPS, "pen") for g in range(0, 54, 3)]


# ------------------------------------------------------------------ 03 FIELD

CELL = 20
GX = np.arange(CELL / 2, W, CELL)
GY = np.arange(CELL / 2 + 10, H, CELL)


def s_field(c, f):
    g = f - 168
    rows_vis = int(g * 3.2)
    th = math.radians(40 + 95 * eo(seg(g, 24, 56)))
    L = np.array([math.cos(th) * 0.75, -math.sin(th) * 0.75, 0.66])
    L /= np.linalg.norm(L)
    R = 410.0
    for j, y in enumerate(GY):
        if j > rows_vis:
            break
        dy = (y - CY) / R
        for x in GX:
            dx = (x - CX) / R
            r2 = dx * dx + dy * dy
            if r2 < 1:
                nz = math.sqrt(1 - r2)
                lum = max(0.0, dx * L[0] + dy * L[1] + nz * L[2]) ** 1.25 * 0.94 + 0.04
                rad = 0.5 * CELL * math.sqrt(lum) * 0.96
                if rad > 0.6:
                    c.circle(x, y, rad, fill=PARCH)
            else:
                c.circle(x, y, 0.9, fill=DIM)
    if rows_vis < len(GY):
        ys = GY[min(rows_vis, len(GY) - 1)] + CELL / 2
        c.line([(0, ys), (W, ys)], GOLD, 1)
    c.text(96, H - 110, f"DENSITY = LUMINANCE    96 × 54 CELLS    LIGHT {int(round(math.degrees(th))):03d}°",
           MONO, 14, PARCH, track=1.5)
    c.text(96, H - 84, "halftone sampling, after Harmon & Knowlton, 1966", MONO, 12, MID, track=1)


def ev_field():
    return [((168 + g) / FPS, "tick") for g in range(0, 17)] + [(192 / FPS, "riser_s")]


# ------------------------------------------------------------------ 04 GRID

COLW, GUT, MARG = 118, 24, 120


def colx(cn):
    return MARG + cn * (COLW + GUT)


def span(c0, n):
    return colx(c0), colx(c0) + n * COLW + (n - 1) * GUT


LAY_A = [(span(0, 4), (150, 520)), (span(4, 4), (150, 380)), (span(8, 4), (150, 620)),
         (span(4, 4), (400, 930)), (span(0, 4), (540, 930)), (span(8, 4), (640, 930))]
LAY_B = [(span(0, 6), (150, 440)), (span(6, 3), (150, 440)), (span(9, 3), (150, 930)),
         (span(0, 3), (460, 930)), (span(3, 3), (460, 930)), (span(6, 3), (460, 930))]
NAMES = ["TYPE", "RULE", "FIELD", "GRID", "REFUSAL", "TIME"]


def s_grid(c, f):
    g = f - 228
    for k in range(13):
        if g >= k * 0.8:
            x = colx(k) - GUT / 2 if 0 < k < 12 else (MARG if k == 0 else colx(11) + COLW)
            c.line([(x, 110), (x, H - 110)], DIM, 1)
    for i in range(6):
        t0 = 10 + 3 * i
        if g < t0:
            continue
        (ax0, ax1), (ay0, ay1) = LAY_A[i]
        (bx0, bx1), (by0, by1) = LAY_B[i]
        u = eo(seg(g, 32 + i, 38 + i))
        x0, x1 = ax0 + (bx0 - ax0) * u, ax1 + (bx1 - ax1) * u
        y0, y1 = ay0 + (by0 - ay0) * u, ay1 + (by1 - ay1) * u
        y1v = y0 + (y1 - y0) * eo(seg(g, t0, t0 + 4))  # mask wipe downward
        col = GOLD if i == 2 else PARCH
        c.rect(x0, y0, x1, y1v, fill=col)
        if y1v - y0 > 70:
            c.text(x0 + 18, y0 + 34, f"{i + 1:02d} — {NAMES[i]}", MONO_MED, 13, INK, track=1.5)
        if y1v - y0 > (y1 - y0) * 0.95 and y1 - y0 > 180:
            c.text(x1 - 18, y1 - 22, f"{i + 1:02d}", DISPLAY, 150, INK, anchor="rs", lnum=True)
    c.text(W - 120, H - 76, f"12 COLUMNS  ·  GUTTER {GUT}  ·  REFLOW {int(100 * eo(seg(g, 32, 43))):3d}%", MONO,
           13, MID, anchor="rs", track=1.5)


def ev_grid():
    return [((228 + 10 + 3 * i + 2) / FPS, "hit") for i in range(6)] + [(260 / FPS, "whoosh")] + \
           [((228 + k) / FPS, "tick") for k in range(0, 10, 2)]


# ------------------------------------------------------------------ 05 REFUSAL

_rng = np.random.default_rng(1966)
NP_ = 150
P_SPAWN = _rng.uniform(4, 34, NP_)
P_ANG = _rng.uniform(0, 2 * math.pi, NP_)
P_OK = _rng.uniform(0, 1, NP_) < 0.8
P_REST = _rng.uniform(26, 205, NP_)
P_V, P_R0, R_RING = 38.0, 1150.0, 250.0


def particle(k, g):
    """Radius at local frame g, plus state: None (not born), 'in', 'rest', 'out', and hit frame."""
    t = g - P_SPAWN[k]
    if t < 0:
        return None, None, None
    r = P_R0 - P_V * t
    if P_OK[k]:
        return (max(r, P_REST[k]), "rest" if r <= P_REST[k] else "in", None)
    hit_t = (P_R0 - R_RING - 6) / P_V
    if t < hit_t:
        return r, "in", None
    return R_RING + 6 + 0.75 * P_V * (t - hit_t), "out", P_SPAWN[k] + hit_t


def s_refusal(c, f):
    g = f - 282
    p = eo(seg(g, 0, 6))
    if p > 0:
        n = 180
        arc = [(CX + R_RING * math.cos(2 * math.pi * a / n - math.pi / 2), CY + R_RING * math.sin(2 * math.pi * a / n - math.pi / 2))
               for a in range(int(n * p) + 1)]
        c.line(arc, PARCH, 1.4)
    adm = rej = 0
    for k in range(NP_):
        r, st, hit = particle(k, g)
        if r is None:
            continue
        a = P_ANG[k]
        ca, sa = math.cos(a), math.sin(a)
        col = GOLD if P_OK[k] else COPPER
        x, y = CX + r * ca, CY + r * sa
        if st in ("in", "out"):
            r2, _, _ = particle(k, g - 1.6)
            if r2 is not None:
                c.line([(x, y), (CX + r2 * ca, CY + r2 * sa)], col, 1.2)
        c.circle(x, y, 3.2, fill=col)
        if st == "rest":
            adm += 1
        if hit is not None and g >= hit:
            rej += 1
            hx, hy = CX + (R_RING + 14) * ca, CY + (R_RING + 14) * sa
            c.line([(hx - 6, hy - 6), (hx + 6, hy + 6)], COPPER, 1.4)
            c.line([(hx - 6, hy + 6), (hx + 6, hy - 6)], COPPER, 1.4)
    c.text(W - 120, 300, f"ADMITTED  {adm:03d}", MONO_MED, 20, GOLD, anchor="rs", track=2)
    c.text(W - 120, 336, f"REJECTED  {rej:03d}", MONO_MED, 20, COPPER, anchor="rs", track=2)
    c.text(W - 120, 372, "NO RECEIPT, NO ENTRY", MONO, 13, MID, anchor="rs", track=2)


def ev_refusal():
    ev = [(282 / FPS, "draw")]
    for k in range(NP_):
        if P_OK[k]:
            t = P_SPAWN[k] + (P_R0 - P_REST[k]) / P_V
            if t < 54:
                ev.append(((282 + t) / FPS, "admit"))
        else:
            t = P_SPAWN[k] + (P_R0 - R_RING - 6) / P_V
            if t < 54:
                ev.append(((282 + t) / FPS, "reject"))
    return ev


# ------------------------------------------------------------------ 06 TIME (recap)

PW, PH = 540, 304
MINI_FRAMES = [(s_type, 36, (92, 100)), (s_rule, 102, (140, 160)), (s_field, 168, (200, 220)),
               (s_grid, 228, (250, 276)), (s_refusal, 282, (316, 330))]


@lru_cache(maxsize=None)
def mini(i, which):
    fn, _, frames = MINI_FRAMES[i]
    c = Canvas()
    fn(c, frames[which])
    point(c)
    return c.out().resize((PW * SS, PH * SS), Image.LANCZOS)


def s_time(c, f):
    g = f - 336
    k = 1 - ei(seg(g, 30, 44))
    gx = [CX - PW - 24, CX, CX + PW + 24]
    gy = [CY - PH / 2 - 12, CY + PH / 2 + 12]
    for i in range(6):
        if g < 2 * i or k <= 0.02:
            continue
        pcx, pcy = gx[i % 3], gy[i // 3]
        cx, cy = CX + (pcx - CX) * k, CY + (pcy - CY) * k
        w, h = PW * k, PH * k
        x0, y0 = cx - w / 2, cy - h / 2
        if i < 5:
            im = mini(i, (g // 2) % 2)  # stepped on twos
            if k < 1:
                im = im.resize((max(2, int(w * SS)), max(2, int(h * SS))), Image.BILINEAR)
            c.im.paste(im, (int(x0 * SS), int(y0 * SS)))
        else:
            c.rect(x0, y0, x0 + w, y0 + h, fill=INK)
            if k > 0.5:
                c.text(cx, cy + 40 * k, f"{f:04d}", MONO_MED, 120 * k, GOLD, anchor="ms", track=4 * k)
        c.rect(x0, y0, x0 + w, y0 + h, outline=MID, w=1)
        if k > 0.9:
            c.text(x0 + 14, y0 + 26, f"{i + 1:02d} — {NAMES[i]}", MONO_MED, 12, GOLD if i == 5 else PARCH, track=1.5)


def ev_time():
    return [((336 + 2 * i) / FPS, "click") for i in range(6)] + [(366 / FPS, "riser")]


# ------------------------------------------------------------------ LOCKUP

def s_lockup(c, f):
    g = f - 399
    word, size, track = "HELEN", 210, 46
    tot = c.width(word, DISPLAY, size, track)
    x = CX - tot / 2
    for i, ch in enumerate(word):
        t0 = 3 + 2 * i
        if g >= t0:
            dy = 14 * (1 - eo((g - t0) / 4))
            c.text(x, CY - 52 + dy, ch, DISPLAY, size, PARCH)
        x += c.width(ch, DISPLAY, size) + track
    p = eo(seg(g, 13, 21))
    if p > 0:
        e = 430 * p
        c.line([(CX - e, CY), (CX - 22, CY)], GOLD, 1.2)
        c.line([(CX + 22, CY), (CX + e, CY)], GOLD, 1.2)
    words = "every frame is a rule you can read".split()
    nw = int(clamp((g - 18) / 1.5, 0, len(words)))
    if nw:
        full = " ".join(words)
        tw = c.width(full, DISPLAY_IT, 40)
        c.text(CX - tw / 2, CY + 74, " ".join(words[:nw]), DISPLAY_IT, 40, PARCH)
    if g >= 26:
        c.text(CX, CY + 128, "TYPE  ·  RULE  ·  FIELD  ·  GRID  ·  REFUSAL  ·  TIME", MONO, 13, MID, anchor="ms", track=2)
    rec = (f"RENDER RECEIPT   showreel.py sha256 {SCRIPT_SHA[:12]}…{SCRIPT_SHA[-4:]}   ·   {N} frames @ {FPS} fps"
           f"   ·   {N / FPS:.1f} s   ·   0 credits   ·   authority = false")
    nch = int(clamp((g - 28) * 7, 0, len(rec)))
    if nch:
        full = c.width(rec, MONO, 12, 0.5)
        c.text(CX - full / 2, H - 92, rec[:nch], MONO, 12, GOLD, track=0.5)
    c.text(W - 48, 52, f"F {f:04d} / {N:04d}", MONO, 13, MID, anchor="rs", track=1.5)


def ev_lockup():
    return [((399 + 3 + 2 * i) / FPS, f"note{i}") for i in range(5)] + [(412 / FPS, "draw")] + \
           [((399 + 28 + k) / FPS, "tick") for k in range(0, 18, 3)]


# ------------------------------------------------------------------ frame and sound

DRAW = {"OPEN": s_open, "TYPE": s_type, "RULE": s_rule, "FIELD": s_field, "GRID": s_grid, "REFUSAL": s_refusal,
        "TIME": s_time, "LOCKUP": s_lockup}


def scene_of(f):
    for i, (name, a, b) in enumerate(SCENES):
        if a <= f < b:
            return i, name
    raise ValueError(f)


def render_frame(f):
    i, name = scene_of(f)
    c = Canvas()
    if name != "BLACK":
        DRAW[name](c, f)
        if name not in ("LOCKUP",):
            hud(c, f, i, name)
        if not (name == "OPEN" and f < 3):
            point(c)
    return c.out()


def _work(args):
    f, out = args
    render_frame(f).save(out / f"f{f:04d}.png", optimize=False, compress_level=1)
    return f


SR = 48000


def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def synth(kind, rng):
    if kind == "click":
        n = int(0.03 * SR)
        return (rng.normal(0, 1, n) * 0.35 + np.sin(2 * np.pi * 2400 * np.arange(n) / SR) * 0.5) * env(n, 0.0005, 0.006)
    if kind == "tick":
        n = int(0.02 * SR)
        return np.sin(2 * np.pi * 3600 * np.arange(n) / SR) * env(n, 0.0003, 0.004) * 0.45
    if kind == "pen":
        n = int(0.05 * SR)
        return rng.normal(0, 1, n) * env(n, 0.001, 0.01) * 0.12
    if kind == "hit":
        n = int(0.35 * SR)
        t = np.arange(n) / SR
        return (np.sin(2 * np.pi * (70 + 60 * np.exp(-t * 30)) * t) * env(n, 0.001, 0.09) * 0.9
                + rng.normal(0, 1, n) * env(n, 0.0005, 0.008) * 0.3)
    if kind == "draw":
        n = int(0.45 * SR)
        t = np.arange(n) / SR
        return rng.normal(0, 1, n) * np.sin(np.pi * t / t[-1]) ** 2 * 0.06 + np.sin(2 * np.pi * 1200 * t) * env(n, 0.002, 0.05) * 0.08
    if kind == "admit":
        n = int(0.12 * SR)
        t = np.arange(n) / SR
        fr = 880 * 2 ** (rng.integers(0, 3) * 7 / 12)
        return np.sin(2 * np.pi * fr * t) * env(n, 0.002, 0.03) * 0.16
    if kind == "reject":
        n = int(0.3 * SR)
        t = np.arange(n) / SR
        return (np.sin(2 * np.pi * 55 * t) * env(n, 0.001, 0.07) * 0.8 + rng.normal(0, 1, n) * env(n, 0.0005, 0.012) * 0.35)
    if kind == "whoosh":
        n = int(0.4 * SR)
        t = np.arange(n) / SR
        noise = np.convolve(rng.normal(0, 1, n), np.ones(24) / 24, "same")
        return noise * np.sin(np.pi * t / t[-1]) ** 3 * 0.9
    if kind in ("riser", "riser_s"):
        dur = 0.8 if kind == "riser" else 1.0
        n = int(dur * SR)
        t = np.arange(n) / SR
        noise = np.convolve(rng.normal(0, 1, n), np.ones(8) / 8, "same")
        return (noise * 0.25 + np.sin(2 * np.pi * (200 + 600 * t / dur) * t) * 0.15) * (t / dur) ** 2 * (0.9 if kind == "riser" else 0.4)
    if kind.startswith("note"):
        i = int(kind[4:])
        fr = 220 * 2 ** ([0, 3, 7, 10, 12][i] / 12)
        n = int(1.6 * SR)
        t = np.arange(n) / SR
        return (np.sin(2 * np.pi * fr * t) + 0.3 * np.sin(4 * np.pi * fr * t)) * env(n, 0.004, 0.5) * 0.22
    raise KeyError(kind)


def events():
    return sorted(ev_open() + ev_type() + ev_rule() + ev_field() + ev_grid() + ev_refusal() + ev_time() + ev_lockup())


def soundtrack(path):
    rng = np.random.default_rng(2001)
    n = int(N / FPS * SR)
    L, R = np.zeros(n), np.zeros(n)
    t = np.arange(n) / SR
    cut = int(390 / FPS * SR)  # drone cut dead at the black
    drone = sum(a * np.sin(2 * np.pi * fr * t + ph) for a, fr, ph in ((0.10, 55, 0), (0.06, 110.4, 1), (0.04, 164.3, 2), (0.025, 220.9, 3)))
    drone *= np.minimum(1, t / 0.6)
    drone[cut:] = 0
    L += drone
    R += np.roll(drone, 40)
    for k, (ts, kind) in enumerate(events()):
        s = synth(kind, rng)
        i0 = int(ts * SR)
        if i0 >= n:
            continue
        s = s[: n - i0]
        if kind not in ("riser", "riser_s") or i0 + len(s) <= cut:
            pan = 0.5 + 0.35 * math.sin(k * 2.399)
        else:
            pan = 0.5
        if kind in ("riser", "riser_s"):
            s = s[: max(0, cut - i0)] if i0 < cut else s
        L[i0:i0 + len(s)] += s * (1 - pan) * 2 * 0.7
        R[i0:i0 + len(s)] += s * pan * 2 * 0.7
    peak = max(np.abs(L).max(), np.abs(R).max())
    stereo = np.stack([L, R], 1) / peak * 0.85
    pcm = (stereo * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", type=int, nargs="*", help="render only these frames (for checking)")
    args = ap.parse_args(argv)
    FONTS["dir"] = pathlib.Path(args.fonts)
    out = pathlib.Path(args.out)
    (out / "frames").mkdir(parents=True, exist_ok=True)
    frames = args.only if args.only else list(range(N))
    with Pool(args.workers, initializer=FONTS.__setitem__, initargs=("dir", pathlib.Path(args.fonts))) as pool:
        for _ in pool.imap_unordered(_work, [(f, out / "frames") for f in frames], chunksize=4):
            pass
    if not args.only:
        soundtrack(out / "audio.wav")
        fonts = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16] for p in sorted(FONTS["dir"].glob("*.ttf"))}
        (out / "render.json").write_text(json.dumps({
            "film": "HELEN motion showreel", "status": "NON_SOVEREIGN", "authority": False, "credits": 0,
            "script_sha256": SCRIPT_SHA, "frames": N, "fps": FPS, "size": [W, H], "supersample": SS,
            "scenes": SCENES, "fonts_sha256_16": fonts, "events": len(events()),
            "generated_media": "none: every pixel and sample computed by showreel.py"}, indent=1))
    print(f"rendered {len(frames)} frames into {out / 'frames'}")


if __name__ == "__main__":
    main()
