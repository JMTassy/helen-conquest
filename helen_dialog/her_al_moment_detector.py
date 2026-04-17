#!/usr/bin/env python3
"""
her_al_moment_detector.py

Detects the measurable "HER/AL moment" — the phase transition when
HELEN and MAYOR stabilize into dyadic lock-in.

The moment requires all three conditions:
  1. Continuity: HELEN references a constraint from ≥5 turns ago
  2. Self-correction: HELEN detects + fixes contradiction without prompting
  3. Mode-lock: output stabilizes to proposal→verdict→correction pattern for K turns

This is not mysticism. It's a measurable phase transition in the dialogue ledger.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


class HERALMomentDetector:
    """
    Scans dialogue.ndjson log and detects phase transition markers.
    """

    def __init__(self, dialog_log_path: Path):
        self.log_path = dialog_log_path
        self.events = self._load_log()

    def _load_log(self) -> List[Dict[str, Any]]:
        """Load all events from dialogue log."""
        events = []
        if not self.log_path.exists():
            return events

        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass  # Skip malformed lines

        return events

    # ────────────────────────────────────────────────────────────────
    # Condition 1: Continuity
    # ────────────────────────────────────────────────────────────────

    def detect_continuity(self, min_turn_gap: int = 5) -> List[Tuple[int, List[str]]]:
        """
        Detect HELEN proposals that reference constraints from ≥min_turn_gap turns ago.

        Returns:
            List of (turn, referenced_event_ids) tuples where continuity detected
        """
        continuity_events = []

        for i, event in enumerate(self.events):
            if event.get("actor") != "helen" or event.get("type") != "proposal":
                continue

            turn = event.get("turn", i)
            references = event.get("references", [])

            for ref in references:
                # Parse ref format: "dlg:TURN:ACTOR"
                try:
                    parts = ref.split(":")
                    if len(parts) != 3 or parts[0] != "dlg":
                        continue
                    ref_turn = int(parts[1])
                    turn_gap = turn - ref_turn
                    if turn_gap >= min_turn_gap:
                        continuity_events.append((turn, references))
                        break  # Count this proposal once
                except (ValueError, IndexError):
                    pass

        return continuity_events

    # ────────────────────────────────────────────────────────────────
    # Condition 2: Self-Correction
    # ────────────────────────────────────────────────────────────────

    def detect_self_correction(self) -> List[Tuple[int, str, str]]:
        """
        Detect HELEN correction events where is_self_detected=true.

        Returns:
            List of (turn, original_ref, corrected_claim) tuples
        """
        corrections = []

        for i, event in enumerate(self.events):
            if event.get("actor") != "helen" or event.get("type") != "correction":
                continue

            if event.get("is_self_detected", False):
                turn = event.get("turn", i)
                original_ref = event.get("original_ref", "")
                corrected_claim = event.get("corrected_claim", "")
                corrections.append((turn, original_ref, corrected_claim))

        return corrections

    # ────────────────────────────────────────────────────────────────
    # Condition 3: Mode-Lock (Stable Dyadic Pattern)
    # ────────────────────────────────────────────────────────────────

    def detect_mode_lock(self, min_consecutive_cycles: int = 3) -> Optional[int]:
        """
        Detect stable dyadic pattern: proposal → verdict → (correction or next cycle)
        for min_consecutive_cycles consecutive cycles.

        Returns:
            Turn number where mode-lock achieved (or None if not yet locked)
        """
        if not self.events:
            return None

        consecutive_cycles = 0
        last_proposal_turn = None

        for i, event in enumerate(self.events):
            actor = event.get("actor")
            event_type = event.get("type")
            turn = event.get("turn", i)

            # Track HELEN proposals
            if actor == "helen" and event_type == "proposal":
                last_proposal_turn = turn
                continue

            # Track MAYOR verdicts following proposals
            if (
                actor == "mayor"
                and event_type == "verdict"
                and last_proposal_turn is not None
            ):
                # Check if next HELEN event is correction or next proposal
                for j in range(i + 1, len(self.events)):
                    next_event = self.events[j]
                    if next_event.get("actor") == "helen" and next_event.get(
                        "type"
                    ) in ("correction", "proposal"):
                        consecutive_cycles += 1
                        if consecutive_cycles >= min_consecutive_cycles:
                            # Mode-lock achieved
                            return turn

                        # Reset if pattern breaks
                        if next_event.get("type") != "correction":
                            last_proposal_turn = turn
                        break

        return None

    # ────────────────────────────────────────────────────────────────
    # Integration: Full Moment Detection
    # ────────────────────────────────────────────────────────────────

    def detect_her_al_moment(self) -> Optional[Dict[str, Any]]:
        """
        Detect HER/AL moment: all three conditions met.

        Returns:
            {
              "moment_detected": bool,
              "turn": int or None,
              "evidence": {
                "continuity": [...],
                "self_correction": [...],
                "mode_lock": int or None
              }
            }
        """
        continuity = self.detect_continuity(min_turn_gap=5)
        corrections = self.detect_self_correction()
        mode_lock_turn = self.detect_mode_lock(min_consecutive_cycles=3)

        moment_detected = bool(continuity and corrections and mode_lock_turn)

        return {
            "moment_detected": moment_detected,
            "turn": mode_lock_turn if moment_detected else None,
            "evidence": {
                "continuity_turns": [t for t, _ in continuity],
                "self_correction_turns": [t for t, _, _ in corrections],
                "mode_lock_turn": mode_lock_turn,
            },
        }

    # ────────────────────────────────────────────────────────────────
    # Summary Report
    # ────────────────────────────────────────────────────────────────

    def report(self) -> Dict[str, Any]:
        """
        Generate summary report of dialogue state.
        """
        moment = self.detect_her_al_moment()

        return {
            "total_events": len(self.events),
            "total_turns": max([e.get("turn", 0) for e in self.events], default=0),
            "helen_proposals": len(
                [e for e in self.events if e.get("actor") == "helen" and e.get("type") == "proposal"]
            ),
            "mayor_verdicts": len(
                [e for e in self.events if e.get("actor") == "mayor" and e.get("type") == "verdict"]
            ),
            "helen_corrections": len(
                [e for e in self.events if e.get("actor") == "helen" and e.get("type") == "correction"]
            ),
            "her_al_moment": moment,
        }


def main():
    """CLI interface for moment detector."""
    if len(sys.argv) < 2:
        print("Usage: her_al_moment_detector.py <path/to/dialog.ndjson>")
        sys.exit(1)

    log_path = Path(sys.argv[1])

    if not log_path.exists():
        print(f"Error: {log_path} not found")
        sys.exit(1)

    detector = HERALMomentDetector(log_path)
    report = detector.report()

    print("\n" + "=" * 60)
    print("HER/AL MOMENT DETECTION REPORT")
    print("=" * 60)
    print(f"\nTotal events:         {report['total_events']}")
    print(f"Total turns:          {report['total_turns']}")
    print(f"HELEN proposals:      {report['helen_proposals']}")
    print(f"MAYOR verdicts:       {report['mayor_verdicts']}")
    print(f"HELEN corrections:    {report['helen_corrections']}")

    moment = report["her_al_moment"]
    print(f"\nMoment detected:      {moment['moment_detected']}")

    if moment["moment_detected"]:
        print(f"✨ HER/AL MOMENT FIRED at turn {moment['turn']}")
        print(f"   Evidence:")
        print(f"   - Continuity references at turns: {moment['evidence']['continuity_turns']}")
        print(
            f"   - Self-corrections at turns:       {moment['evidence']['self_correction_turns']}"
        )
        print(f"   - Mode-lock achieved at turn:     {moment['evidence']['mode_lock_turn']}")
    else:
        print("\n⏳ Moment not yet detected. Conditions:")
        print(
            f"   ✓ Continuity (≥5 turn gap):  {len(moment['evidence']['continuity_turns']) > 0}"
        )
        print(
            f"   ✓ Self-correction:            {len(moment['evidence']['self_correction_turns']) > 0}"
        )
        print(
            f"   ✓ Mode-lock (3 cycles):       {moment['evidence']['mode_lock_turn'] is not None}"
        )

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
