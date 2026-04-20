"""Build arc spec — 3-minute sparse-keyframe protocol.

Consumes an audio_analysis JSON and produces a scene-arc spec:
    [{t_start, t_end, mood, keyframe_id, ken_burns}]

Protocol:
    - Default 12 sparse keyframes over target duration (1 per ~15s for 3min)
    - Mood cycles through a fixed HELEN emotion palette
    - Each segment carries a ken_burns hint (zoom/pan vector) for assemble step

Pure stdlib. Deterministic given same inputs.

Usage:
    python3 scripts/build_arc_spec.py <audio_analysis.json>
        [--n 12] [--duration 180] [--out spec.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MOOD_PALETTE = [
    "calm_open",
    "quiet_bloom",
    "curious_turn",
    "tender_gaze",
    "dramatic_rise",
    "serene_hold",
    "playful_shift",
    "vulnerable_drop",
    "intense_center",
    "contemplative_drift",
    "joyful_release",
    "canonical_return",
]

KEN_BURNS_CYCLE = [
    {"zoom_start": 1.00, "zoom_end": 1.08, "pan": "center"},
    {"zoom_start": 1.10, "zoom_end": 1.00, "pan": "left_to_center"},
    {"zoom_start": 1.00, "zoom_end": 1.06, "pan": "center_to_up"},
    {"zoom_start": 1.05, "zoom_end": 1.12, "pan": "center"},
]


def build_spec(duration: float, n_keyframes: int, analysis: dict | None) -> list[dict]:
    segment_sec = duration / n_keyframes
    spec: list[dict] = []
    for i in range(n_keyframes):
        t_start = round(i * segment_sec, 3)
        t_end = round((i + 1) * segment_sec, 3)
        mood = MOOD_PALETTE[i % len(MOOD_PALETTE)]
        kb = KEN_BURNS_CYCLE[i % len(KEN_BURNS_CYCLE)]
        seg = {
            "idx": i,
            "keyframe_id": f"kf_{i:02d}",
            "t_start": t_start,
            "t_end": t_end,
            "duration_sec": round(t_end - t_start, 3),
            "mood": mood,
            "ken_burns": kb,
        }
        if analysis and analysis.get("energy_windows"):
            energies = [w for w in analysis["energy_windows"] if t_start <= w["t"] < t_end]
            if energies:
                avg = sum(w["rms_db"] for w in energies) / len(energies)
                seg["avg_rms_db"] = round(avg, 2)
        spec.append(seg)
    return spec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("analysis", nargs="?", default=None,
                    help="audio_analysis.json (optional; duration defaults to --duration)")
    ap.add_argument("--n", type=int, default=12, help="number of sparse keyframes")
    ap.add_argument("--duration", type=float, default=180.0,
                    help="target duration in seconds (default 180 = 3min)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    analysis = None
    duration = args.duration
    if args.analysis:
        analysis = json.loads(Path(args.analysis).read_text())
        if "duration_sec" in analysis:
            duration = analysis["duration_sec"]

    spec = build_spec(duration, args.n, analysis)

    manifest = {
        "schema": "arc_spec_v1",
        "protocol": "sparse_keyframe_3min",
        "duration_sec": duration,
        "n_keyframes": args.n,
        "source_analysis": str(args.analysis) if args.analysis else None,
        "segments": spec,
    }

    out = Path(args.out) if args.out else Path("arc_spec.json")
    out.write_text(json.dumps(manifest, indent=2))
    print(f"[build_arc_spec] wrote {out}")
    print(f"  duration   : {duration:.2f}s")
    print(f"  keyframes  : {args.n}")
    print(f"  seg length : ~{duration / args.n:.2f}s each")
    return 0


if __name__ == "__main__":
    sys.exit(main())
