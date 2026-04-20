"""Mirror Oracle report — per-frame verdict pass over an assembled video.

Extracts N sample frames from the produced video, applies the MIA v1 pixel-hash
stub gate (same as mirror_oracle audit), and emits:
    - per-frame verdict: ✅ green  |  ⚠️ yellow  |  ❌ red
    - aggregate counts

Reads MIA v1 thresholds from mia/mia_helen_dual_v1.json (τ_id_real=0.128,
τ_id_twin=0.127 per 2026-04-20 calibration). Honest stub: pixel-hash distance,
NOT ArcFace. MIA v2 promotion (aura_score fit ≥0.7 Spearman) will swap the
backend.

Usage:
    python3 scripts/mirror_oracle_report.py <video.mp4>
        [--n 12] [--mia mia/mia_helen_dual_v1.json] [--out report.json]

Pure stdlib + ffmpeg + Pillow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow required.", file=sys.stderr)
    sys.exit(3)


def extract_frames(video: Path, n: int, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video),
    ]
    duration = float(subprocess.check_output(cmd, text=True).strip())
    frames: list[Path] = []
    for i in range(n):
        t = duration * (i + 0.5) / n
        out = out_dir / f"frame_{i:02d}.png"
        subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-nostats", "-loglevel", "error",
            "-ss", f"{t:.3f}", "-i", str(video),
            "-frames:v", "1", "-vf", "scale=512:-1",
            str(out),
        ], check=True)
        frames.append(out)
    return frames


def pixel_hash_distance(img_path: Path, ref_hash_hex: str) -> float:
    """Normalized Hamming-like distance between image SHA256 prefix bytes and reference.

    HONEST STUB: this is a placeholder. Real MIA v1 gate uses curated pixel hashes
    against a precomputed anchor. Here we reuse the same principle: compute a
    truncated hash of downscaled grayscale pixel bytes, compare byte-wise to the
    supplied reference hash.
    """
    img = Image.open(img_path).convert("L").resize((32, 32))
    raw = img.tobytes()
    h = hashlib.sha256(raw).hexdigest()
    n = min(len(h), len(ref_hash_hex))
    if n == 0:
        return 1.0
    diff = sum(1 for a, b in zip(h[:n], ref_hash_hex[:n]) if a != b)
    return diff / n


def verdict(d_real: float, d_twin: float, tau_real: float, tau_twin: float) -> str:
    if d_real <= tau_real and d_twin <= tau_twin:
        return "green"
    if d_real <= tau_real * 1.1 or d_twin <= tau_twin * 1.1:
        return "yellow"
    return "red"


def emoji(v: str) -> str:
    return {"green": "\u2705", "yellow": "\u26a0\ufe0f", "red": "\u274c"}.get(v, "?")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--mia", default="mia/mia_helen_dual_v1.json")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    video = Path(args.video)
    mia_path = Path(args.mia)
    if not video.exists() or not mia_path.exists():
        print(f"ERROR: missing video={video.exists()} mia={mia_path.exists()}", file=sys.stderr)
        return 2

    mia = json.loads(mia_path.read_text())
    tau_real = mia.get("tau_id_real", 0.128)
    tau_twin = mia.get("tau_id_twin", 0.127)
    ref_real_hash = mia.get("pixel_hash_ref_real", "00" * 32)
    ref_twin_hash = mia.get("pixel_hash_ref_twin", "ff" * 32)

    with tempfile.TemporaryDirectory() as td:
        frames = extract_frames(video, args.n, Path(td))
        results: list[dict] = []
        for f in frames:
            d_r = pixel_hash_distance(f, ref_real_hash)
            d_t = pixel_hash_distance(f, ref_twin_hash)
            v = verdict(d_r, d_t, tau_real, tau_twin)
            results.append({
                "frame": f.name,
                "d_real": round(d_r, 4),
                "d_twin": round(d_t, 4),
                "verdict": v,
            })
            print(f"  {emoji(v)}  {f.name:15s} d_real={d_r:.4f} d_twin={d_t:.4f}  {v}")

    counts = {"green": 0, "yellow": 0, "red": 0}
    for r in results:
        counts[r["verdict"]] += 1
    report = {
        "schema": "mirror_oracle_report_v1",
        "backend": "pixel_hash_stub",
        "TODO": "swap to ArcFace + CLIP embeddings once MIA v2 is promoted",
        "video": str(video),
        "n_frames": args.n,
        "tau_real": tau_real,
        "tau_twin": tau_twin,
        "counts": counts,
        "frames": results,
    }
    out = Path(args.out) if args.out else video.with_suffix(".mirror_oracle.json")
    out.write_text(json.dumps(report, indent=2))
    print()
    print(f"[mirror_oracle]  \u2705 {counts['green']}  \u26a0\ufe0f {counts['yellow']}  \u274c {counts['red']}")
    print(f"  report → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
