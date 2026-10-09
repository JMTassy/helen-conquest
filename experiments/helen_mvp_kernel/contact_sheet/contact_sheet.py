#!/usr/bin/env python3
"""Contact sheet + measurements to pre-select a master image. NON_SOVEREIGN · authority=false. No AI.

Working version for HELEN M001, consolidated from three parallel implementations (this repo, the operator's
local tools/contact_sheet.py, and the ChatGPT prototype zip kept as a separate reference).

    python contact_sheet.py <folder> [--out DIR] [--metadata metadata.json] [--require-nail]
                            [--min-short-side 1080] [--min-roi-short-side 400] [--fps 1]

metadata.json (optional), per file name, either a nail box [x, y, w, h] or an object:
    {"still_01.jpg": {"nail_roi": [x, y, w, h], "source": "e-mail Gaël 2025-05-18", "notes": "..."}}

Per image: pixel dimensions, file size, bytes per pixel, compression index (estimated JPEG quality),
EXIF, RMS contrast, blown highlights and deep shadows (reported for the whole image; blown highlights are
penalised only inside the nail box, since white or black backgrounds are legitimate), sharpness
(variance of the Laplacian after a 3x3 denoise) for the whole image, a 6x6 focus map and the nail box.
Without a nail box, nail sharpness is "not evaluated". Unreadable files are listed, never dropped silently.

Duplicates: exact file (sha256) or exact pixels (decoded RGB + size, so different metadata does not hide a
copy) are excluded, one copy kept. Visual resemblance (luminance hash AND local colour) is flagged for
inspection, never excluded. Videos are probed and sampled; each image gets its nearest sampled frame with
video, timestamp and distance: a candidate visual match, not proof of provenance.

Conclusions this tool can support (and no more): candidates "according to these criteria"; the 25 %
relative-sharpness filter is a heuristic; the compression index is not a resolution or fidelity measure;
"no candidate" means no candidate by these criteria. A person decides at 100 %, and product fidelity is
judged against real product references, not here.
"""
import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

IMG_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
VID_EXT = {".mov", ".mp4", ".m4v"}
GRID = 6
AHASH_NEAR = 3       # luminance-hash distance for a resemblance
COLOUR_NEAR = 12     # worst 16x16 cell mean |RGB| difference for a resemblance (0..255)
REL_SHARP = 0.25     # heuristic: far blurrier than the best image -> not a candidate
STD_LUMA = np.array([16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55, 14, 13, 16, 24, 40, 57, 69, 56,
                     14, 17, 22, 29, 51, 87, 80, 62, 18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92,
                     49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99])
EXIF_TAGS = {306: "datetime", 271: "make", 272: "model", 305: "software", 36867: "datetime_original"}


# ---------------------------------------------------------------- measures

def jpeg_quality(img):
    """Compression index: libjpeg quality (1-100) that best matches the luminance table, or None."""
    q = getattr(img, "quantization", None)
    if not q or 0 not in q:
        return None
    table = np.sort(np.array(q[0][:64]))
    errs = []
    for quality in range(1, 101):
        scale = 5000 / quality if quality < 50 else 200 - 2 * quality
        errs.append(np.abs(np.sort(np.clip((STD_LUMA * scale + 50) // 100, 1, 255)) - table).sum())
    return int(np.argmin(errs)) + 1


def denoise(gray):
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        return gray
    p = np.pad(gray, 1, mode="edge")
    k = (1.0, 2.0, 1.0)
    rows = sum(k[i] * p[i:i + gray.shape[0], :] for i in range(3)) / 4.0
    return sum(k[j] * rows[:, j:j + gray.shape[1]] for j in range(3)) / 4.0


def laplacian_var(gray):
    """Sharpness after a 3x3 denoise, so grain and JPEG noise do not win. Still content-dependent."""
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        return 0.0
    g = denoise(gray)
    lap = g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:] - 4 * g[1:-1, 1:-1]
    return float(lap.var())


NOISY = 8.0  # estimated noise sigma above which sharpness numbers are flagged as unreliable


def noise_sigma(gray):
    """Immerkaer (1996) fast noise estimate: sharpness of a noisy image is not trustworthy, even denoised."""
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        return 0.0
    g = gray
    conv = (g[:-2, :-2] - 2 * g[:-2, 1:-1] + g[:-2, 2:] - 2 * g[1:-1, :-2] + 4 * g[1:-1, 1:-1] - 2 * g[1:-1, 2:]
            + g[2:, :-2] - 2 * g[2:, 1:-1] + g[2:, 2:])
    return float(np.sqrt(np.pi / 2) * np.abs(conv).sum() / (6 * (g.shape[0] - 2) * (g.shape[1] - 2)))


def focus_map(gray, grid=GRID):
    h, w = gray.shape
    return [[round(laplacian_var(gray[h * i // grid:h * (i + 1) // grid, w * j // grid:w * (j + 1) // grid]), 1)
             for j in range(grid)] for i in range(grid)]


def ahash(img, size=8):
    small = np.asarray(ImageOps.grayscale(img).resize((size, size), Image.Resampling.BILINEAR), dtype=np.float64)
    return int("".join("1" if v else "0" for v in (small > small.mean()).flatten()), 2)


def colour_grid(img, size=16):
    return np.asarray(img.convert("RGB").resize((size, size), Image.Resampling.BOX), dtype=np.int16)


def colour_distance(a, b):
    """Worst-cell colour difference: a luminance hash cannot tell two shades of equal luminance apart."""
    return float(np.abs(a - b).mean(axis=2).max())


def hamming(a, b):
    return bin(a ^ b).count("1")


def measure(path, meta):
    raw = path.read_bytes()
    try:
        im = Image.open(path)
        im.load()
    except (UnidentifiedImageError, OSError) as e:
        return {"file": path.name, "error": f"unreadable: {type(e).__name__}"}, None
    with im:
        exif = im.getexif() if hasattr(im, "getexif") else {}
        info = {"file": path.name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()[:16],
                "format": im.format, "mode": im.mode, "width": im.width, "height": im.height,
                "megapixels": round(im.width * im.height / 1e6, 2),
                "bytes_per_pixel": round(len(raw) / (im.width * im.height), 3),
                "compression_index_jpeg_q": jpeg_quality(im),
                "exif": {name: str(exif.get(tag)) for tag, name in EXIF_TAGS.items() if exif.get(tag)}}
        rgb = ImageOps.exif_transpose(im).convert("RGB")
    arr = np.asarray(rgb)
    info["pixel_sha256"] = hashlib.sha256(f"{rgb.width}x{rgb.height}".encode() + arr.tobytes()).hexdigest()[:16]
    gray = np.asarray(rgb.convert("L"), dtype=np.float64)
    info["contrast_rms"] = round(float(gray.std() / 255), 3)
    # whole image: reported only (white seamless or black backgrounds are legitimate)
    info["blown_highlights"] = round(float((arr.min(axis=2) >= 250).mean()), 4)
    info["deep_shadows"] = round(float((arr.max(axis=2) <= 5).mean()), 4)
    info["sharpness_global"] = round(laplacian_var(gray), 1)
    info["noise_sigma_est"] = round(noise_sigma(gray), 2)
    fm = focus_map(gray)
    info["focus_map"] = fm
    info["sharpness_best_tile"] = max(max(r) for r in fm)
    roi = meta.get("nail_roi")
    if roi:
        x, y, w, h = roi
        info["nail_roi"] = [x, y, w, h]
        info["nail_roi_short_side_px"] = min(w, h)
        info["sharpness_nail"] = round(laplacian_var(gray[y:y + h, x:x + w]), 1)
        info["blown_highlights_nail"] = round(float((arr[y:y + h, x:x + w].min(axis=2) >= 250).mean()), 4)  # penalised
    else:
        info["sharpness_nail"] = "not evaluated"
    for k in ("source", "notes"):
        if meta.get(k):
            info[k] = meta[k]
    info["_ahash"], info["_colour"] = ahash(rgb), colour_grid(rgb)
    return info, rgb


def rank_value(i):
    return i["sharpness_nail"] if isinstance(i["sharpness_nail"], (int, float)) else i["sharpness_best_tile"]


# ---------------------------------------------------------------- video

def probe_video(path):
    if not shutil.which("ffprobe"):
        return {"file": path.name, "error": "ffprobe not installed"}
    p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,codec_name,r_frame_rate:format=duration,size", "-of", "json", str(path)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        return {"file": path.name, "error": p.stderr.strip()[-200:] or "unreadable"}
    d = json.loads(p.stdout)
    s = (d.get("streams") or [{}])[0]
    return {"file": path.name, "width": s.get("width"), "height": s.get("height"), "codec": s.get("codec_name"),
            "fps": s.get("r_frame_rate"), "duration_s": round(float(d.get("format", {}).get("duration", 0) or 0), 2),
            "bytes": int(d.get("format", {}).get("size", 0) or 0)}


def sample_frames(path, out_dir, fps):
    """Returns [(frame file, video name, timestamp in s)]."""
    if not shutil.which("ffmpeg"):
        return []
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-vf", f"fps={fps}",
                    str(out_dir / f"{path.stem}_%05d.png")], capture_output=True)
    return [(f, path.name, round((int(f.stem.rsplit("_", 1)[1]) - 1) / fps, 2))
            for f in sorted(out_dir.glob(f"{path.stem}_*.png"))]


# ---------------------------------------------------------------- sheet

def draw_sheet(items, out_path, thumb=360, cols=4):
    items = [(i, rgb) for i, rgb in items if rgb is not None]
    if not items:
        return
    rows, label_h = (len(items) + cols - 1) // cols, 60
    sheet = Image.new("RGB", (cols * thumb, rows * (thumb + label_h)), (24, 24, 24))
    d = ImageDraw.Draw(sheet)
    for n, (info, rgb) in enumerate(items):
        s = thumb / max(rgb.width, rgb.height)
        t = rgb.resize((max(1, int(rgb.width * s)), max(1, int(rgb.height * s))))
        x0, y0 = (n % cols) * thumb, (n // cols) * (thumb + label_h)
        ox, oy = x0 + (thumb - t.width) // 2, y0 + (thumb - t.height) // 2
        sheet.paste(t, (ox, oy))
        if "nail_roi" in info:
            x, y, w, h = info["nail_roi"]
            d.rectangle([ox + x * s, oy + y * s, ox + (x + w) * s, oy + (y + h) * s], outline=(0, 220, 120), width=2)
        tag = "CANDIDATE " if info.get("candidate") else ("EXACT DUP " if info.get("exact_duplicate_of") else "")
        d.text((x0 + 6, y0 + thumb + 4), f"#{n + 1} {tag}{info['file'][:40]}", fill=(255, 210, 0) if tag == "CANDIDATE " else (235, 235, 235))
        d.text((x0 + 6, y0 + thumb + 22), f"{info['width']}x{info['height']}  q~{info['compression_index_jpeg_q'] or '-'}  "
                                          f"blown {info['blown_highlights']:.1%}", fill=(180, 180, 180))
        d.text((x0 + 6, y0 + thumb + 40), f"sharp nail {info['sharpness_nail']} / tile {info['sharpness_best_tile']}",
               fill=(180, 180, 180))
    sheet.save(out_path, quality=90)


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("--out", "--output", dest="out", default="contact_sheet_out")
    ap.add_argument("--metadata", "--roi", dest="metadata", help="JSON per file: [x,y,w,h] or {nail_roi, source, notes}")
    ap.add_argument("--require-nail", action="store_true", help="images without a nail box cannot be candidates")
    ap.add_argument("--min-short-side", type=int, default=1080)
    ap.add_argument("--min-roi-short-side", type=int, default=400)
    ap.add_argument("--max-blown", type=float, default=0.02, help="max fraction of blown highlights inside the nail box for a candidate")
    ap.add_argument("--fps", type=float, default=1.0)
    args = ap.parse_args(argv)

    src, out = pathlib.Path(args.folder), pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    raw_meta = json.loads(pathlib.Path(args.metadata).read_text()) if args.metadata else {}
    meta = {k: (v if isinstance(v, dict) else {"nail_roi": v}) for k, v in raw_meta.items()}
    files = sorted(p for p in src.iterdir() if p.is_file())

    measured = [measure(p, meta.get(p.name, {})) for p in files if p.suffix.lower() in IMG_EXT]
    errors = [i for i, rgb in measured if rgb is None]
    images = [(i, rgb) for i, rgb in measured if rgb is not None]

    # exact duplicates (file or pixels) are excluded; resemblances are only flagged
    first_of, first_sha = {}, {}
    # among exact copies keep the annotated one (nail box, then source), then the first by name
    for info, _ in sorted(images, key=lambda ir: ("nail_roi" not in ir[0], "source" not in ir[0], ir[0]["file"])):
        key = info["pixel_sha256"]
        if key in first_of:
            info["exact_duplicate_of"] = first_of[key]
            info["exact_duplicate_kind"] = "file" if first_sha[key] == info["sha256"] else "pixels (metadata differ)"
        else:
            first_of[key], first_sha[key] = info["file"], info["sha256"]
    for a in range(len(images)):
        for b in range(a + 1, len(images)):
            ia, ib = images[a][0], images[b][0]
            if ia["pixel_sha256"] != ib["pixel_sha256"] and hamming(ia["_ahash"], ib["_ahash"]) <= AHASH_NEAR \
                    and colour_distance(ia["_colour"], ib["_colour"]) <= COLOUR_NEAR:
                ia.setdefault("resembles", []).append(ib["file"])
                ib.setdefault("resembles", []).append(ia["file"])

    video_info, frames = [], []
    for v in (p for p in files if p.suffix.lower() in VID_EXT):
        video_info.append(probe_video(v))
        for f, vname, ts in sample_frames(v, out / "frames", args.fps):
            with Image.open(f) as fr:
                frames.append({"video": vname, "t_s": ts, "frame": f.name, "_h": ahash(fr.convert("RGB"))})
    for info, _ in images:
        if frames:
            best = min(frames, key=lambda fr: hamming(fr["_h"], info["_ahash"]))
            info["nearest_video_frame"] = {"video": best["video"], "t_s": best["t_s"], "frame": best["frame"],
                                           "distance": hamming(best["_h"], info["_ahash"]),
                                           "meaning": "candidate visual match, not proof of provenance"}

    pool = [i for i, _ in images if not i.get("exact_duplicate_of")]
    top = max([rank_value(i) for i in pool] or [0])
    for i in pool:
        reasons = []
        if min(i["width"], i["height"]) < args.min_short_side:
            reasons.append(f"short side {min(i['width'], i['height'])}px < {args.min_short_side}")
        if args.require_nail and "nail_roi" not in i:
            reasons.append("no nail box (nail sharpness not evaluated)")
        if "nail_roi" in i and i["nail_roi_short_side_px"] < args.min_roi_short_side:
            reasons.append(f"nail box {i['nail_roi_short_side_px']}px < {args.min_roi_short_side}")
        if i.get("blown_highlights_nail", 0) > args.max_blown:
            reasons.append(f"blown highlights on the nail {i['blown_highlights_nail']:.1%}")
        if top and rank_value(i) < REL_SHARP * top:
            reasons.append(f"sharpness < {int(REL_SHARP * 100)} % of the best (heuristic)")
        i["rejection_reasons"] = reasons
        if i["noise_sigma_est"] > NOISY:
            i["caution"] = f"noise sigma ~{i['noise_sigma_est']}: sharpness unreliable, inspect at 100 %"
    ranked = sorted((i for i in pool if not i["rejection_reasons"]), key=lambda i: -rank_value(i))
    candidates = [i["file"] for i in ranked[:3]]
    for i in pool:
        i["candidate"] = i["file"] in candidates
    verdict = ("candidates according to these criteria" if candidates else
               "no candidate according to these criteria: inspect the images at 100 % before deciding whether HD originals are needed")

    draw_sheet(images, out / "contact_sheet.jpg")
    clean = [{k: v for k, v in i.items() if not k.startswith("_")} for i, _ in images]
    report = {"folder": str(src), "criteria": {"min_short_side": args.min_short_side, "min_roi_short_side": args.min_roi_short_side,
              "require_nail": args.require_nail, "max_blown": args.max_blown, "relative_sharpness": REL_SHARP,
              "resemblance": {"ahash_max": AHASH_NEAR, "colour_max": COLOUR_NEAR}},
              "coverage": {"files_in_folder": len(files), "images_measured": len(images), "unreadable": [e["file"] for e in errors],
                           "exact_duplicates": [i["file"] for i in clean if i.get("exact_duplicate_of")],
                           "videos": len(video_info), "frames_sampled": len(frames),
                           "nail_boxes_given": sum(1 for i in clean if "nail_roi" in i)},
              "images": clean, "unreadable": errors, "videos": video_info, "candidates": candidates, "verdict": verdict,
              "limits": ["relative sharpness filter is a heuristic; compare similar zones and scales",
                         "denoised sharpness helps against moderate noise but heavy noise can still win (see caution flags)",
                         "nearest video frame is a candidate visual match, not proof of provenance",
                         "compression index is not a resolution or product-fidelity measure",
                         "ranking is a technical pre-selection, not a product-fidelity validation"]}
    (out / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    lines = [f"# Contact sheet — {src.name}", "", f"Verdict: **{verdict}**", "",
             f"Coverage: {len(files)} files · {len(images)} images measured · {len(errors)} unreadable · "
             f"{len(report['coverage']['exact_duplicates'])} exact duplicates · {len(video_info)} videos · {len(frames)} frames sampled · "
             f"{report['coverage']['nail_boxes_given']} nail boxes", "",
             "| # | File | W×H | q~ | Blown | Sharp nail / best tile | Exact dup of | Resembles | Nearest frame | Candidate / why not |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for n, i in enumerate(clean, 1):
        nv = i.get("nearest_video_frame")
        nv_txt = f"{nv['video']} @ {nv['t_s']} s (d={nv['distance']})" if nv else "-"
        why = ("**yes**" + (f" ⚠ {i['caution']}" if i.get("caution") else "")) if i.get("candidate") else ("; ".join(i.get("rejection_reasons", [])) or "ranked below top 3" if not i.get("exact_duplicate_of") else "excluded")
        lines.append(f"| {n} | {i['file']} | {i['width']}×{i['height']} | {i['compression_index_jpeg_q'] or '-'} | {i['blown_highlights']:.1%} | "
                     f"{i['sharpness_nail']} / {i['sharpness_best_tile']} | {i.get('exact_duplicate_of', '-')} | "
                     f"{', '.join(i.get('resembles', [])) or '-'} | {nv_txt} | {why} |")
    for e in errors:
        lines.append(f"| - | {e['file']} | {e['error']} | | | | | | | not analysed |")
    lines += ["", "Limits: " + " · ".join(report["limits"]) + "."]
    (out / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return report


if __name__ == "__main__":
    main()
