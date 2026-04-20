"""Assemble video — Ken Burns + xfade crossfades from keyframes.

Consumes the keyframes_manifest.json (from render_keyframes.py) and an
arc_spec.json. Builds a single ffmpeg command with:
    - zoompan filter per keyframe (ken-burns per ken_burns hint)
    - xfade between consecutive keyframes (dissolve)
    - audio overlaid if provided

Pure stdlib + ffmpeg subprocess. No MoviePy / OpenCV.

Usage:
    python3 scripts/assemble_video.py <arc_spec.json> <keyframes_manifest.json>
        [--audio path.mp3] [--out /tmp/helen_arc.mp4] [--fps 30] [--size 1080x1920]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

XFADE_SEC = 0.8


def zoompan_expr(kb: dict, duration_sec: float, fps: int) -> str:
    zs = kb.get("zoom_start", 1.00)
    ze = kb.get("zoom_end", 1.05)
    frames = max(1, int(round(duration_sec * fps)))
    z_expr = f"{zs}+({ze}-{zs})*on/{frames}"
    pan = kb.get("pan", "center")
    if pan == "left_to_center":
        x_expr = "iw/2-(iw/zoom/2)+(iw/zoom/4)*(1-on/%d)" % frames
        y_expr = "ih/2-(ih/zoom/2)"
    elif pan == "center_to_up":
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)-(ih/zoom/8)*(on/%d)" % frames
    else:
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    return f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':d={frames}:fps={fps}:s={{size}}"


def build_filter_graph(spec: dict, keyframes: list[dict], fps: int, size: str) -> tuple[str, list[str]]:
    segments = spec["segments"]
    by_id = {k["keyframe_id"]: k for k in keyframes}
    inputs: list[str] = []
    filters: list[str] = []
    for i, seg in enumerate(segments):
        kf = by_id[seg["keyframe_id"]]
        inputs.extend(["-loop", "1", "-t", f"{seg['duration_sec']}", "-i", kf["out_path"]])
        zp = zoompan_expr(seg["ken_burns"], seg["duration_sec"], fps).format(size=size)
        filters.append(f"[{i}:v]{zp},format=yuv420p[v{i}]")

    chain = f"[v0]"
    offset = segments[0]["duration_sec"] - XFADE_SEC
    for i in range(1, len(segments)):
        nxt = f"[x{i}]"
        filters.append(f"{chain}[v{i}]xfade=transition=dissolve:duration={XFADE_SEC}:offset={offset:.3f}{nxt}")
        chain = nxt
        offset += segments[i]["duration_sec"] - XFADE_SEC
    final_v_label = chain
    filter_complex = ";".join(filters) + f";{final_v_label}null[vout]"
    return filter_complex, inputs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("arc_spec")
    ap.add_argument("keyframes_manifest")
    ap.add_argument("--audio", default=None)
    ap.add_argument("--out", default="/tmp/helen_arc_v04.mp4")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--size", default="1080x1920")
    args = ap.parse_args()

    spec = json.loads(Path(args.arc_spec).read_text())
    kfm = json.loads(Path(args.keyframes_manifest).read_text())

    if not spec.get("segments") or not kfm.get("keyframes"):
        print("ERROR: spec or keyframes empty", file=sys.stderr)
        return 2

    filter_complex, inputs = build_filter_graph(spec, kfm["keyframes"], args.fps, args.size)

    cmd = ["ffmpeg", "-y", "-hide_banner"] + inputs
    if args.audio:
        cmd += ["-i", args.audio]
    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[vout]",
    ]
    if args.audio:
        audio_idx = len(spec["segments"])
        cmd += ["-map", f"{audio_idx}:a", "-shortest"]
    cmd += [
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(args.fps),
        "-preset", "medium", "-crf", "20",
        args.out,
    ]

    print(f"[assemble_video] ffmpeg invocation length: {len(cmd)} args")
    print(f"  segments: {len(spec['segments'])}  audio: {bool(args.audio)}  out: {args.out}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("ffmpeg stderr (last 40 lines):", file=sys.stderr)
        print("\n".join(result.stderr.splitlines()[-40:]), file=sys.stderr)
        return result.returncode
    print(f"  → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
