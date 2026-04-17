#!/usr/bin/env python3
"""
test_dialogue_appendonly_discipline.py

T2: Append-Only Discipline

Verifies: dialog.ndjson is never rewritten, only appended.
Acceptance: file length strictly increases; no line mutation.
"""

import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helen_dialog_engine import DialogueEngine


def test_appendonly_discipline():
    """
    T2: Add turns, verify file only grows (never shrinks or rewrites lines).
    """
    print("\n" + "=" * 70)
    print("T2: APPEND-ONLY DISCIPLINE")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        dialog_dir = Path(tmpdir)
        engine = DialogueEngine(dialog_dir)
        log_path = dialog_dir / "dialog.ndjson"

        # Fixed mock response (no format strings)
        mock_response = """[HER] Response processed.

[AL]
{
  "verdict": "PASS",
  "checks": ["OK"],
  "state_update": {},
  "decision": "continue"
}
"""

        file_sizes = []
        event_counts = []

        # Turn 1
        engine.process_turn("Turn 1 input", mock_response)
        size1 = log_path.stat().st_size
        with open(log_path, "r") as f:
            count1 = len(f.readlines())
        file_sizes.append(size1)
        event_counts.append(count1)
        print(f"After turn 1: size={size1}, events={count1}")

        # Save state for line-by-line verification
        with open(log_path, "r") as f:
            lines_at_1 = f.readlines()

        # Turn 2
        engine.process_turn("Turn 2 input", mock_response)
        size2 = log_path.stat().st_size
        with open(log_path, "r") as f:
            count2 = len(f.readlines())
        file_sizes.append(size2)
        event_counts.append(count2)
        print(f"After turn 2: size={size2}, events={count2}")

        # Verify no rewrite (first lines unchanged)
        with open(log_path, "r") as f:
            lines_at_2 = f.readlines()
        for i, (line1, line2) in enumerate(zip(lines_at_1, lines_at_2)):
            assert line1 == line2, f"Line {i} mutated between turns"

        # Turn 3
        engine.process_turn("Turn 3 input", mock_response)
        size3 = log_path.stat().st_size
        with open(log_path, "r") as f:
            count3 = len(f.readlines())
        file_sizes.append(size3)
        event_counts.append(count3)
        print(f"After turn 3: size={size3}, events={count3}")

        # Acceptance criteria
        assert size1 < size2 < size3, f"File size must strictly increase: {size1} < {size2} < {size3}"
        assert count1 < count2 < count3, f"Event count must strictly increase: {count1} < {count2} < {count3}"

        print("\n✅ T2 PASSED: Append-only discipline verified")
        print(f"   File growth: {size1} → {size2} → {size3} bytes")
        print(f"   Event growth: {count1} → {count2} → {count3} events")


if __name__ == "__main__":
    try:
        test_appendonly_discipline()
    except AssertionError as e:
        print(f"\n❌ T2 FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n⚠️ T2 ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
