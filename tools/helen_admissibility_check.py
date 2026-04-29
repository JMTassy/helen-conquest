#!/usr/bin/env python3
"""
HELEN admissibility check — runs the 3-layer composite gate on a video.

Layers (per docs/proposals/HELEN_AV_ADMISSIBILITY_GATES_V1.md):
  1. spectral_gate        — temporal luminance Gram coherence
  2. face_motion_gate     — mouth motion activity + autocorrelation structure
  3. av_sync_gate         — mouth motion vs audio envelope cross-correlation

Run with the dedicated uv-managed Python (numpy + cv2 deps):

  experiments/helen_mvp_kernel/.venv-gates/bin/python \
      tools/helen_admissibility_check.py <video.mp4>

Or write a thin shell wrapper if you prefer.

NON_SOVEREIGN. Returns a composite receipt JSON. Caller decides whether to
ship based on composite_verdict.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXP = REPO / "experiments" / "helen_mvp_kernel"
sys.path.insert(0, str(EXP))


def main() -> int:
    ap = argparse.ArgumentParser(description="HELEN admissibility check (3 stacked gates)")
    ap.add_argument("video", help="path to video file (mp4 etc.)")
    ap.add_argument("--av-threshold", type=float, default=0.35,
                    help="AV sync admissibility threshold (default 0.35)")
    ap.add_argument("--min-activity", type=float, default=0.15,
                    help="mouth motion minimum activity threshold (default 0.15)")
    ap.add_argument("--json-only", action="store_true",
                    help="output only the JSON composite receipt, no human-readable lines")
    args = ap.parse_args()

    video = Path(args.video).resolve()
    if not video.exists():
        print(f"ERROR: video not found: {video}", file=sys.stderr)
        return 2

    try:
        from helen_os.gates.composite_admissibility import composite_admissibility
    except ModuleNotFoundError as e:
        print(f"ERROR: gates module not importable: {e}", file=sys.stderr)
        print("Hint: run with the gates venv:", file=sys.stderr)
        print(f"  {EXP}/.venv-gates/bin/python tools/helen_admissibility_check.py <video>",
              file=sys.stderr)
        return 3

    receipt = composite_admissibility(
        str(video),
        face_min_activity=args.min_activity,
        av_threshold=args.av_threshold,
    )

    if args.json_only:
        print(json.dumps(receipt, indent=2, default=str))
        return 0

    # Human-readable summary
    print("=" * 70)
    print(f"HELEN ADMISSIBILITY CHECK")
    print(f"video: {video}")
    print(f"verdict: {receipt['composite_verdict']}")
    print(f"payload_hash: {receipt['payload_hash'][:16]}...")
    print("-" * 70)
    for gate_name in ("spectral_gate", "face_motion_gate", "av_sync_gate"):
        g = receipt["gates"][gate_name]
        print(f"  [{gate_name}] verdict: {g.get('gate_verdict')}")
        if gate_name == "spectral_gate":
            print(f"     margin={g.get('margin')!r:.30}  aeon={g.get('aeon')!r:.30}")
        elif gate_name == "face_motion_gate":
            print(f"     activity={g.get('activity')!r:.20}  threshold={g.get('activity_threshold')}")
            print(f"     spectral_margin={g.get('spectral_margin')!r:.30}")
            print(f"     n_frames={g.get('n_frames_analyzed')}")
        elif gate_name == "av_sync_gate":
            print(f"     sync_score={g.get('sync_score')!r:.20}  optimal_lag={g.get('optimal_lag')}")
            print(f"     threshold={g.get('threshold')}  audio={g.get('audio_present')}  mouth={g.get('mouth_present')}")
    print("=" * 70)
    print()
    print("Full JSON receipt:")
    print(json.dumps(receipt, indent=2, default=str))
    return 0 if receipt["composite_verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
