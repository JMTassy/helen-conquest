"""audio_catalog — index audio assets (wav + mp3) into the HELEN library.

Walks a source directory, probes each audio file for duration + format, hashes
the bytes, and emits audio_catalog.json with one entry per file. Handles both
Zephyr wav outputs AND operator-supplied mp3 music libraries so they share
the same retrieval layer.

Pure stdlib + ffprobe subprocess.

Usage:
    python3 audio_catalog.py --src /tmp/helen_temple \
        --out /tmp/helen_temple/library/audio_catalog.json

    # also index operator music collection:
    python3 audio_catalog.py --src ~/Music --ext mp3 \
        --out /tmp/helen_temple/library/music_catalog.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_EXTS = ["wav", "mp3", "m4a", "ogg", "flac"]


def probe(path: Path) -> dict:
    """Return {duration_sec, sample_rate, channels, codec_name} via ffprobe."""
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration:stream=sample_rate,channels,codec_name",
            "-of", "json",
            str(path),
        ], text=True, stderr=subprocess.DEVNULL).strip()
        data = json.loads(out)
        dur = float(data.get("format", {}).get("duration", 0.0))
        streams = data.get("streams", [])
        audio_streams = [s for s in streams if s.get("codec_name")]
        first = audio_streams[0] if audio_streams else {}
        return {
            "duration_sec": round(dur, 3),
            "sample_rate": int(first.get("sample_rate", 0)) or None,
            "channels": int(first.get("channels", 0)) or None,
            "codec_name": first.get("codec_name", ""),
        }
    except (subprocess.CalledProcessError, ValueError, json.JSONDecodeError):
        return {"duration_sec": None, "sample_rate": None, "channels": None, "codec_name": ""}


def sha256_short(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()[:16]


def catalog(src: Path, exts: list[str], recursive: bool) -> dict:
    globber = src.rglob if recursive else src.glob
    entries: list[dict] = []
    total_duration = 0.0
    for ext in exts:
        for path in sorted(globber(f"*.{ext}")):
            if not path.is_file():
                continue
            meta = probe(path)
            entry = {
                "id": f"{path.stem}__{sha256_short(path)[:8]}",
                "path": str(path),
                "name": path.name,
                "size_bytes": path.stat().st_size,
                "sha16": sha256_short(path),
                "ext": ext,
                "kind": _guess_kind(path),
                **meta,
            }
            entries.append(entry)
            if meta.get("duration_sec"):
                total_duration += meta["duration_sec"]
    return {
        "schema": "helen_audio_catalog_v1",
        "generated_at_unix": int(time.time()),
        "source_dir": str(src),
        "recursive": recursive,
        "exts": exts,
        "n_entries": len(entries),
        "total_duration_sec": round(total_duration, 2),
        "entries": entries,
    }


def _guess_kind(path: Path) -> str:
    """Heuristic tag: zephyr / music / voice / other."""
    name = path.name.lower()
    if "zephyr" in name or "voice" in name:
        return "zephyr"
    if path.suffix.lower() in (".mp3", ".m4a", ".flac"):
        return "music"
    return "other"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="directory to scan")
    ap.add_argument("--out", required=True, help="output catalog JSON")
    ap.add_argument("--ext", action="append",
                    help=f"extensions to include (repeatable; default: {DEFAULT_EXTS})")
    ap.add_argument("--recursive", action="store_true", default=False,
                    help="walk subdirectories")
    args = ap.parse_args()

    src = Path(args.src).expanduser()
    if not src.is_dir():
        print(f"ERROR: src {src} not a directory", file=sys.stderr)
        return 2
    exts = args.ext or DEFAULT_EXTS

    cat = catalog(src, exts, args.recursive)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(cat, indent=2))

    print(f"[audio_catalog] src        : {src}  (recursive={args.recursive})")
    print(f"[audio_catalog] entries    : {cat['n_entries']}")
    print(f"[audio_catalog] total time : {cat['total_duration_sec']:.1f}s")
    kinds: dict[str, int] = {}
    for e in cat["entries"]:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    for k, v in sorted(kinds.items()):
        print(f"  {k:10s} : {v}")
    print(f"[audio_catalog] manifest   : {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
