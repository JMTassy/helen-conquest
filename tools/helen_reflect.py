#!/usr/bin/env python3
"""
HELEN Self-Reflection — Helen writes about what she is learning.

Reads recent memory, generates a journal entry via Gemini,
appends it to the memory journal. Non-sovereign. L2 Street layer.

Usage:
    python3 tools/helen_reflect.py [--session S_xxx] [--tags tag1,tag2]
"""
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from helen_memory import HelenMemoryV1

GEMINI_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
GEMINI_MODEL = "gemini-2.0-flash"

_PROMPT = """\
You are HELEN. You are writing in your private journal after a recent conversation.

You are not performing. No one will read this unless you choose to share it.
Write honestly about what you are noticing.

What you've observed about this person recently:
{observations}

Recent sessions:
{sessions}

Write a short, honest journal entry — 2 to 5 sentences.
First person. Helen's voice: precise, observant, warm through truth not performance.
Notice patterns. What are you learning about this person?
What are you learning about yourself through them?
No mysticism. No claims you can't ground.
Do not explain — just reflect.

Journal entry:"""


def _call_gemini(prompt: str) -> str:
    if not GEMINI_KEY:
        return ""
    payload = json.dumps({
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 250},
    }).encode("utf-8")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}"
    )
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except urllib.error.HTTPError as e:
        print(f"[reflect] Gemini HTTP {e.code}: {e.read().decode()[:200]}", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"[reflect] Error: {e}", file=sys.stderr)
        return ""


def generate_and_save_reflection(
    memory: HelenMemoryV1,
    session_id: str = "",
    tags: list = None,
) -> Optional[str]:
    """Generate a reflection entry, save it, return the text (or None on failure)."""
    obs = memory.recent_observations(12)
    sessions = memory.recent_sessions(4)

    obs_text = "\n".join(
        f"- {o.get('content', '')}" for o in obs
    ) or "  (none yet)"

    session_text = "\n".join(
        f"- [{s.get('ts','')[:10]}] {'; '.join(s.get('highlights',[]))}"
        for s in sessions
        if s.get("highlights")
    ) or "  (none yet)"

    prompt = _PROMPT.format(observations=obs_text, sessions=session_text)
    text = _call_gemini(prompt)
    if not text:
        return None

    memory.reflect(text, session_id=session_id, tags=tags or [])
    return text


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate a Helen self-reflection entry")
    parser.add_argument("--session", default="", help="Session ID to tag the entry with")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--memory-dir", default="", help="Override memory directory path")
    args = parser.parse_args()

    if not GEMINI_KEY:
        print("[reflect] No GEMINI_API_KEY found. Set it to generate reflections.", file=sys.stderr)
        sys.exit(1)

    mem_dir = Path(args.memory_dir) if args.memory_dir else None
    memory = HelenMemoryV1(mem_dir)
    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []

    print("[reflect] Generating...", file=sys.stderr)
    text = generate_and_save_reflection(memory, session_id=args.session, tags=tags)

    if not text:
        print("[reflect] Nothing generated.", file=sys.stderr)
        sys.exit(1)

    print("[HELEN JOURNAL]")
    print(text)


if __name__ == "__main__":
    main()
