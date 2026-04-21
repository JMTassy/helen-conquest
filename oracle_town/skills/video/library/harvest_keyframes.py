"""harvest_keyframes — extract stills from existing mp4s into the HELEN library.

Walks a source directory, extracts one frame every N seconds from each video,
writes frames to `<out>/stills/<video_stem>/frame_NNN.png`, and emits a
library_manifest.json with source provenance for each frame.

Pure stdlib + ffmpeg subprocess. No PIL ops (stills stay in source colorspace).

Usage:
    python3 harvest_keyframes.py --src /tmp/helen_temple \
        --every 2.0 --out /tmp/helen_temple/library [--limit-per-video 20]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path


def probe_duration(mp4: Path) -> float | None:
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(mp4),
        ], text=True, stderr=subprocess.DEVNULL).strip()
        return float(out) if out else None
    except (subprocess.CalledProcessError, ValueError):
        return None


def extract_frame(mp4: Path, t_sec: float, out_path: Path, scale_w: int = 720) -> bool:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-nostats", "-loglevel", "error",
        "-ss", f"{t_sec:.3f}", "-i", str(mp4),
        "-frames:v", "1", "-vf", f"scale={scale_w}:-1",
        str(out_path),
    ], capture_output=True)
    return result.returncode == 0 and out_path.exists()


def sha256_8(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()[:16]


def harvest(src: Path, out: Path, every_sec: float, scale_w: int,
            limit_per_video: int | None) -> dict:
    stills_root = out / "stills"
    mp4s = sorted(src.glob("*.mp4"))
    manifest: dict = {
        "schema": "helen_library_v1",
        "generated_at_unix": int(time.time()),
        "source_dir": str(src),
        "stills_root": str(stills_root),
        "every_sec": every_sec,
        "scale_w": scale_w,
        "n_videos_seen": len(mp4s),
        "n_frames_total": 0,
        "videos": [],
    }

    for mp4 in mp4s:
        duration = probe_duration(mp4)
        if duration is None or duration < 1.0:
            print(f"  skip {mp4.name}  (no duration)")
            continue
        n = max(1, int(duration // every_sec))
        if limit_per_video is not None:
            n = min(n, limit_per_video)
        video_stem = mp4.stem
        frames: list[dict] = []
        for i in range(n):
            t = (i + 0.5) * every_sec
            if t >= duration:
                break
            frame_path = stills_root / video_stem / f"frame_{i:03d}.png"
            if not extract_frame(mp4, t, frame_path, scale_w):
                continue
            frames.append({
                "frame_id": f"{video_stem}_{i:03d}",
                "t_sec": round(t, 3),
                "path": str(frame_path),
                "sha16": sha256_8(frame_path),
                "source_video": mp4.name,
                "taxonomy": "unclassified",
            })
        manifest["videos"].append({
            "source": mp4.name,
            "duration_sec": round(duration, 3),
            "n_frames": len(frames),
            "frames": frames,
        })
        manifest["n_frames_total"] += len(frames)
        print(f"  harvested {len(frames):3d} frames from {mp4.name}  ({duration:.1f}s)")
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="directory of mp4s")
    ap.add_argument("--out", required=True, help="library output directory")
    ap.add_argument("--every", type=float, default=2.0,
                    help="extract one frame every N seconds (default 2.0)")
    ap.add_argument("--scale-w", type=int, default=720,
                    help="downscale frames to this width (default 720)")
    ap.add_argument("--limit-per-video", type=int, default=None,
                    help="cap frames per video (default: no cap)")
    args = ap.parse_args()

    src = Path(args.src)
    out = Path(args.out)
    if not src.is_dir():
        print(f"ERROR: src {src} not a directory", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)

    manifest = harvest(src, out, args.every, args.scale_w, args.limit_per_video)
    manifest_path = out / "library_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print()
    print(f"[harvest] videos processed : {manifest['n_videos_seen']}")
    print(f"[harvest] frames harvested : {manifest['n_frames_total']}")
    print(f"[harvest] manifest         : {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
