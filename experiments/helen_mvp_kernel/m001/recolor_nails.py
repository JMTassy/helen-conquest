#!/usr/bin/env python3
"""M001-A · COLOR CONSTANCY baseline: change ONLY the nail colour of one master image. No AI, no credits.

    python recolor_nails.py I0006.jpg --boxes boxes.json \\
        --target "coral_approx=#E2483B" --target "pistachio_approx=#C8D8A0" --out m001a_I0006

boxes.json: list of nail boxes [x, y, w, h] in image pixels (one per visible nail), or --mask mask.png
(white = nail) painted by a person. Inside each box the nail is separated from skin automatically
(Otsu split on L*, --nail lighter|darker, largest connected region), unless a mask is given.

Recolouring in CIELAB: target hue/chroma replace the nail's, the nail's own lightness variations
(shading, texture) are kept around the target lightness, and specular highlights stay bright and
nearly neutral. Mask edges are feathered (1-2 px). Outputs are PNG (lossless) so that every pixel
outside the feathered mask is bit-identical to the source; any later JPEG export breaks that.

Per variant the report measures: pixels changed, changes outside the mask (must be 0), mean ΔE76 to
the target colour in the nail core, and texture kept (correlation of L* before/after in the nail).
Limits: opaque shades only. A translucent shade (Active Glow) depends on skin and coats and is not
simulated. Target colours are parameters, not product references: product fidelity is NOT evaluated.
"""
import argparse
import hashlib
import json
import pathlib

import numpy as np
from PIL import Image, ImageDraw

# ------------------------------------------------------------------ colour maths (sRGB D65 <-> CIELAB)

_M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
_WHITE = np.array([0.95047, 1.0, 1.08883])


def srgb_to_lab(rgb):
    c = rgb.astype(np.float64) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    xyz = lin @ _M.T / _WHITE
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], axis=-1)


def lab_to_srgb(lab):
    fy = (lab[..., 0] + 16) / 116
    fx, fz = fy + lab[..., 1] / 500, fy - lab[..., 2] / 200
    f = np.stack([fx, fy, fz], axis=-1)
    xyz = np.where(f > 6 / 29, f ** 3, 3 * (6 / 29) ** 2 * (f - 4 / 29)) * _WHITE
    lin = np.clip(xyz @ np.linalg.inv(_M).T, 0, 1)
    c = np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * lin ** (1 / 2.4) - 0.055)
    return np.clip(np.round(c * 255), 0, 255).astype(np.uint8)


def hex_to_lab(h):
    h = h.lstrip("#")
    return srgb_to_lab(np.array([[[int(h[i:i + 2], 16) for i in (0, 2, 4)]]], dtype=np.uint8))[0, 0]


# ------------------------------------------------------------------ mask

def otsu(values):
    hist, edges = np.histogram(values, bins=128)
    p = hist / max(hist.sum(), 1)
    centers = (edges[:-1] + edges[1:]) / 2
    w0, mu0 = np.cumsum(p), np.cumsum(p * centers)
    mu_t = mu0[-1]
    with np.errstate(divide="ignore", invalid="ignore"):
        between = (mu_t * w0 - mu0) ** 2 / (w0 * (1 - w0))
    return centers[int(np.nanargmax(between))]


def largest_component(binary):
    """4-connected labelling, keeps the largest region (boxes are small: plain BFS is fine)."""
    h, w = binary.shape
    seen = np.zeros_like(binary, dtype=bool)
    best = []
    for y0, x0 in zip(*np.nonzero(binary)):
        if seen[y0, x0]:
            continue
        stack, comp = [(y0, x0)], []
        seen[y0, x0] = True
        while stack:
            y, x = stack.pop()
            comp.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and binary[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        if len(comp) > len(best):
            best = comp
    out = np.zeros_like(binary, dtype=bool)
    if best:
        ys, xs = zip(*best)
        out[list(ys), list(xs)] = True
    return out


def fill_holes(mask):
    """Fill enclosed holes (e.g. a highlight Otsu put on the wrong side) by flooding the background from the border."""
    h, w = mask.shape
    outside = np.zeros_like(mask)
    stack = [(y, x) for y in range(h) for x in (0, w - 1) if not mask[y, x]] + \
            [(y, x) for x in range(w) for y in (0, h - 1) if not mask[y, x]]
    for y, x in stack:
        outside[y, x] = True
    while stack:
        y, x = stack.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not mask[ny, nx] and not outside[ny, nx]:
                outside[ny, nx] = True
                stack.append((ny, nx))
    return ~outside


def auto_mask(lab, boxes, polarity):
    mask = np.zeros(lab.shape[:2], dtype=bool)
    H, W = mask.shape
    for box in boxes:
        x, y, w, h = (int(round(v)) for v in box)
        x, y = max(x, 0), max(y, 0)
        w, h = min(w, W - x), min(h, H - y)
        if w < 3 or h < 3:
            raise ValueError(f"nail box {box} is outside the image or too small")
        L = lab[y:y + h, x:x + w, 0]
        t = otsu(L.ravel())
        sel = L > t if polarity == "lighter" else L < t
        mask[y:y + h, x:x + w] |= fill_holes(largest_component(sel))
    return mask


def _dilate(mask):
    p = np.pad(mask, 1)
    return p[1:-1, 1:-1] | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]


def feather(mask, radius=1):
    """Soft alpha: 1 on the mask, then rings of 1 - k/(radius+1) for k = 1..radius px outside, 0 beyond."""
    a = mask.astype(np.float64)
    grown = mask.copy()
    for k in range(1, radius + 1):
        ring = _dilate(grown) & ~grown
        a[ring] = 1 - k / (radius + 1)
        grown |= ring
    return a


# ------------------------------------------------------------------ recolour

def recolour(rgb, mask, target_lab, highlight_pct=97.0, texture_gain=1.0, feather_px=1):
    if not mask.any():
        raise ValueError("empty nail mask: check the boxes / --nail polarity / painted mask")
    lab = srgb_to_lab(rgb)
    alpha = feather(mask, feather_px)
    zone = alpha > 0                                              # mask + feather ring get the new colour
    L = lab[..., 0]
    L_mean = L[mask].mean()
    hi_thr = np.percentile(L[mask], highlight_pct)
    span = max(100 - hi_thr, 1e-6)
    w_hi = np.clip((L - hi_thr) / span, 0, 1)                    # 0 = body of the nail, 1 = strongest highlight
    new = lab.copy()
    new_L = target_lab[0] + (L - L_mean) * texture_gain
    new[..., 0] = np.where(zone, (1 - w_hi) * new_L + w_hi * L, L)  # highlights keep their own (bright) lightness
    for k in (1, 2):
        new[..., k] = np.where(zone, (1 - w_hi) * target_lab[k] + w_hi * lab[..., k] * 0.3, lab[..., k])
    a3 = alpha[..., None]
    out = np.round(a3 * lab_to_srgb(new).astype(np.float64) + (1 - a3) * rgb.astype(np.float64)).astype(np.uint8)
    out[~zone] = rgb[~zone]                                       # bit-identical outside the soft mask
    return out, alpha


def measure(src, out, mask, alpha, target_lab):
    diff = np.abs(out.astype(np.int16) - src.astype(np.int16)).max(axis=2)
    outside = alpha == 0
    core = mask.copy()
    p = np.pad(core, 1)                                           # erode once: ignore the edge for colour
    core = core & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    lab_src, lab_out = srgb_to_lab(src), srgb_to_lab(out)
    body = core & (lab_src[..., 0] < np.percentile(lab_src[..., 0][mask], 97)) if core.any() else core
    de = np.sqrt(((lab_out[body] - target_lab) ** 2).sum(axis=1)) if body.any() else np.array([np.nan])
    corr = float(np.corrcoef(lab_src[..., 0][core], lab_out[..., 0][core])[0, 1]) if core.sum() > 2 else float("nan")
    return {"pixels_changed": int((diff > 0).sum()), "pixels_changed_outside_mask": int((diff[outside] > 0).sum()),
            "max_change_outside_mask": int(diff[outside].max()) if outside.any() else 0,
            "mask_pixels": int(mask.sum()), "mean_dE76_to_target_nail_body": round(float(np.nanmean(de)), 2),
            "texture_kept_corr_L": round(corr, 4)}


def sheet(images, labels, path, width=360):
    thumbs = [im.resize((width, int(im.height * width / im.width))) for im in images]
    h = max(t.height for t in thumbs) + 28
    s = Image.new("RGB", (width * len(thumbs), h), (24, 24, 24))
    d = ImageDraw.Draw(s)
    for i, (t, lab) in enumerate(zip(thumbs, labels)):
        s.paste(t, (i * width, 0))
        d.text((i * width + 6, h - 22), lab, fill=(235, 235, 235))
    s.save(path)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--boxes", help="JSON list of nail boxes [x, y, w, h]")
    g.add_argument("--mask", help="PNG mask, white = nail")
    ap.add_argument("--target", action="append", required=True, help='name=#RRGGBB (opaque shade, approximate unless sourced)')
    ap.add_argument("--nail", choices=["lighter", "darker"], default="lighter", help="nail vs skin inside each box")
    ap.add_argument("--out", default="m001a_out")
    ap.add_argument("--feather", type=int, default=1)
    args = ap.parse_args(argv)

    src_path, out = pathlib.Path(args.image), pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    src = np.asarray(Image.open(src_path).convert("RGB"))
    if args.mask:
        mask = np.asarray(Image.open(args.mask).convert("L")) > 127
    else:
        mask = auto_mask(srgb_to_lab(src), json.loads(pathlib.Path(args.boxes).read_text()), args.nail)
    Image.fromarray((mask * 255).astype(np.uint8)).save(out / "mask.png")
    Image.fromarray(src).save(out / "00_original.png")
    report = {"source": src_path.name, "source_sha256": hashlib.sha256(src_path.read_bytes()).hexdigest()[:16],
              "size": [int(src.shape[1]), int(src.shape[0])], "method": "deterministic CIELAB recolour, no AI, no credits",
              "mask_source": "painted" if args.mask else f"auto in boxes (nail {args.nail})",
              "limits": ["opaque shades only; translucent shades not simulated",
                         "target colours are parameters, not product references: product fidelity not evaluated",
                         "invariance holds for the PNG outputs; JPEG export changes every pixel slightly"],
              "variants": []}
    images, labels = [Image.fromarray(src)], ["original"]
    for i, t in enumerate(args.target, 1):
        name, hexv = t.split("=", 1)
        tl = hex_to_lab(hexv)
        res, alpha = recolour(src, mask, tl, feather_px=args.feather)
        f = out / f"{i:02d}_{name}.png"
        Image.fromarray(res).save(f)
        diffmap = (np.abs(res.astype(np.int16) - src.astype(np.int16)).max(axis=2) > 0).astype(np.uint8) * 255
        Image.fromarray(diffmap).save(out / f"{i:02d}_{name}_diff.png")
        m = measure(src, res, mask, alpha, tl)
        report["variants"].append({"name": name, "target_hex": hexv, "file": f.name, **m})
        images += [Image.fromarray(res), Image.fromarray(diffmap).convert("RGB")]
        labels += [name, f"{name}: changed pixels"]
    sheet(images, labels, out / "m001a_sheet.png")
    (out / "report.json").write_text(json.dumps(report, indent=1))
    for v in report["variants"]:
        ok = v["pixels_changed_outside_mask"] == 0
        print(f"{v['name']}: {v['pixels_changed']} px changed, outside mask {v['pixels_changed_outside_mask']} "
              f"({'OK' if ok else 'FAIL'}), dE76 to target {v['mean_dE76_to_target_nail_body']}, texture corr {v['texture_kept_corr_L']}")
    return report


if __name__ == "__main__":
    main()
