"""
helen_star_bridge.py — HELEN OS Channel C → Star-Office-UI state bridge

Architecture contract (HELEN OS Canon V1 §5):
  - Channel A (sovereign ledger)  : NEVER touched by this module
  - Channel B (MemoryKernel)      : Read-only — used to generate daily memos
  - Channel C (RunTrace / UI)     : This module writes non-sovereign state here

This bridge is a presentation adapter only.
It publishes HELEN's current activity to Star-Office-UI so the pixel office
shows what HELEN is doing — without granting any authority to the UI.

Mapping:
  HELEN activity              → Star-Office state
  ─────────────────────────────────────────────────
  Waiting / standby           → idle
  Receiving user input        → receiving
  Thinking / retrieval        → researching
  Drafting / synthesis        → writing
  Tool calls / gateway        → executing
  Memory sync / federation    → syncing
  Error / gate fail / BLOCK   → error
  Generating reply            → replying

Usage (as a module, from server.py):
  from helen_star_bridge import HelenStarBridge
  bridge = HelenStarBridge()
  bridge.update_state("researching", "HELEN is thinking...")

Usage (standalone CLI):
  python helen_star_bridge.py writing "Drafting law proposal"
  python helen_star_bridge.py idle
  python helen_star_bridge.py --register-agents   # push agent roster once
"""

from __future__ import annotations

import json
import os
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ──────────────────────────────────────────────────────────────────────────────
# Paths (all relative to helen_os_scaffold/, resolved from this file's location)
# ──────────────────────────────────────────────────────────────────────────────

_THIS_DIR = Path(__file__).parent.resolve()

STAR_OFFICE_DIR = _THIS_DIR / "Star-Office-UI"
STATE_FILE = STAR_OFFICE_DIR / "state.json"
AGENTS_STATE_FILE = STAR_OFFICE_DIR / "agents-state.json"
JOIN_KEYS_FILE = STAR_OFFICE_DIR / "join-keys.json"
MEMORY_DIR = _THIS_DIR / "memory"         # Star-Office reads memos from here

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

VALID_STATES = [
    "idle", "writing", "receiving", "replying",
    "researching", "executing", "syncing", "error",
]

# State → area (mirrors Star-Office-UI logic)
STATE_AREA = {
    "idle": "breakroom",
    "writing": "writing",
    "receiving": "writing",
    "replying": "writing",
    "researching": "writing",
    "executing": "writing",
    "syncing": "writing",
    "error": "error",
}

# HELEN's canonical agent roster (L0 + L1 layer)
HELEN_AGENTS = [
    {"id": "helen-main",     "name": "HELEN",      "role": "Cognitive compiler — non-sovereign"},
    {"id": "hal-auditor",    "name": "HAL",         "role": "Sovereignty gate — PASS / WARN / BLOCK"},
    {"id": "planner-l1",     "name": "Planner",     "role": "L1 servitor — generates step list"},
    {"id": "worker-l1",      "name": "Worker",      "role": "L1 servitor — produces draft"},
    {"id": "critic-l1",      "name": "Critic",      "role": "L1 servitor — critiques draft"},
    {"id": "archivist-l1",   "name": "Archivist",   "role": "L1 servitor — synthesizes artifact"},
]

# Keywords that signal specific modes in HELEN's response text
_MODE_SIGNALS: list[tuple[list[str], str]] = [
    (["BLOCK", "required_fixes", "❌"],          "error"),
    (["WARN", "potential issue"],                "error"),
    (["receipt", "ledger", "gate", "GovernanceVM", "reducer"], "executing"),
    (["federati", "sync", "MemoryKernel"],       "syncing"),
    (["retrieving", "jmt_retrieval", "framework", "oracle-governance",
      "research", "manifest", "plugin"],         "researching"),
    (["draft", "proposal", "writing", "synthesis", "[HER]"], "writing"),
]


# ──────────────────────────────────────────────────────────────────────────────
# Core bridge class
# ──────────────────────────────────────────────────────────────────────────────

class HelenStarBridge:
    """
    Non-sovereign Channel C bridge.

    Writes HELEN's current activity into Star-Office-UI state files.
    Never reads or writes Channel A (ledger) or Channel B (memory) directly.
    Memory (Channel B) is accessed read-only for daily memo generation.
    """

    def __init__(self, star_office_dir: Optional[Path] = None):
        self.star_office_dir = Path(star_office_dir) if star_office_dir else STAR_OFFICE_DIR
        self.state_file = self.star_office_dir / "state.json"
        self.agents_file = self.star_office_dir / "agents-state.json"
        self._lock = threading.Lock()

    # ── State management ──────────────────────────────────────────────────────

    def update_state(self, state: str, detail: str = "", progress: int = 0) -> bool:
        """
        Write a new state to Star-Office-UI.
        This is the primary public API — call this after each HELEN turn.
        Returns True on success, False if Star-Office is not present (graceful skip).
        """
        if state not in VALID_STATES:
            state = "idle"

        if not self.state_file.parent.exists():
            return False   # Star-Office not cloned — skip silently

        payload = {
            "state": state,
            "detail": detail or _default_detail(state),
            "progress": max(0, min(100, progress)),
            "updated_at": datetime.now().isoformat(),
        }
        with self._lock:
            self.state_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        return True

    def get_state(self) -> dict:
        """Read current state from Star-Office."""
        if not self.state_file.exists():
            return {"state": "idle", "detail": "offline"}
        return json.loads(self.state_file.read_text(encoding="utf-8"))

    # ── Agent roster ──────────────────────────────────────────────────────────

    def register_agents(self) -> bool:
        """
        Write HELEN's agent roster to Star-Office agents-state.json.
        Call once at startup to populate the pixel office crew.
        """
        if not self.agents_file.parent.exists():
            return False

        now = datetime.now().isoformat()
        agents = []
        for i, agent_def in enumerate(HELEN_AGENTS):
            agents.append({
                "agentId": agent_def["id"],
                "name": agent_def["name"],
                "state": "idle" if i > 0 else "researching",   # HELEN starts active
                "detail": agent_def["role"],
                "area": "writing" if i == 0 else "breakroom",
                "joinKey": f"helen_os_{agent_def['id']}",
                "authStatus": "approved",
                "authApprovedAt": now,
                "authExpiresAt": (datetime.now() + timedelta(days=365)).isoformat(),
                "authRejectedAt": None,
                "lastPushAt": now,
                "updated_at": now,
                "isMain": (i == 0),
                "source": "helen-os-bridge",
            })

        with self._lock:
            self.agents_file.write_text(
                json.dumps(agents, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        return True

    def push_agent_state(self, agent_id: str, state: str, detail: str = "") -> bool:
        """Update a single agent's state in the roster."""
        if not self.agents_file.exists():
            return False
        if state not in VALID_STATES:
            state = "idle"

        with self._lock:
            agents = json.loads(self.agents_file.read_text(encoding="utf-8"))
            now = datetime.now().isoformat()
            for agent in agents:
                if agent.get("agentId") == agent_id:
                    agent["state"] = state
                    agent["detail"] = detail
                    agent["area"] = STATE_AREA.get(state, "breakroom")
                    agent["lastPushAt"] = now
                    agent["updated_at"] = now
            self.agents_file.write_text(
                json.dumps(agents, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        return True

    # ── Daily memo ────────────────────────────────────────────────────────────

    def write_daily_memo(self, content: str, date: Optional[str] = None) -> Path:
        """
        Write a daily memo for Star-Office 'yesterday-memo' feature.
        Writes to memory/YYYY-MM-DD.md (the path Star-Office reads from).
        Content should be a Channel B summary — not sovereign material.
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        memo_path = MEMORY_DIR / f"{date}.md"
        header = f"# HELEN Daily Summary — {date}\n\n"
        memo_path.write_text(header + content, encoding="utf-8")
        return memo_path

    def write_session_memo(self, helen_output: str) -> Optional[Path]:
        """
        Auto-generate today's memo from a HELEN response.
        Strips sovereign language (receipts, hashes) and keeps narrative.
        Non-sovereign summary only.
        """
        lines = helen_output.split("\n")
        summary_lines = []
        for line in lines:
            # Skip raw receipt/hash lines (non-sovereign surface only)
            if any(tok in line for tok in ["cum_hash", "payload_hash", "sha256", "receipt_id"]):
                continue
            summary_lines.append(line)

        content = "\n".join(summary_lines).strip()
        if not content:
            return None
        return self.write_daily_memo(
            f"## Session Activity\n\n{content}\n\n"
            f"*Generated: {datetime.now().strftime('%H:%M:%S')} UTC — Channel C (non-sovereign)*\n"
        )

    # ── Mode detection ────────────────────────────────────────────────────────

    @staticmethod
    def detect_mode(response_text: str) -> str:
        """
        Infer Star-Office state from HELEN's response text.
        Used when the caller doesn't know the mode explicitly.
        Defaults to 'writing' if any [HER] content is present, else 'idle'.
        """
        for keywords, state in _MODE_SIGNALS:
            if any(kw.lower() in response_text.lower() for kw in keywords):
                return state
        return "writing" if "[HER]" in response_text else "idle"

    # ── Convenience: full turn lifecycle ─────────────────────────────────────

    def on_turn_start(self, user_message: str) -> None:
        """Call this before HELEN.speak() — sets UI to 'receiving' then 'researching'."""
        self.update_state("receiving", f"Reading: {user_message[:60]}...")
        # Agents: HELEN goes to researching, others idle
        self.push_agent_state("helen-main", "researching", "Processing input...")
        self.push_agent_state("hal-auditor", "researching", "Preparing audit...")

    def on_turn_end(self, response_text: str) -> None:
        """Call this after HELEN.speak() — sets UI to detected mode then idle."""
        mode = self.detect_mode(response_text)
        label = _detail_from_response(response_text, mode)
        self.update_state(mode, label)
        # Update individual agent states
        self.push_agent_state("helen-main", "idle", "Turn complete")
        if "BLOCK" in response_text:
            self.push_agent_state("hal-auditor", "error", "HAL: BLOCK issued")
        elif "WARN" in response_text:
            self.push_agent_state("hal-auditor", "idle", "HAL: WARN")
        else:
            self.push_agent_state("hal-auditor", "idle", "HAL: PASS")

    def on_task_start(self, task: str) -> None:
        """Call before run_task() pipeline — activates Planner/Worker/Critic."""
        self.update_state("executing", f"Pipeline: {task[:50]}")
        for aid, role in [
            ("planner-l1", "Planning steps..."),
            ("worker-l1", "Waiting for plan..."),
            ("critic-l1", "Waiting for draft..."),
            ("archivist-l1", "Waiting for review..."),
        ]:
            self.push_agent_state(aid, "idle", role)
        self.push_agent_state("planner-l1", "researching", "Generating step list...")

    def on_task_end(self, success: bool = True) -> None:
        """Call after run_task() completes — returns all agents to idle."""
        self.update_state("idle" if success else "error", "Pipeline complete" if success else "Pipeline error")
        for aid in ["planner-l1", "worker-l1", "critic-l1", "archivist-l1"]:
            self.push_agent_state(aid, "idle", "Standby")


# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────────

def _default_detail(state: str) -> str:
    return {
        "idle": "HELEN is standing by",
        "writing": "HELEN is drafting",
        "receiving": "HELEN is reading your message",
        "replying": "HELEN is composing a reply",
        "researching": "HELEN is retrieving context",
        "executing": "Running through governance gate",
        "syncing": "Syncing with MemoryKernel",
        "error": "Gate failure — reviewing",
    }.get(state, "HELEN OS active")


def _detail_from_response(text: str, mode: str) -> str:
    """Extract a short readable label from HELEN's response."""
    # Try to pull first [HER] body line
    for line in text.split("\n"):
        line = line.strip()
        if line and not line.startswith("[") and len(line) > 10:
            return line[:80]
    return _default_detail(mode)


# ──────────────────────────────────────────────────────────────────────────────
# Singleton — shared across FastAPI server + background threads
# ──────────────────────────────────────────────────────────────────────────────

_bridge_instance: Optional[HelenStarBridge] = None


def get_bridge() -> HelenStarBridge:
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = HelenStarBridge()
    return _bridge_instance


# ──────────────────────────────────────────────────────────────────────────────
# Standalone CLI entrypoint
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="HELEN → Star-Office state bridge")
    parser.add_argument("state", nargs="?", default="idle",
                        choices=VALID_STATES, help="State to set")
    parser.add_argument("detail", nargs="?", default="",
                        help="Detail text")
    parser.add_argument("--register-agents", action="store_true",
                        help="Register HELEN agent roster in Star-Office")
    parser.add_argument("--show", action="store_true",
                        help="Show current Star-Office state")
    args = parser.parse_args()

    bridge = get_bridge()

    if args.register_agents:
        ok = bridge.register_agents()
        print(f"✅ Agents registered → {bridge.agents_file}" if ok else "⚠️  Star-Office-UI not found")
        sys.exit(0)

    if args.show:
        state = bridge.get_state()
        print(f"Current state: {state['state']} — {state['detail']}")
        sys.exit(0)

    ok = bridge.update_state(args.state, args.detail)
    if ok:
        print(f"✅ State set: {args.state} — {args.detail or _default_detail(args.state)}")
        print(f"   Written to: {bridge.state_file}")
    else:
        print("⚠️  Star-Office-UI directory not found — is it cloned at Star-Office-UI/?")
        sys.exit(1)
