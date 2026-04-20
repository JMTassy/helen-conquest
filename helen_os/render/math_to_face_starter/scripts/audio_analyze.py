"""Audio analyze — stdlib + ffmpeg, no librosa / numpy.

Extracts rough temporal features from an audio file for arc-spec construction.
Uses ffprobe for metadata, ffmpeg astats/silencedetect filters for energy
markers. Output is a JSON manifest consumable by build_arc_spec.py.

Usage:
    python3 scripts/audio_analyze.py <audio_file> [--out path.json]

Laptop constraint: pip broken on 3.14; no numpy/librosa/scipy available. Stdlib
+ ffmpeg subprocess only.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def probe_duration(path: Path) -> float:
    """Get duration in seconds via ffprobe."""
    out = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ], text=True).strip()
    return float(out)


def silence_markers(path: Path, thresh_db: float = -30.0, min_sec: float = 0.5) -> list[dict]:
    """Detect silences via ffmpeg silencedetect filter."""
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
        "-af", f"silencedetect=noise={thresh_db}dB:d={min_sec}",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    stderr = result.stderr
    starts = [float(m.group(1)) for m in re.finditer(r"silence_start: ([\d.]+)", stderr)]
    ends = [float(m.group(1)) for m in re.finditer(r"silence_end: ([\d.]+)", stderr)]
    pairs = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else None
        pairs.append({"silence_start": s, "silence_end": e})
    return pairs


def energy_windows(path: Path, window_sec: float = 2.0) -> list[dict]:
    """Coarse RMS per window via ffmpeg astats. Returns [{t, rms_db}, ...]."""
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
        "-af", f"astats=metadata=1:reset={window_sec},"
               f"ametadata=print:key=lavfi.astats.Overall.RMS_level",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    stderr = result.stderr
    windows: list[dict] = []
    time_re = re.compile(r"pts_time:([\d.]+)")
    rms_re = re.compile(r"lavfi\.astats\.Overall\.RMS_level=(-?[\d.]+|-?inf)")
    cur_t = None
    for line in stderr.splitlines():
        tm = time_re.search(line)
        if tm:
            cur_t = float(tm.group(1))
        rm = rms_re.search(line)
        if rm and cur_t is not None:
            raw = rm.group(1)
            val = -120.0 if raw.endswith("inf") else float(raw)
            windows.append({"t": round(cur_t, 3), "rms_db": val})
            cur_t = None
    return windows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--out", default=None)
    ap.add_argument("--window-sec", type=float, default=2.0)
    args = ap.parse_args()

    audio = Path(args.audio)
    if not audio.exists():
        print(f"ERROR: {audio} not found", file=sys.stderr)
        return 2

    duration = probe_duration(audio)
    silences = silence_markers(audio)
    energies = energy_windows(audio, window_sec=args.window_sec)

    manifest = {
        "schema": "audio_analysis_v1",
        "source": str(audio),
        "duration_sec": duration,
        "window_sec": args.window_sec,
        "n_energy_windows": len(energies),
        "n_silence_intervals": len(silences),
        "silences": silences,
        "energy_windows": energies,
    }

    out_path = Path(args.out) if args.out else audio.with_suffix(".audio_analysis.json")
    out_path.write_text(json.dumps(manifest, indent=2))
    print(f"[audio_analyze] wrote {out_path}")
    print(f"  duration       : {duration:.2f}s")
    print(f"  energy windows : {len(energies)}")
    print(f"  silences       : {len(silences)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
