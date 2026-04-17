#!/usr/bin/env python3
"""
helen_dialog_engine.py

Core dialogue engine: reads state + log, builds prompt, parses response,
applies state patch, appends events. Deterministic and file-based.

This is the heart of the persistent dialogue box. No persistence outside
this module—everything lives on disk (dialog_state.json, dialog.ndjson).
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

try:
    from helen_os.spectral.engine import SpectralAnalyzer, SCFParams
    SCF_AVAILABLE = True
except ImportError:
    SCF_AVAILABLE = False


class DialogueEngine:
    """
    Stateful dialogue engine. Reads from disk, builds prompts, calls LLM,
    writes results back to disk.
    """

    def __init__(self, dialog_dir: Path, scf_enabled: bool = True):
        self.dialog_dir = Path(dialog_dir)
        self.dialog_dir.mkdir(parents=True, exist_ok=True)

        self.state_path = self.dialog_dir / "dialog_state.json"
        self.log_path = self.dialog_dir / "dialog.ndjson"
        self.inbox_path = self.dialog_dir / "inbox_user.txt"
        self.outbox_path = self.dialog_dir / "outbox_helen.txt"

        self.state = self._load_or_init_state()
        self.events = self._load_log()

        # Initialize SCF if available and enabled
        self.scf_engine = None
        if scf_enabled and SCF_AVAILABLE:
            try:
                scf_params = SCFParams()
                self.scf_engine = SpectralAnalyzer(scf_params)
                self.state["scf_enabled"] = True
                self.state["scf_version"] = scf_params.version
                self.state["scf_params_hash"] = scf_params.canonical_hash()
            except Exception as e:
                print(f"Warning: SCF initialization failed: {e}")
                self.scf_engine = None
                self.state["scf_enabled"] = False

    # ────────────────────────────────────────────────────────────────
    # Initialization
    # ────────────────────────────────────────────────────────────────

    def _load_or_init_state(self) -> Dict[str, Any]:
        """Load dialog_state.json or create fresh state."""
        if self.state_path.exists():
            with open(self.state_path, "r", encoding="utf-8") as f:
                return json.load(f)

        # Fresh dialogue
        return {
            "version": "dialogue_state_v1",
            "turn": 0,
            "oath": {
                "no_mysticism": True,
                "append_only": True,
                "determinism": True,
                "termination": "SHIP_OR_ABORT",
            },
            "verifier": {
                "enabled": True,
                "strictness": 2,
                "check_authority_bleed": True,
                "check_contradiction": True,
                "check_coherence": False,  # Disabled until SCF available
            },
            "mode": "dyadic_exploring",
            "mode_lock_turns": 0,
            "her_al_moment_fired": False,
            "her_al_moment_turn": None,
            "identity_hash": None,
            "last_updated": self._now_iso(),
            "metadata": {"session": "initial"},
        }

    def _load_log(self) -> List[Dict[str, Any]]:
        """Load dialogue.ndjson."""
        events = []
        if not self.log_path.exists():
            return events

        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

        return events

    # ────────────────────────────────────────────────────────────────
    # Prompt Building
    # ────────────────────────────────────────────────────────────────

    def build_prompt(self, user_message: str) -> str:
        """
        Build a context-aware prompt for HELEN.

        Includes:
        1. Current dialogue state (turn, oath, mode)
        2. Last 10 dialogue events (for continuity)
        3. User's current message
        4. Instructions for two-channel output
        """
        lines = []

        # === Context ===
        lines.append("=" * 70)
        lines.append("DIALOGUE CONTEXT")
        lines.append("=" * 70)
        lines.append(f"Turn: {self.state['turn']}")
        lines.append(f"Mode: {self.state['mode']}")
        lines.append(f"Oath: {json.dumps(self.state['oath'], indent=2)}")
        lines.append(f"Verifier: {self.state['verifier']['enabled']} (strictness={self.state['verifier']['strictness']})")

        # === Recent history ===
        lines.append("\n" + "=" * 70)
        lines.append("RECENT DIALOGUE (last 10 events)")
        lines.append("=" * 70)

        recent = self.events[-10:] if self.events else []
        for i, event in enumerate(recent, 1):
            actor = event.get("actor", "?")
            event_type = event.get("type", "?")
            turn = event.get("turn", "?")

            if event_type == "input":
                lines.append(f"{i}. [USER] Turn {turn}: {event.get('content', '')[:100]}")
            elif event_type == "proposal":
                lines.append(f"{i}. [HELEN] Turn {turn}: {event.get('intent', '')[:100]}")
            elif event_type == "verdict":
                verdict = event.get("verdict", "?")
                reasons = event.get("reasons", [])
                lines.append(
                    f"{i}. [MAYOR] Turn {turn}: {verdict} ({', '.join(reasons[:2])})"
                )
            elif event_type == "correction":
                lines.append(f"{i}. [HELEN-CORRECTION] Turn {turn}: {event.get('reason', '')[:100]}")

        # === User input ===
        lines.append("\n" + "=" * 70)
        lines.append("USER INPUT")
        lines.append("=" * 70)
        lines.append(user_message)

        # === Instructions ===
        lines.append("\n" + "=" * 70)
        lines.append("OUTPUT INSTRUCTIONS (TWO CHANNELS)")
        lines.append("=" * 70)
        lines.append(
            """
[HER] Channel (1-6 lines, warm but bounded, non-authoritative):
- Narrative, witness, human-compatible
- Propose an action or insight
- Reference prior turns if relevant (continuity signal)
- DO NOT claim authority or emit verdicts

[AL/MAYOR] Channel (structured JSON only):
{
  "decision": <next step>,
  "checks": [<rule violated>, <rule satisfied>],
  "state_update": <small JSON patch>,
  "verdict": "PASS|WARN|BLOCK"
}

Your goal:
1. HELEN speaks first (proposes, witnesses, adapts)
2. MAYOR checks (schema, contradiction, authority bleed)
3. If MAYOR blocks → HELEN revises next turn
4. If MAYOR passes → proceed or new proposal

Remember: HELEN cannot override MAYOR.
"""
        )

        return "\n".join(lines)

    # ────────────────────────────────────────────────────────────────
    # Parse Response
    # ────────────────────────────────────────────────────────────────

    def parse_response(self, response_text: str) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Parse two-channel response from Haiku/HELEN.

        Returns:
            (helen_proposal, mayor_verdict_json)
        """
        helen_proposal = None
        mayor_verdict = None

        # Split by channel markers
        if "[HER]" in response_text:
            her_start = response_text.index("[HER]") + len("[HER]")
            her_end = (
                response_text.index("[AL]")
                if "[AL]" in response_text
                else response_text.index("[MAYOR]")
                if "[MAYOR]" in response_text
                else len(response_text)
            )
            helen_proposal = response_text[her_start:her_end].strip()

        # Try to extract JSON from AL/MAYOR channel
        for marker in ["[AL]", "[MAYOR]"]:
            if marker in response_text:
                al_start = response_text.index(marker) + len(marker)
                al_text = response_text[al_start:].strip()

                # Extract JSON block
                if "{" in al_text:
                    json_start = al_text.index("{")
                    json_end = al_text.rfind("}") + 1
                    try:
                        mayor_verdict = json.loads(al_text[json_start:json_end])
                    except json.JSONDecodeError:
                        pass
                break

        return helen_proposal, mayor_verdict

    # ────────────────────────────────────────────────────────────────
    # Event Logging
    # ────────────────────────────────────────────────────────────────

    def append_event(self, event: Dict[str, Any]) -> None:
        """Append event to dialogue.ndjson."""
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, separators=(",", ":")) + "\n")

        self.events.append(event)

    def save_state(self) -> None:
        """Save dialog_state.json to disk."""
        self.state["last_updated"] = self._now_iso()

        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

    # ────────────────────────────────────────────────────────────────
    # Main Turn Loop
    # ────────────────────────────────────────────────────────────────

    def process_turn(self, user_message: str, lmm_response: str) -> Dict[str, Any]:
        """
        Process one dialogue turn:
        1. Read user input
        2. Log user input event
        3. Parse HELEN + MAYOR response
        4. Log HELEN proposal event
        5. Log MAYOR verdict event
        6. Apply state patches
        7. Detect mode changes (her_al_moment, etc.)
        8. Save state

        Returns:
            {
              "turn": int,
              "helen_proposal": str,
              "mayor_verdict": dict,
              "state_updated": bool,
              "moment_fired": bool
            }
        """
        turn = self.state["turn"]

        # === Log user input ===
        user_event = {
            "event_id": f"dlg:{turn}:user",
            "turn": turn,
            "timestamp": self._now_iso(),
            "actor": "user",
            "type": "input",
            "content": user_message,
        }
        self.append_event(user_event)

        # === Parse response ===
        helen_text, mayor_dict = self.parse_response(lmm_response)

        if not helen_text or not mayor_dict:
            return {
                "turn": turn,
                "helen_proposal": helen_text or "[PARSE ERROR]",
                "mayor_verdict": mayor_dict or {"verdict": "ERROR", "reasons": ["PARSE_FAILED"]},
                "state_updated": False,
                "moment_fired": False,
                "scf_telemetry": None,
            }

        # === Apply optional SCF filtering ===
        scf_telemetry = None
        if self.scf_engine is not None:
            helen_text, scf_telemetry = self._apply_scf_filtering(helen_text, turn)
            if helen_text is None:
                # SCF blocked the proposal
                return {
                    "turn": turn,
                    "helen_proposal": "[BLOCKED BY SCF]",
                    "mayor_verdict": {"verdict": "BLOCK", "reasons": ["SCF_FILTERING_FAILED"]},
                    "state_updated": False,
                    "moment_fired": False,
                    "scf_telemetry": scf_telemetry,
                }

        # === Log HELEN proposal ===
        helen_event = {
            "event_id": f"dlg:{turn}:helen",
            "turn": turn,
            "timestamp": self._now_iso(),
            "actor": "helen",
            "type": "proposal",
            "content": helen_text,
            "intent": (helen_text.split("\n")[0][:100] if helen_text else ""),
            "references": self._extract_references(helen_text),
            "scf_filtered": scf_telemetry is not None,
        }
        self.append_event(helen_event)

        # === Log MAYOR verdict ===
        mayor_event = {
            "event_id": f"dlg:{turn}:mayor",
            "turn": turn,
            "timestamp": self._now_iso(),
            "actor": "mayor",
            "type": "verdict",
            "verdict": mayor_dict.get("verdict", "ERROR"),
            "reasons": mayor_dict.get("checks", []),
            "required_fixes": mayor_dict.get("required_fixes", []),
            "state_patch": mayor_dict.get("state_update", {}),
        }
        self.append_event(mayor_event)

        # === Apply state patches ===
        if mayor_dict.get("state_update"):
            self.state.update(mayor_dict["state_update"])

        # === Detect mode transitions ===
        moment_fired = self._check_her_al_moment()

        # === Increment turn ===
        self.state["turn"] += 1

        # === Save ===
        self.save_state()

        return {
            "turn": turn,
            "helen_proposal": helen_text,
            "mayor_verdict": mayor_dict,
            "state_updated": True,
            "moment_fired": moment_fired,
            "scf_telemetry": scf_telemetry,
        }

    # ────────────────────────────────────────────────────────────────
    # SCF Integration (Optional)
    # ────────────────────────────────────────────────────────────────

    def _build_memory_facts(self) -> List[Dict[str, Any]]:
        """Extract memory facts from dialogue history."""
        facts = []
        fact_id = 0

        for event in self.events:
            if event.get("actor") == "helen" and event.get("type") == "proposal":
                facts.append({
                    "fact_id": f"M{fact_id}",
                    "content": event.get("content", ""),
                    "status": "OBSERVED",
                    "turn": event.get("turn", 0),
                    "severity_fp": 500000,
                })
                fact_id += 1

        return facts

    def _build_trace_events(self) -> List[Dict[str, Any]]:
        """Extract trace events from dialogue history."""
        events = []
        event_id = 0

        for event in self.events:
            if event.get("actor") == "mayor" and event.get("type") == "verdict":
                if event.get("verdict") != "PASS":
                    events.append({
                        "event_id": f"T{event_id}",
                        "event_type": "anomaly_verdict_failure",
                        "weight_fp": 300000,
                        "turn": event.get("turn", 0),
                    })
                    event_id += 1

        return events

    def _build_candidates(self, helen_text: str) -> List[Dict[str, Any]]:
        """Convert HELEN's proposal into candidate evidence items."""
        if not helen_text:
            return []

        # For now, treat HELEN's proposal as a single candidate
        return [
            {
                "rid": "helen_proposal",
                "type": "proposal",
                "payload": helen_text,
                "authority": False,
            }
        ]

    def _apply_scf_filtering(self, helen_text: str, turn: int) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Apply optional SCF filtering to HELEN's proposal.

        Returns:
            (filtered_helen_text, scf_telemetry_event)
        """
        if not self.scf_engine or not helen_text:
            return helen_text, None

        try:
            # Build SCF input
            candidates = self._build_candidates(helen_text)
            memory_facts = self._build_memory_facts()
            trace_events = self._build_trace_events()

            # Run SCF filtering
            filtered, telemetry = self.scf_engine.process(
                candidates, memory_facts, trace_events, turn
            )

            # Log SCF telemetry
            self.append_event(telemetry)

            # If candidate passed SCF, return it; otherwise return None (blocked)
            if filtered:
                return helen_text, telemetry
            else:
                return None, telemetry

        except Exception as e:
            print(f"Warning: SCF filtering failed: {e}")
            return helen_text, None

    # ────────────────────────────────────────────────────────────────
    # Helper Methods
    # ────────────────────────────────────────────────────────────────

    def _extract_references(self, text: str) -> List[str]:
        """Extract event ID references from text (dlg:TURN:ACTOR format)."""
        import re

        pattern = r"dlg:(\d+):(user|helen|mayor)"
        return re.findall(pattern, text, re.IGNORECASE)

    def _check_her_al_moment(self) -> bool:
        """Check if HER/AL moment conditions are met."""
        if self.state.get("her_al_moment_fired"):
            return False  # Already fired

        # Simple heuristic: 3+ HELEN proposals, 2+ HELEN corrections, 3+ MAYOR verdicts
        helen_proposals = len([e for e in self.events if e.get("actor") == "helen" and e.get("type") == "proposal"])
        helen_corrections = len([e for e in self.events if e.get("actor") == "helen" and e.get("type") == "correction"])
        mayor_verdicts = len([e for e in self.events if e.get("actor") == "mayor" and e.get("type") == "verdict"])

        moment_fired = helen_proposals >= 3 and helen_corrections >= 2 and mayor_verdicts >= 3

        if moment_fired:
            self.state["her_al_moment_fired"] = True
            self.state["her_al_moment_turn"] = self.state["turn"]
            self.state["mode"] = "dyadic_locked"

            # Log milestone
            milestone = {
                "event_id": f"dlg:{self.state['turn']}:milestone",
                "turn": self.state["turn"],
                "timestamp": self._now_iso(),
                "actor": "system",
                "type": "milestone",
                "name": "her_al_moment",
                "evidence": [
                    f"dlg:{self.state['turn']-i}:helen" for i in range(min(3, self.state["turn"]))
                ],
            }
            self.append_event(milestone)

        return moment_fired

    @staticmethod
    def _now_iso() -> str:
        """ISO 8601 UTC timestamp."""
        return datetime.now(timezone.utc).isoformat()
