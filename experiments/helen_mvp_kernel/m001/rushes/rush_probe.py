"""M001 rush probe: what is in a folder of MOV/MP4 rushes, read from the files themselves. NON_SOVEREIGN · authority=false.

For each clip: duration, native size and display rotation, frame rate, codec, HDR transfer (iPhone HLG/PQ), audio,
SHA-256; then K frames sampled evenly, a per-clip contact sheet with timecodes, and a sharpness score per frame
(variance of the Laplacian at 960 px wide). Plus one triage sheet with the middle frame of every clip.

    python rush_probe.py /path/to/CALVI --out /path/outside/the/repo/rush_probe [--frames 8] [--limit 20]

Deterministic (ffprobe/ffmpeg, numpy, Pillow): no AI model, no upload, no network. It does not judge content:
hands, nails, faces and rights are for a person to check on the sheets. Client footage stays local: the script
refuses an --out inside a git working tree (this repository is public) unless --allow-in-repo.
"""
import argparse
import csv
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

VIDEO_EXT = {".mov", ".mp4", ".m4v"}
HDR = {"arib-std-b67": "HLG", "smpte2084": "PQ"}


def inside_git(path):
    p = pathlib.Path(path).resolve()
    return any((q / ".git").exists() for q in [p, *p.parents])


def sha256(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
                       capture_output=True, text=True)
    if r.returncode:
        return {"error": r.stderr.strip()[:200]}
    d = json.loads(r.stdout)
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), None)
    if v is None:
        return {"error": "no video stream"}
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(sd["rotation"])
    rot = rot or int((v.get("tags") or {}).get("rotate", 0) or 0)
    num, den = (v.get("avg_frame_rate") or "0/1").split("/")
    fps = round(int(num) / int(den), 3) if int(den) else 0.0
    w, h = int(v.get("width", 0)), int(v.get("height", 0))
    disp = (h, w) if abs(rot) % 180 == 90 else (w, h)
    return {"duration_s": round(float(d["format"].get("duration", v.get("duration", 0)) or 0), 3),
            "coded_size": f"{w}x{h}", "display_size": f"{disp[0]}x{disp[1]}", "rotation": rot,
            "orientation": "portrait" if disp[1] > disp[0] else "landscape" if disp[0] > disp[1] else "square",
            "fps": fps, "codec": v.get("codec_name"), "pix_fmt": v.get("pix_fmt"),
            "hdr": HDR.get(v.get("color_transfer"), "SDR" if v.get("color_transfer") else "unknown"),
            "bit_rate_mbps": round(int(d["format"].get("bit_rate", 0) or 0) / 1e6, 1),
            "audio": any(s.get("codec_type") == "audio" for s in d["streams"])}


def grab(path, t, width=960):
    """One frame at time t, display-oriented (ffmpeg applies rotation), scaled to `width`, as RGB array."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(path), "-frames:v", "1",
                        "-vf", f"scale={width}:-2", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True)
    if r.returncode or not r.stdout:
        return None
    probe_w = width
    n = len(r.stdout) // 3
    h = n // probe_w
    return np.frombuffer(r.stdout[: probe_w * h * 3], np.uint8).reshape(h, probe_w, 3)


def sharpness(rgb):
    g = rgb.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    lap = -4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:]
    return round(float(lap.var()), 1)


def sheet(frames, labels, path, tile=320):
    th = max(int(tile * f.shape[0] / f.shape[1]) for f in frames)
    cols = min(4, len(frames))
    rows = (len(frames) + cols - 1) // cols
    im = Image.new("RGB", (cols * tile, rows * (th + 18)), (16, 16, 16))
    d = ImageDraw.Draw(im)
    for i, (f, lab) in enumerate(zip(frames, labels)):
        t = Image.fromarray(f).resize((tile, int(tile * f.shape[0] / f.shape[1])), Image.LANCZOS)
        x, y = (i % cols) * tile, (i // cols) * (th + 18)
        im.paste(t, (x, y))
        d.text((x + 4, y + th + 3), lab, fill=(220, 210, 190))
    im.save(path)


def run(src, out, k=8, limit=None):
    src, out = pathlib.Path(src), pathlib.Path(out)
    files = sorted(p for p in (src.iterdir() if src.is_dir() else [src]) if p.suffix.lower() in VIDEO_EXT)
    if limit:
        files = files[:limit]
    out.mkdir(parents=True, exist_ok=True)
    rows, mids, mid_labels = [], [], []
    for p in files:
        meta = probe(p)
        row = {"file": p.name, "bytes": p.stat().st_size, "sha256": sha256(p), **meta}
        if "error" not in meta and meta["duration_s"] > 0:
            ts = [(i + 0.5) / k * meta["duration_s"] for i in range(k)]
            frames, labels, sharp = [], [], []
            for t in ts:
                f = grab(p, t)
                if f is not None:
                    frames.append(f)
                    sharp.append(sharpness(f))
                    labels.append(f"{t:6.2f}s  sharp {sharp[-1]:.0f}")
            if frames:
                sheet(frames, labels, out / f"{p.stem}_sheet.png")
                best = int(np.argmax(sharp))
                row.update({"frames_sampled": len(frames), "sharpness_max": max(sharp),
                            "sharpness_median": float(np.median(sharp)), "sharpest_at_s": round(ts[best], 2)})
                mids.append(frames[len(frames) // 2])
                mid_labels.append(p.name[:28])
        rows.append(row)
        print(f"{p.name}: {row.get('display_size', '?')} {row.get('duration_s', '?')} s {row.get('hdr', '')}"
              f" sharp max {row.get('sharpness_max', '-')}", flush=True)
    for i in range(0, len(mids), 24):
        sheet(mids[i:i + 24], mid_labels[i:i + 24], out / f"triage_{i // 24 + 1:02d}.png", tile=240)
    keys = sorted({k_ for r in rows for k_ in r}, key=lambda s: (s != "file", s))
    with open(out / "rushes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    (out / "rushes.json").write_text(json.dumps({"status": "NON_SOVEREIGN", "authority": False,
                                                 "note": "metadata and sampled frames only; content, faces and rights need a person",
                                                 "frames_per_clip": k, "clips": rows}, indent=1))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", help="a folder of rushes, or one file")
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None, help="only the first N clips (sorted by name)")
    ap.add_argument("--allow-in-repo", action="store_true")
    a = ap.parse_args(argv)
    if inside_git(a.out) and not a.allow_in_repo:
        ap.error(f"{a.out} is inside a git working tree: client footage must not land in a repository")
    for tool in ("ffprobe", "ffmpeg"):
        if shutil.which(tool) is None:
            sys.exit(f"{tool} not found: install ffmpeg first")
    return run(a.src, a.out, a.frames, a.limit)


if __name__ == "__main__":
    main()
