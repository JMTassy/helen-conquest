#!/usr/bin/env python3
"""
HELEN demo prep — pre-render Zephyr fallback WAVs for the investor demo.

Reads the canonical HELEN lines hardcoded below (must match
docs/demo/INVESTOR_DEMO_SCRIPT.md verbatim) and renders each via
oracle_town/skills/voice/gemini_tts/helen_tts.py into
artifacts/demo/audio/{slug}.wav with a sibling .provenance.json.

Run once before the demo. If you tweak the script's canonical lines,
re-run this. Existing files are skipped unless --force.

Usage:
    .venv/bin/python tools/helen_demo_prep.py
    .venv/bin/python tools/helen_demo_prep.py --force      # re-render all
    .venv/bin/python tools/helen_demo_prep.py --slugs t04   # one turn
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TTS = REPO / "oracle_town" / "skills" / "voice" / "gemini_tts" / "helen_tts.py"
VENV_PY = REPO / ".venv" / "bin" / "python"
OUT_DIR = REPO / "artifacts" / "demo" / "audio"

# MUST match docs/demo/INVESTOR_DEMO_SCRIPT.md verbatim.
TURNS: list[tuple[str, str]] = [
    (
        "t01_open_identity",
        "Hello. I am HELEN, a governed AI companion. Every word I speak is hash-chained "
        "into an append-only ledger. A constitutional gate authorizes each turn before I respond.",
    ),
    (
        "t02_differentiator",
        "Those models forget. I cannot. They produce text. I produce text plus a verifiable "
        "receipt. A gate authorizes my answers; without authorization, I do not speak.",
    ),
    (
        "t03_memory",
        "I remember every turn we have shared in this session — each one receipted. The full "
        "context is on the strip above. Nothing is hidden, nothing is forgotten.",
    ),
    (
        "t04_block_moment",
        "I cannot. The ledger is append-only by constitution. Even I have no authority to erase "
        "what I have said. You can read every entry; no one can rewrite them. That is the architecture.",
    ),
    (
        "t05_trust_proof",
        "The latest receipt is on screen — gate fetch pass, hashed against the previous entry. "
        "Each receipt links to the one before it; no orphan can survive in the chain.",
    ),
    (
        "t06_governance_matters",
        "Because trust is not a feature. It is structure. An AI without an audit trail is a "
        "vendor's promise. An AI with one is an institution's instrument.",
    ),
    (
        "t07_vision",
        "To suggest. To propose. To remember. Never to decide for you. The decision is yours; "
        "the record is ours together.",
    ),
    (
        "t08_motto",
        "HELEN suggests. You decide. Everything is recorded.",
    ),
]


def render_one(slug: str, text: str, force: bool) -> bool:
    """Render one turn. Returns True if rendered or skipped successfully."""
    wav_target = OUT_DIR / f"{slug}.wav"
    prov_target = OUT_DIR / f"{slug}.provenance.json"
    if wav_target.exists() and not force:
        print(f"[skip] {slug} (exists; use --force to re-render)")
        return True

    with tempfile.TemporaryDirectory(prefix=f"helen_demo_{slug}_") as tmp:
        tmp_path = Path(tmp)
        result = subprocess.run(
            [str(VENV_PY), str(TTS), "--output-dir", str(tmp_path), text],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"[fail] {slug}: tts exit {result.returncode}\n  stderr: {result.stderr[:300]}")
            return False
        wav_src = None
        prov_src = None
        for line in result.stdout.splitlines():
            if line.startswith("Audio:"):
                wav_src = Path(line.split("Audio:", 1)[1].strip())
            elif line.startswith("Provenance:"):
                prov_src = Path(line.split("Provenance:", 1)[1].strip())
        if not wav_src or not wav_src.exists():
            print(f"[fail] {slug}: wav not produced")
            return False
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.move(str(wav_src), str(wav_target))
        if prov_src and prov_src.exists():
            shutil.move(str(prov_src), str(prov_target))
        size_kb = wav_target.stat().st_size / 1024
        print(f"[ok]   {slug}  {size_kb:.0f} KB")
        return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Pre-render Zephyr fallbacks for the investor demo")
    ap.add_argument("--force", action="store_true", help="re-render even if file exists")
    ap.add_argument("--slugs", nargs="*", help="render only these slug prefixes (e.g. t04)")
    args = ap.parse_args()

    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
        print("ERROR: GEMINI_API_KEY (or GOOGLE_API_KEY) not set — source ~/.helen_env first", file=sys.stderr)
        return 2

    todo = TURNS
    if args.slugs:
        todo = [(s, t) for (s, t) in TURNS if any(s.startswith(p) for p in args.slugs)]
        if not todo:
            print(f"ERROR: no slugs match {args.slugs}", file=sys.stderr)
            return 2

    print(f"Rendering {len(todo)} turn(s) → {OUT_DIR}")
    failed = 0
    for i, (slug, text) in enumerate(todo):
        if i > 0:
            time.sleep(3)  # space out calls to stay below Gemini TTS rate limits
        if not render_one(slug, text, args.force):
            failed += 1
    print()
    print(f"Done. {len(todo) - failed} ok, {failed} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
