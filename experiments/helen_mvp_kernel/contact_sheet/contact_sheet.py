#!/usr/bin/env python3
"""Contact sheet + measurements for choosing a master image. NON_SOVEREIGN · authority=false. No AI.

    python contact_sheet.py <folder> [--out <dir>] [--roi roi.json] [--min-short-side 1080] [--fps 1]

For every image in <folder> (jpg, jpeg, png, tif, webp): file size, sha256, width x height, megapixels,
estimated JPEG quality, progressive flag, EXIF date/camera/software, sharpness (variance of the Laplacian)
for the whole image and for the sharpest tile of an 8x8 grid, and near-duplicates (perceptual hash).
Optional roi.json {"file.jpg": [x, y, w, h]} gives the nail region: its size in pixels and its own
sharpness are then reported, which is what decides whether the nail is usable in macro.
Videos (mov, mp4, m4v) are probed with ffprobe and sampled with ffmpeg at --fps; each still is matched
to its nearest sampled frame, to check whether the stills come from those videos.

Outputs in --out: contact_sheet.jpg (numbered thumbnails, sharpest tile in yellow, ROI in green),
report.md and report.json, with up to 3 candidates. Sharpness depends on resolution and content:
compare images of the same kind, and confirm by eye at 100 %.
"""
import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageOps

IMG_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
VID_EXT = {".mov", ".mp4", ".m4v"}
# libjpeg standard luminance table (ITU T.81 Annex K), used to estimate the encoder quality.
STD_LUMA = np.array([16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55, 14, 13, 16, 24, 40, 57, 69, 56,
                     14, 17, 22, 29, 51, 87, 80, 62, 18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92,
                     49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99])
EXIF_TAGS = {306: "datetime", 271: "make", 272: "model", 305: "software", 36867: "datetime_original"}


def jpeg_quality(img):
    """Estimated libjpeg quality (1-100) from the luminance quantization table, or None."""
    q = getattr(img, "quantization", None)
    if not q or 0 not in q:
        return None
    table = np.sort(np.array(q[0][:64]))  # order-independent comparison (zigzag vs natural order)
    best, best_err = None, None
    for quality in range(1, 101):
        scale = 5000 / quality if quality < 50 else 200 - 2 * quality
        ref = np.sort(np.clip((STD_LUMA * scale + 50) // 100, 1, 255))
        err = np.abs(ref - table).sum()
        if best_err is None or err < best_err:
            best, best_err = quality, err
    return best


def denoise(gray):
    """3x3 binomial blur: damps sensor grain and JPEG noise, which would otherwise inflate the Laplacian."""
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        return gray
    p = np.pad(gray, 1, mode="edge")
    k = (1.0, 2.0, 1.0)
    rows = sum(k[i] * p[i:i + gray.shape[0], :] for i in range(3)) / 4.0
    return sum(k[j] * rows[:, j:j + gray.shape[1]] for j in range(3)) / 4.0


def laplacian_var(gray):
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        return 0.0
    gray = denoise(gray)
    lap = (gray[:-2, 1:-1] + gray[2:, 1:-1] + gray[1:-1, :-2] + gray[1:-1, 2:] - 4 * gray[1:-1, 1:-1])
    return float(lap.var())


def sharpest_tile(gray, grid=8):
    h, w = gray.shape
    best = (0.0, (0, 0, w, h))
    for i in range(grid):
        for j in range(grid):
            y0, y1 = h * i // grid, h * (i + 1) // grid
            x0, x1 = w * j // grid, w * (j + 1) // grid
            v = laplacian_var(gray[y0:y1, x0:x1])
            if v > best[0]:
                best = (v, (x0, y0, x1 - x0, y1 - y0))
    return best


def ahash(img, size=8):
    small = np.asarray(ImageOps.grayscale(img).resize((size, size), Image.Resampling.BILINEAR), dtype=np.float64)
    return int("".join("1" if v else "0" for v in (small > small.mean()).flatten()), 2)


COLOUR_NEAR = 12  # max mean |RGB| difference of the worst 16x16 cell for a near-duplicate (0..255)


def colour_grid(img, size=16):
    return np.asarray(img.convert("RGB").resize((size, size), Image.Resampling.BOX), dtype=np.int16)


def colour_distance(a, b):
    """Worst-cell colour difference. aHash sees luminance only: the same nail framing in two shades
    hashes alike, so a near-duplicate must also match in local colour (or shade variants get merged)."""
    return float(np.abs(a - b).mean(axis=2).max())


def hamming(a, b):
    return bin(a ^ b).count("1")


def measure(path, roi=None):
    raw = path.read_bytes()
    with Image.open(path) as im:
        info = {"file": path.name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()[:12],
                "format": im.format, "mode": im.mode, "width": im.width, "height": im.height,
                "megapixels": round(im.width * im.height / 1e6, 2), "jpeg_quality_est": jpeg_quality(im),
                "progressive": bool(im.info.get("progressive") or im.info.get("progression"))}
        exif = im.getexif() if hasattr(im, "getexif") else {}
        info["exif"] = {name: str(exif.get(tag)) for tag, name in EXIF_TAGS.items() if exif.get(tag)}
        rgb = ImageOps.exif_transpose(im).convert("RGB")
    gray = np.asarray(rgb.convert("L"), dtype=np.float64)
    info["sharpness_global"] = round(laplacian_var(gray), 1)
    tv, tile = sharpest_tile(gray)
    info["sharpness_best_tile"], info["best_tile_xywh"] = round(tv, 1), list(tile)
    if roi:
        x, y, w, h = roi
        info["roi_xywh"] = [x, y, w, h]
        info["roi_short_side_px"] = min(w, h)
        info["sharpness_roi"] = round(laplacian_var(gray[y:y + h, x:x + w]), 1)
    info["_ahash"] = ahash(rgb)
    info["_colour"] = colour_grid(rgb)
    return info, rgb


def probe_video(path):
    if not shutil.which("ffprobe"):
        return {"file": path.name, "error": "ffprobe not installed"}
    p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,codec_name,r_frame_rate,pix_fmt:format=duration,size",
                        "-of", "json", str(path)], capture_output=True, text=True)
    if p.returncode != 0:
        return {"file": path.name, "error": p.stderr.strip()[-200:]}
    d = json.loads(p.stdout)
    s = (d.get("streams") or [{}])[0]
    return {"file": path.name, "width": s.get("width"), "height": s.get("height"), "codec": s.get("codec_name"),
            "fps": s.get("r_frame_rate"), "pix_fmt": s.get("pix_fmt"),
            "duration_s": round(float(d.get("format", {}).get("duration", 0) or 0), 2),
            "bytes": int(d.get("format", {}).get("size", 0) or 0)}


def sample_frames(path, out_dir, fps):
    if not shutil.which("ffmpeg"):
        return []
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = out_dir / f"{path.stem}_%05d.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-vf", f"fps={fps}", str(pattern)],
                   capture_output=True)
    return sorted(out_dir.glob(f"{path.stem}_*.png"))


def contact_sheet(items, out_path, thumb=360, cols=4):
    rows = (len(items) + cols - 1) // cols
    label_h = 46
    sheet = Image.new("RGB", (cols * thumb, rows * (thumb + label_h)), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    for n, (info, rgb) in enumerate(items):
        scale = thumb / max(rgb.width, rgb.height)
        t = rgb.resize((max(1, int(rgb.width * scale)), max(1, int(rgb.height * scale))))
        x0, y0 = (n % cols) * thumb, (n // cols) * (thumb + label_h)
        ox, oy = x0 + (thumb - t.width) // 2, y0 + (thumb - t.height) // 2
        sheet.paste(t, (ox, oy))
        for key, color in (("best_tile_xywh", (255, 210, 0)), ("roi_xywh", (0, 220, 120))):
            if key in info:
                x, y, w, h = info[key]
                draw.rectangle([ox + x * scale, oy + y * scale, ox + (x + w) * scale, oy + (y + h) * scale],
                               outline=color, width=2)
        q = info.get("jpeg_quality_est")
        draw.text((x0 + 6, y0 + thumb + 4), f"#{n + 1} {info['file'][:44]}", fill=(235, 235, 235))
        draw.text((x0 + 6, y0 + thumb + 22),
                  f"{info['width']}x{info['height']}  q~{q if q else '-'}  sharp {info.get('sharpness_roi', info['sharpness_best_tile'])}",
                  fill=(180, 180, 180))
    sheet.save(out_path, quality=90)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("--out", default="contact_sheet_out")
    ap.add_argument("--roi", help='JSON {"file.jpg": [x, y, w, h]} marking the nail in each image')
    ap.add_argument("--min-short-side", type=int, default=1080, help="resolution gate for a master image (px)")
    ap.add_argument("--min-roi-short-side", type=int, default=400, help="nail size gate when a ROI is given (px)")
    ap.add_argument("--fps", type=float, default=1.0, help="frames per second sampled from videos")
    args = ap.parse_args(argv)

    src, out = pathlib.Path(args.folder), pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rois = json.loads(pathlib.Path(args.roi).read_text()) if args.roi else {}
    files = sorted(p for p in src.iterdir() if p.is_file())
    images = [measure(p, rois.get(p.name)) for p in files if p.suffix.lower() in IMG_EXT]
    videos = [p for p in files if p.suffix.lower() in VID_EXT]

    # near-duplicates among images
    for a in range(len(images)):
        for b in range(a + 1, len(images)):
            ia, ib = images[a][0], images[b][0]
            exact = ia["sha256"] == ib["sha256"]
            near = hamming(ia["_ahash"], ib["_ahash"]) <= 3 and colour_distance(ia["_colour"], ib["_colour"]) <= COLOUR_NEAR
            if exact or near:
                ia.setdefault("duplicates", []).append(ib["file"])
                ib.setdefault("duplicates", []).append(ia["file"])

    # videos: probe, sample, match each still to its nearest frame
    video_info, frames = [], []
    for v in videos:
        video_info.append(probe_video(v))
        for f in sample_frames(v, out / "frames", args.fps):
            with Image.open(f) as fr:
                frames.append((f.name, ahash(fr.convert("RGB"))))
    for info, _ in images:
        if frames:
            name, h = min(frames, key=lambda fh: hamming(fh[1], info["_ahash"]))
            info["nearest_video_frame"] = {"frame": name, "ahash_distance": hamming(h, info["_ahash"])}

    # gates for every image; candidates ranked by nail sharpness (ROI) else best tile, one per duplicate group
    for info, _ in images:
        gate_res = min(info["width"], info["height"]) >= args.min_short_side
        gate_roi = info.get("roi_short_side_px", args.min_roi_short_side) >= args.min_roi_short_side
        info["passes_gates"] = bool(gate_res and gate_roi)
    seen, ranked = set(), []
    for info, _ in sorted(images, key=lambda ir: -(ir[0].get("sharpness_roi") or ir[0]["sharpness_best_tile"])):
        kept = next((d for d in info.get("duplicates", []) if d in seen), None)
        if kept:
            info["duplicate_of_ranked"] = kept
            continue
        seen.add(info["file"])
        ranked.append(info)
    top = max([(i.get("sharpness_roi") or i["sharpness_best_tile"]) for i in ranked] or [0])
    for i in ranked:  # far blurrier than the best image: not a candidate, whatever its resolution
        i["sharp_enough"] = (i.get("sharpness_roi") or i["sharpness_best_tile"]) >= 0.25 * top
    candidates = [i["file"] for i in ranked if i["passes_gates"] and i["sharp_enough"]][:3]
    verdict = ("candidates found" if candidates else
               "no image passes the resolution gates: ask for HD originals (or lower the gates after looking at 100 %)")

    contact_sheet(images, out / "contact_sheet.jpg")
    clean = [{k: v for k, v in i.items() if not k.startswith("_")} for i, _ in images]
    report = {"folder": str(src), "gates": {"min_short_side": args.min_short_side,
              "min_roi_short_side": args.min_roi_short_side if rois else None},
              "images": clean, "videos": video_info, "candidates": candidates, "verdict": verdict,
              "roi_given": bool(rois)}
    (out / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    lines = [f"# Contact sheet report — {src.name}", "",
             f"Gates: short side ≥ {args.min_short_side}px" + (f", nail ROI short side ≥ {args.min_roi_short_side}px" if rois else
                                                               " (no nail ROI given: sharpness is the sharpest tile, a proxy only)"), "",
             "| # | File | W×H | MP | Size | JPEG q~ | Sharp (best tile / ROI) | Duplicates | Nearest video frame |",
             "|---|---|---|---|---|---|---|---|---|"]
    for n, i in enumerate(clean, 1):
        nv = i.get("nearest_video_frame")
        nv_txt = f"{nv['frame']} (d={nv['ahash_distance']})" if nv else "-"
        lines.append(f"| {n} | {i['file']} | {i['width']}×{i['height']} | {i['megapixels']} | {i['bytes'] // 1024} KB | "
                     f"{i['jpeg_quality_est'] or '-'} | {i['sharpness_best_tile']} / {i.get('sharpness_roi', '-')} | "
                     f"{', '.join(i.get('duplicates', [])) or '-'} | {nv_txt} |")
    if video_info:
        lines += ["", "| Video | W×H | Codec | fps | Duration | Size |", "|---|---|---|---|---|---|"]
        lines += [f"| {v['file']} | {v.get('width')}×{v.get('height')} | {v.get('codec')} | {v.get('fps')} | "
                  f"{v.get('duration_s')} s | {v.get('bytes', 0) // 1_000_000} MB |" if "error" not in v else f"| {v['file']} | error: {v['error']} | | | | |"
                  for v in video_info]
    lines += ["", f"**Candidates (max 3):** {', '.join(candidates) or 'none'}", f"**Verdict:** {verdict}", "",
              "Read the sheet at 100 % before choosing: sharpness numbers rank, they do not decide. "
              "A nearest-frame distance ≤ 5 suggests the still comes from that video; confirm visually."]
    (out / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return report


if __name__ == "__main__":
    main()
