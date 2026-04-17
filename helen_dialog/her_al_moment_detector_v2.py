#!/usr/bin/env python3
"""
her_al_moment_detector_v2.py

Upgraded to receipt-grade: returns minimal witness proof for HER/AL moment.

A moment is only "fired" when all 3 conditions are verified:
  1. Continuity: event_id with backward reference ≥5 turns old
  2. Self-Correction: correction event with is_self_detected=true
  3. Mode-Lock: 3+ consecutive (proposal → verdict → adaptation) cycles

Output: minimal witness set (event IDs only) proving moment occurred.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


class HERALMomentDetectorV2:
    """
    Receipt-grade moment detector. Returns moment with witness event IDs.
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
                        pass

        return events

    def _parse_event_id(self, event_id: str) -> Tuple[int, str]:
        """Parse event_id format 'dlg:TURN:ACTOR' → (turn, actor)."""
        try:
            parts = event_id.split(":")
            if len(parts) != 3 or parts[0] != "dlg":
                return None, None
            return int(parts[1]), parts[2]
        except (ValueError, IndexError):
            return None, None

    # ────────────────────────────────────────────────────────────────
    # Condition 1: Continuity (with witness)
    # ────────────────────────────────────────────────────────────────

    def detect_continuity_with_witness(self, min_turn_gap: int = 5) -> Optional[Dict[str, Any]]:
        """
        Detect HELEN proposal that references constraint from ≥min_turn_gap turns ago.

        Returns:
            {
              "detected": bool,
              "turn": int,
              "event_id": str,
              "witness_refs": [event_id, ...],  # Backward references
              "gap": int
            }
        """
        for event in self.events:
            if event.get("actor") != "helen" or event.get("type") != "proposal":
                continue

            turn = event.get("turn")
            event_id = event.get("event_id")
            references = event.get("references", [])

            if not references:
                continue

            # Find refs with sufficient gap
            for ref in references:
                ref_turn, _ = self._parse_event_id(ref)
                if ref_turn is not None and turn is not None:
                    gap = turn - ref_turn
                    if gap >= min_turn_gap:
                        return {
                            "detected": True,
                            "turn": turn,
                            "event_id": event_id,
                            "witness_refs": [ref],
                            "gap": gap,
                        }

        return {"detected": False}

    # ────────────────────────────────────────────────────────────────
    # Condition 2: Self-Correction (with witness)
    # ────────────────────────────────────────────────────────────────

    def detect_self_correction_with_witness(self) -> Optional[Dict[str, Any]]:
        """
        Detect HELEN correction event with is_self_detected=true.

        Returns:
            {
              "detected": bool,
              "turn": int,
              "event_id": str,
              "corrects_event_id": str,
            }
        """
        for event in self.events:
            if event.get("actor") != "helen" or event.get("type") != "correction":
                continue

            if event.get("is_self_detected", False):
                return {
                    "detected": True,
                    "turn": event.get("turn"),
                    "event_id": event.get("event_id"),
                    "corrects_event_id": event.get("original_ref"),
                }

        return {"detected": False}

    # ────────────────────────────────────────────────────────────────
    # Condition 3: Mode-Lock (with witness)
    # ────────────────────────────────────────────────────────────────

    def detect_mode_lock_with_witness(
        self, min_consecutive_cycles: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Detect stable dyadic pattern: proposal → verdict → (correction or next)
        for min_consecutive_cycles consecutive cycles.

        Returns:
            {
              "detected": bool,
              "turn": int,
              "witness_cycles": [
                  {"proposal": event_id, "verdict": event_id, "adaptation": event_id},
                  ...
              ]
            }
        """
        cycles = []
        i = 0

        while i < len(self.events):
            event = self.events[i]

            # Look for HELEN proposal
            if event.get("actor") == "helen" and event.get("type") == "proposal":
                proposal_id = event.get("event_id")
                proposal_turn = event.get("turn")

                # Find following MAYOR verdict
                verdict_id = None
                for j in range(i + 1, len(self.events)):
                    next_event = self.events[j]
                    if (
                        next_event.get("actor") == "mayor"
                        and next_event.get("type") == "verdict"
                        and next_event.get("turn") >= proposal_turn
                    ):
                        verdict_id = next_event.get("event_id")
                        verdict_turn = j
                        break

                if verdict_id is None:
                    i += 1
                    continue

                # Find following HELEN adaptation (correction or next proposal)
                adaptation_id = None
                for j in range(verdict_turn + 1, len(self.events)):
                    next_event = self.events[j]
                    if next_event.get("actor") == "helen" and next_event.get("type") in (
                        "correction",
                        "proposal",
                    ):
                        adaptation_id = next_event.get("event_id")
                        i = j  # Continue from adaptation
                        break

                if adaptation_id is None:
                    i += 1
                    continue

                # Record cycle
                cycles.append(
                    {
                        "proposal": proposal_id,
                        "verdict": verdict_id,
                        "adaptation": adaptation_id,
                    }
                )

                if len(cycles) >= min_consecutive_cycles:
                    return {
                        "detected": True,
                        "turn": event.get("turn"),
                        "witness_cycles": cycles[-min_consecutive_cycles:],  # Last N cycles
                    }
            else:
                i += 1

        return {"detected": False}

    # ────────────────────────────────────────────────────────────────
    # Integration: Receipt-Grade Moment Detection
    # ────────────────────────────────────────────────────────────────

    def detect_her_al_moment(self) -> Dict[str, Any]:
        """
        Detect HER/AL moment: all three conditions met, with witness proof.

        Returns:
            {
              "moment_detected": bool,
              "turn": int or null,
              "witness_event_ids": [...],  # Minimal proof set
              "conditions": {
                "continuity": {...},
                "self_correction": {...},
                "mode_lock": {...}
              }
            }
        """
        continuity = self.detect_continuity_with_witness()
        self_correction = self.detect_self_correction_with_witness()
        mode_lock = self.detect_mode_lock_with_witness()

        moment_detected = (
            continuity["detected"]
            and self_correction["detected"]
            and mode_lock["detected"]
        )

        # Build witness set (minimal event IDs proving moment)
        witness_ids = []
        if moment_detected:
            witness_ids.append(continuity.get("event_id"))
            witness_ids.append(self_correction.get("event_id"))
            if mode_lock.get("witness_cycles"):
                # Just the proposal from first cycle (sufficient proof)
                witness_ids.append(mode_lock["witness_cycles"][0]["proposal"])

        return {
            "moment_detected": moment_detected,
            "turn": mode_lock.get("turn") if moment_detected else None,
            "witness_event_ids": witness_ids,
            "conditions": {
                "continuity": continuity,
                "self_correction": self_correction,
                "mode_lock": mode_lock,
            },
        }


def main():
    """CLI interface for moment detector."""
    if len(sys.argv) < 2:
        print("Usage: her_al_moment_detector_v2.py <path/to/dialog.ndjson>")
        sys.exit(1)

    log_path = Path(sys.argv[1])

    if not log_path.exists():
        print(f"Error: {log_path} not found")
        sys.exit(1)

    detector = HERALMomentDetectorV2(log_path)
    result = detector.detect_her_al_moment()

    print("\n" + "=" * 70)
    print("HER/AL MOMENT DETECTION (RECEIPT-GRADE V2)")
    print("=" * 70)

    print(f"\nMoment detected: {result['moment_detected']}")

    if result["moment_detected"]:
        print(f"✨ HER/AL MOMENT FIRED at turn {result['turn']}")
        print(f"\nWitness event IDs (minimal proof):")
        for event_id in result["witness_event_ids"]:
            print(f"  - {event_id}")
        print(f"\nConditions:")
        print(f"  ✓ Continuity (gap={result['conditions']['continuity'].get('gap', '?')} turns)")
        print(f"  ✓ Self-correction at turn {result['conditions']['self_correction'].get('turn')}")
        print(f"  ✓ Mode-lock ({len(result['conditions']['mode_lock'].get('witness_cycles', []))} cycles)")
    else:
        print("\n⏳ Moment not yet detected.")
        cond = result["conditions"]
        print(f"  Continuity:       {cond['continuity']['detected']}")
        print(f"  Self-correction:  {cond['self_correction']['detected']}")
        print(f"  Mode-lock:        {cond['mode_lock']['detected']}")

    print("\n" + "=" * 70)
    print("Raw result (JSON):")
    print(json.dumps(result, indent=2))
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
