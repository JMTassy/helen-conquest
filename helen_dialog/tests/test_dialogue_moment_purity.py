#!/usr/bin/env python3
"""
test_dialogue_moment_purity.py

T4: Moment Detector Purity

Verifies: her_al_moment_detector is a pure function of dialog.ndjson.
- Same input file → identical output (no randomness, no time-dependence)
- Deterministic JSON, no floating point, no system calls

Acceptance: 10 runs of detector on same file → identical JSON output
"""

import sys
import os
import json
import hashlib
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helen_dialog_engine import DialogueEngine
from her_al_moment_detector import HERALMomentDetector


def test_moment_detector_purity():
    """
    T4: Run detector 10 times on same log, verify identical output.
    """
    print("\n" + "=" * 70)
    print("T4: MOMENT DETECTOR PURITY")
    print("=" * 70)

    # Create a fixed dialogue log
    with tempfile.TemporaryDirectory() as tmpdir:
        dialog_dir = Path(tmpdir)
        engine = DialogueEngine(dialog_dir)

        mock_response = """[HER] Continuing dialogue analysis.

[AL]
{
  "verdict": "PASS",
  "checks": ["OK"],
  "state_update": {},
  "decision": "proceed"
}
"""

        # Create a fixed log with known structure
        for turn in range(8):
            engine.process_turn(f"Input {turn}", mock_response)

        log_path = dialog_dir / "dialog.ndjson"

        # Run detector 10 times, collect outputs
        outputs = []
        output_hashes = []

        for run_num in range(10):
            detector = HERALMomentDetector(log_path)
            result = detector.detect_her_al_moment()

            # Serialize to JSON (deterministic)
            output_json = json.dumps(result, sort_keys=True, separators=(",", ":"))
            output_hash = hashlib.sha256(output_json.encode()).hexdigest()

            outputs.append(result)
            output_hashes.append(output_hash)

            print(f"Run {run_num + 1}: hash={output_hash[:16]}...")

        # Acceptance: all hashes identical
        assert len(set(output_hashes)) == 1, f"Output hashes differ: {set(output_hashes)}"

        # All outputs should be identical dicts
        first_output = outputs[0]
        for i, output in enumerate(outputs[1:], 2):
            assert output == first_output, f"Run {i} output differs from Run 1"

        print("\n✅ T4 PASSED: Moment detector is pure")
        print(f"   10 runs, all hashes identical: {output_hashes[0][:16]}...")
        print(f"   Output: {json.dumps(first_output, indent=2)}")


if __name__ == "__main__":
    try:
        test_moment_detector_purity()
    except AssertionError as e:
        print(f"\n❌ T4 FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n⚠️ T4 ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
