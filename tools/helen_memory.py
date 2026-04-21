#!/usr/bin/env python3
"""
HELEN_MEMORY_V1 — Persistent memory layer.

Append-only NDJSON stores. Non-sovereign (no authority tokens).
L2 Street layer: influences proposals, has zero power over verdicts.

Three channels:
  observations.ndjson  — what Helen notices about the user
  journal.ndjson       — Helen's self-reflections
  sessions.ndjson      — session index with highlights
"""
import json
import os
import datetime
import uuid
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
MEMORY_DIR = ROOT / "memory" / "helen_memory_v1"

# Hard-ban: authority tokens must not enter memory (sovereign boundary)
_BANNED = {"LEDGER", "SEAL", "VERDICT", "SHIP", "HAL_VERDICT", "CUM_HASH", "RECEIPT_ID"}


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def _short_id() -> str:
    return uuid.uuid4().hex[:8]


def _safety_check(text: str) -> None:
    upper = text.upper()
    for tok in _BANNED:
        if tok in upper:
            raise ValueError(f"Memory safety: banned token '{tok}' in content")


def _append_line(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def _read_tail(path: Path, n: int) -> list:
    if not path.exists():
        return []
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s:
                try:
                    lines.append(json.loads(s))
                except Exception:
                    pass
    return lines[-n:] if n > 0 else lines


def _read_all(path: Path) -> list:
    return _read_tail(path, 0)


class HelenMemoryV1:
    def __init__(self, memory_dir: Optional[Path] = None):
        self.dir = Path(memory_dir) if memory_dir else MEMORY_DIR
        self.obs = self.dir / "observations.ndjson"
        self.journal = self.dir / "journal.ndjson"
        self.sessions = self.dir / "sessions.ndjson"
        self.dir.mkdir(parents=True, exist_ok=True)

    # ── Observations ──────────────────────────────────────────────────

    def observe(
        self,
        content: str,
        kind: str = "user_pattern",
        session_id: str = "",
        tags: list = None,
    ) -> dict:
        """Record something Helen has noticed about the user or context."""
        _safety_check(content)
        rec = {
            "id": _short_id(),
            "ts": _now(),
            "session_id": session_id,
            "kind": kind,
            "content": content,
            "tags": tags or [],
        }
        _append_line(self.obs, rec)
        return rec

    def recent_observations(self, n: int = 15) -> list:
        return _read_tail(self.obs, n)

    def all_observations(self) -> list:
        return _read_all(self.obs)

    # ── Journal / Self-reflection ─────────────────────────────────────

    def reflect(self, content: str, session_id: str = "", tags: list = None) -> dict:
        """Append a Helen self-reflection entry."""
        _safety_check(content)
        rec = {
            "id": _short_id(),
            "ts": _now(),
            "session_id": session_id,
            "content": content,
            "tags": tags or [],
        }
        _append_line(self.journal, rec)
        return rec

    def recent_reflections(self, n: int = 5) -> list:
        return _read_tail(self.journal, n)

    # ── Sessions ──────────────────────────────────────────────────────

    def open_session(self, session_id: str = None, source: str = "") -> str:
        """Record session open. Returns session_id."""
        sid = session_id or f"S_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        _append_line(self.sessions, {
            "session_id": sid,
            "event": "open",
            "ts": _now(),
            "source": source,
        })
        return sid

    def close_session(
        self,
        session_id: str,
        highlights: list = None,
        mood: str = "",
    ) -> dict:
        """Seal a session with highlights."""
        rec = {
            "session_id": session_id,
            "event": "close",
            "ts": _now(),
            "highlights": highlights or [],
            "mood": mood,
        }
        _append_line(self.sessions, rec)
        return rec

    def recent_sessions(self, n: int = 5) -> list:
        """Return the n most recent closed sessions with highlights."""
        all_ev = _read_all(self.sessions)
        closed = [e for e in all_ev if e.get("event") == "close" and e.get("highlights")]
        return closed[-n:]

    # ── Context block for prompt injection ───────────────────────────

    def context_block(
        self,
        n_sessions: int = 3,
        n_obs: int = 15,
        n_reflections: int = 2,
    ) -> str:
        """
        Build a concise memory context block for injection into Helen's prompt.
        Returns empty string if no memory exists yet.
        """
        parts = []

        sessions = self.recent_sessions(n_sessions)
        if sessions:
            parts.append("Past sessions:")
            for s in sessions:
                ts = s.get("ts", "")[:10]
                hi = "; ".join(s.get("highlights", []))
                if hi:
                    parts.append(f"  [{ts}] {hi}")

        obs = self.recent_observations(n_obs)
        if obs:
            parts.append("What I know about this person:")
            for o in obs:
                parts.append(f"  • {o.get('content', '')}")

        refs = self.recent_reflections(n_reflections)
        if refs:
            parts.append("My recent reflections:")
            for r in refs:
                ts = r.get("ts", "")[:10]
                parts.append(f"  [{ts}] {r.get('content', '')}")

        if not parts:
            return ""

        return (
            "=== HELEN MEMORY ===\n"
            + "\n".join(parts)
            + "\n=== END MEMORY ==="
        )

    # ── Observation extraction helpers ───────────────────────────────

    def infer_observations(
        self,
        exchange: list,  # [{"role": "user"|"helen", "text": ...}, ...]
        session_id: str = "",
    ) -> list:
        """
        Simple heuristic extraction of observations from an exchange.
        Returns list of saved observation records.
        Caller should pass exchanges worth recording; this does not call LLM.
        """
        saved = []
        for turn in exchange:
            if turn.get("role") == "user":
                text = turn.get("text", "")
                # Record topics that seem emotionally significant
                if any(kw in text.lower() for kw in [
                    "i feel", "i think", "i need", "i want", "i'm worried",
                    "i love", "i hate", "important", "crucial", "stressed",
                    "excited", "afraid", "hope", "dream",
                ]):
                    rec = self.observe(
                        f"User said: \"{text[:120]}\"",
                        kind="user_state",
                        session_id=session_id,
                        tags=["auto"],
                    )
                    saved.append(rec)
        return saved


# ── CLI ───────────────────────────────────────────────────────────────

def _cmd_show(mem: HelenMemoryV1):
    print("\n=== HELEN MEMORY ===")
    obs = mem.recent_observations(20)
    if obs:
        print(f"\nObservations ({len(obs)}):")
        for o in obs:
            ts = o.get("ts", "")[:10]
            print(f"  [{ts}] {o.get('kind','?')} — {o.get('content','')}")
    refs = mem.recent_reflections(5)
    if refs:
        print(f"\nJournal ({len(refs)} recent):")
        for r in refs:
            ts = r.get("ts", "")[:10]
            print(f"  [{ts}] {r.get('content','')}")
    sessions = mem.recent_sessions(5)
    if sessions:
        print(f"\nSessions ({len(sessions)} recent):")
        for s in sessions:
            ts = s.get("ts", "")[:10]
            hi = "; ".join(s.get("highlights", []))
            print(f"  [{ts}] {hi or '(no highlights)'}")
    if not obs and not refs and not sessions:
        print("  (empty — no memory yet)")
    print()


if __name__ == "__main__":
    import sys
    mem = HelenMemoryV1()

    if len(sys.argv) < 2:
        _cmd_show(mem)
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "show":
        _cmd_show(mem)
    elif cmd == "observe" and len(sys.argv) > 2:
        text = " ".join(sys.argv[2:])
        rec = mem.observe(text, kind="manual")
        print(f"Saved observation {rec['id']}: {text[:60]}")
    elif cmd == "context":
        block = mem.context_block()
        print(block if block else "(no memory yet)")
    else:
        print(f"Usage: helen_memory.py [show|observe <text>|context]")
