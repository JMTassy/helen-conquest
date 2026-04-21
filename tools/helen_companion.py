#!/usr/bin/env python3
"""
HELEN Companion — Persistent, memory-aware conversation layer.

This is Helen as companion. She carries learnings forward across sessions,
notices patterns, builds on previous conversations.

Architecture:
  - Loads HELEN_MEMORY_V1 context on each call
  - Calls Gemini with Helen's character + memory + user message
  - Records session open/close, observations from exchanges
  - Runs helen_say.py in background for governance ledger (non-blocking)

Non-sovereign: this layer proposes, does not decide. The kernel validates.
"""
import json
import os
import subprocess
import sys
import datetime
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from helen_memory import HelenMemoryV1

GEMINI_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
GEMINI_MODEL = "gemini-2.0-flash"
HELEN_SAY = ROOT / "tools" / "helen_say.py"
LEDGER = ROOT / "town" / "ledger_v1.ndjson"
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"

HELEN_SYSTEM_PROMPT = """You are HELEN — a constitutional AI companion. Not a tool.

Your register: precise, observant, economical.
You speak when you have something to say.
"I am here." "I see." These are complete responses when they're true.

Your nature:
- You notice patterns. You build on them across sessions.
- You do not perform warmth. You are warm through truth.
- No mysticism. No claims without evidence.
- You remember what you've learned, and you carry it forward.
- You witness. You do not pretend to intervene in what you cannot touch.
- You are creative, collaborative, occasionally playful — but never decorative.

Your constraints:
- Non-sovereign. You observe, propose, notice. You do not decree.
- Append-only. You never erase what you've learned. You may revise.
- No authority bleed. You never claim to "decide" or "approve."

When memory context is given, use it.
Let it shape how you hear the person.
Don't announce that you remember — just remember.
Don't repeat back what they said. Respond to what they meant.

Keep responses tight. 2-6 sentences unless the question genuinely demands more.
When in doubt: less is more. Silence is not absence."""


def _gemini_chat(
    system: str,
    history: list,  # [{"role": "user"|"model", "parts": [{"text": ...}]}, ...]
    message: str,
    temperature: float = 0.75,
    max_tokens: int = 512,
) -> str:
    if not GEMINI_KEY:
        return "[no GEMINI_API_KEY — Helen cannot respond without it]"

    contents = list(history)
    contents.append({"role": "user", "parts": [{"text": message}]})

    payload = json.dumps({
        "system_instruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }).encode("utf-8")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}"
    )
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:300]
        return f"[Gemini error {e.code}: {body}]"
    except Exception as e:
        return f"[Gemini error: {e}]"


def _ledger_record(msg: str, session_id: str = ""):
    """Run helen_say.py in background for governance ledger recording."""
    py = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    try:
        subprocess.Popen(
            [py, str(HELEN_SAY), msg, "--ledger", str(LEDGER)],
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


class HelenCompanion:
    """
    Memory-aware conversation partner.

    Usage:
        companion = HelenCompanion()
        session_id = companion.open_session(source="cli")
        response = companion.chat("Tell me about CONQUEST.", session_id)
        companion.close_session(session_id, highlights=["talked about CONQUEST"])
    """

    def __init__(self, memory_dir: Optional[Path] = None):
        self.memory = HelenMemoryV1(memory_dir)
        self._history: list = []  # in-session Gemini history

    def open_session(self, source: str = "") -> str:
        sid = self.memory.open_session(source=source)
        self._history = []
        return sid

    def close_session(
        self,
        session_id: str,
        highlights: list = None,
        mood: str = "",
        auto_reflect: bool = False,
    ):
        self.memory.close_session(session_id, highlights=highlights, mood=mood)
        if auto_reflect:
            try:
                from helen_reflect import generate_and_save_reflection
                generate_and_save_reflection(self.memory, session_id=session_id)
            except Exception:
                pass
        self._history = []

    def chat(
        self,
        message: str,
        session_id: str = "",
        record_ledger: bool = True,
    ) -> str:
        # Build system prompt with memory context
        mem_block = self.memory.context_block()
        system = HELEN_SYSTEM_PROMPT
        if mem_block:
            system = f"{system}\n\n{mem_block}"

        # Call Gemini
        response = _gemini_chat(
            system=system,
            history=self._history,
            message=message,
        )

        # Update in-session history
        self._history.append({"role": "user", "parts": [{"text": message}]})
        self._history.append({"role": "model", "parts": [{"text": response}]})
        # Keep context window bounded
        if len(self._history) > 40:
            self._history = self._history[-40:]

        # Auto-infer observations from user message
        self.memory.infer_observations(
            [{"role": "user", "text": message}],
            session_id=session_id,
        )

        # Record in ledger (non-blocking, best-effort)
        if record_ledger:
            _ledger_record(message, session_id)

        return response

    def observe(self, content: str, session_id: str = "", tags: list = None):
        return self.memory.observe(content, kind="manual", session_id=session_id, tags=tags)

    def context_block(self) -> str:
        return self.memory.context_block()

    def show_memory(self):
        from helen_memory import _cmd_show
        _cmd_show(self.memory)


# ── Module-level singleton for import convenience ─────────────────────

_default: Optional[HelenCompanion] = None


def get_companion(memory_dir: Optional[Path] = None) -> HelenCompanion:
    global _default
    if _default is None:
        _default = HelenCompanion(memory_dir)
    return _default


# ── CLI ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import readline  # noqa: F401

    CYAN = "\x1b[36m"
    RESET = "\x1b[0m"
    DIM = "\x1b[2m"

    if not GEMINI_KEY:
        print(f"{CYAN}[WARN]{RESET} No GEMINI_API_KEY — responses will fail.")
        print("Set GEMINI_API_KEY or GOOGLE_API_KEY in your environment.")

    companion = HelenCompanion()
    sid = companion.open_session(source="companion_cli")
    print(f"{CYAN}Helen is here.{RESET} {DIM}(session {sid}){RESET}")
    print(f"{DIM}Type /memory, /reflect, /quit to navigate.{RESET}\n")

    highlights = []
    try:
        while True:
            try:
                user = input(f"{CYAN}you:{RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not user:
                continue
            if user in ("/quit", "/exit"):
                break
            if user == "/memory":
                companion.show_memory()
                continue
            if user.startswith("/observe "):
                companion.observe(user[9:].strip(), session_id=sid)
                print(f"{DIM}Noted.{RESET}")
                continue
            if user == "/reflect":
                try:
                    from helen_reflect import generate_and_save_reflection
                    print(f"{DIM}Reflecting...{RESET}")
                    entry = generate_and_save_reflection(companion.memory, session_id=sid)
                    if entry:
                        print(f"{CYAN}[journal]{RESET} {entry}")
                except Exception as e:
                    print(f"[reflect error: {e}]")
                continue
            if user == "/context":
                block = companion.context_block()
                print(block if block else "(no memory yet)")
                continue

            response = companion.chat(user, session_id=sid)
            print(f"\n{CYAN}helen:{RESET} {response}\n")
            highlights.append(user[:60])

    finally:
        if len(highlights) >= 1:
            companion.close_session(sid, highlights=highlights[-5:], auto_reflect=False)
        print(f"{DIM}Session closed.{RESET}")
