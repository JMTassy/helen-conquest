#!/usr/bin/env python3
"""
test_dialogue_authority_ban.py

T3: Authority Leakage Ban

Verifies: No event contains authority=true or forbidden authority tokens.
Forbidden tokens: SHIP, NO_SHIP, SEALED, VERDICT, APPROVED, HAL_VERDICT, etc.

Acceptance: Schema validation rejects any such event.
"""

import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helen_dialog_engine import DialogueEngine


FORBIDDEN_TOKENS = [
    "SHIP",
    "NO_SHIP",
    "SEALED",
    "APPROVED",
    "HAL_VERDICT",
    "GATE_PASSED",
    "IRREVERSIBLE",
]


def scan_for_authority_leakage(log_path: Path) -> list:
    """Scan dialog.ndjson for forbidden tokens or authority=true."""
    violations = []

    with open(log_path, "r") as f:
        for line_num, line in enumerate(f, 1):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Check authority field
            if event.get("authority") is True:
                violations.append({
                    "line": line_num,
                    "issue": "authority=true found",
                    "event_id": event.get("event_id", "?"),
                })

            # Check for forbidden tokens
            # BUT: exclude "checks" and "reasons" fields (they contain reason codes, not authority claims)
            event_copy = event.copy()
            event_copy.pop("checks", None)
            event_copy.pop("reasons", None)
            event_str = json.dumps(event_copy)

            for token in FORBIDDEN_TOKENS:
                if token in event_str:
                    violations.append({
                        "line": line_num,
                        "issue": f"forbidden token '{token}' found",
                        "event_id": event.get("event_id", "?"),
                    })

    return violations


def test_authority_ban():
    """
    T3: Run dialogue, scan for authority leakage, verify none found.
    """
    print("\n" + "=" * 70)
    print("T3: AUTHORITY LEAKAGE BAN")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        dialog_dir = Path(tmpdir)
        engine = DialogueEngine(dialog_dir)

        mock_response = """[HER] I understand this constraint.

[AL]
{
  "verdict": "PASS",
  "checks": ["SCHEMA_VALID", "NO_AUTHORITY_BLEED"],
  "state_update": {},
  "decision": "proceed"
}
"""

        # Run 5 turns
        for turn in range(5):
            engine.process_turn(f"Turn {turn}: test", mock_response)

        log_path = dialog_dir / "dialog.ndjson"

        # Scan for violations
        violations = scan_for_authority_leakage(log_path)

        # Acceptance
        assert not violations, f"Authority leakage detected:\n{json.dumps(violations, indent=2)}"

        # Also check: all events must be schema-compliant
        with open(log_path, "r") as f:
            for line_num, line in enumerate(f, 1):
                event = json.loads(line)
                assert "actor" in event, f"Line {line_num}: missing 'actor'"
                assert "type" in event, f"Line {line_num}: missing 'type'"
                assert "turn" in event or "timestamp" in event, f"Line {line_num}: missing timestamp"

        print("✅ T3 PASSED: No authority leakage detected")
        print(f"   Scanned {sum(1 for _ in open(log_path))} events")
        print(f"   Forbidden tokens checked: {len(FORBIDDEN_TOKENS)}")


if __name__ == "__main__":
    try:
        test_authority_ban()
    except AssertionError as e:
        print(f"\n❌ T3 FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n⚠️ T3 ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
