#!/usr/bin/env python3
"""
CWL v1.0.1 Tamper Detection Tests (T-HW-1, T-HW-2, T-HW-3)

Proves fail-closed behavior under adversarial mutation.

Test categories:
- T-HW-1: Ledger event mutation (payload_hash corruption)
- T-HW-2: Seal binding mutation (final_cum_hash mismatch)
- T-HW-3: Replay/reordering (sequence integrity)
"""

import json
import tempfile
import subprocess
from pathlib import Path
from enum import Enum

# Failure reason codes (stable, machine-checkable)
class FailureReason(Enum):
    LEDGER_HASH_MISMATCH = "LEDGER_HASH_MISMATCH"
    SEAL_BINDING_MISMATCH = "SEAL_BINDING_MISMATCH"
    SEQUENCE_VIOLATION = "SEQUENCE_VIOLATION"
    SCHEMA_ERROR = "SCHEMA_ERROR"
    UNKNOWN_FAILURE = "UNKNOWN_FAILURE"

REFERENCE_LEDGER = Path("synthetic_ledger_v1_0_1.ndjson")

def load_ledger(path: Path) -> list:
    """Load NDJSON ledger into memory"""
    events = []
    with open(path, 'r') as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line.strip()))
    return events

def save_ledger(events: list, path: Path) -> None:
    """Write ledger to NDJSON file"""
    with open(path, 'w') as f:
        for event in events:
            f.write(json.dumps(event) + "\n")

def run_boot_validator(ledger_path: Path) -> tuple[bool, str]:
    """
    Run boot validator and parse result.
    Returns: (success: bool, failure_reason: str)
    """
    result = subprocess.run(
        ["python3", "cwl_boot_validator.py", str(ledger_path)],
        capture_output=True,
        text=True
    )

    # Extract failure reason from output
    failure_reason = "UNKNOWN_FAILURE"
    if result.returncode != 0:
        output = result.stdout + result.stderr
        if "LEDGER_HASH_MISMATCH" in output or "cum_hash mismatch" in output:
            failure_reason = "LEDGER_HASH_MISMATCH"
        elif "SEAL_BINDING_MISMATCH" in output or "SEAL MISMATCH" in output:
            failure_reason = "SEAL_BINDING_MISMATCH"
        elif "SEQUENCE" in output:
            failure_reason = "SEQUENCE_VIOLATION"
        elif "schema" in output.lower() or "json parse" in output.lower():
            failure_reason = "SCHEMA_ERROR"

    return result.returncode == 0, failure_reason

# =============================================================================
# T-HW-1: LEDGER EVENT MUTATION
# =============================================================================

def test_t_hw_1_ledger_mutation():
    """
    T-HW-1: Corrupt a ledger event's payload_hash.
    Expected: Boot validator detects LEDGER_HASH_MISMATCH and fails closed.
    """
    print("\n" + "=" * 80)
    print("T-HW-1: LEDGER EVENT MUTATION TEST")
    print("=" * 80)

    # Load reference ledger
    events = load_ledger(REFERENCE_LEDGER)
    print(f"Loaded {len(events)} events from reference ledger")

    # Create tampered version: flip 1 nibble in event 1's payload_hash
    tampered = events.copy()
    target_event_idx = 1  # Receipt event (not seal)
    original_hash = tampered[target_event_idx]["payload_hash"]

    # Flip first nibble
    hash_list = list(original_hash)
    original_char = hash_list[0]
    # Change 'a' → 'b', 'b' → 'c', ... 'f' → '0'
    new_char = chr((ord(original_char) + 1) % 256)
    if new_char > 'f' or (new_char >= '0' and new_char < 'a'):
        new_char = '0'
    hash_list[0] = new_char
    tampered[target_event_idx]["payload_hash"] = "".join(hash_list)

    corrupted_hash = tampered[target_event_idx]["payload_hash"]
    print(f"\nTampering event {target_event_idx}:")
    print(f"  Original payload_hash: {original_hash[:16]}...")
    print(f"  Corrupted payload_hash: {corrupted_hash[:16]}...")

    # Write to temp file and validate
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False) as f:
        tampered_path = Path(f.name)
        save_ledger(tampered, tampered_path)

    try:
        success, failure_reason = run_boot_validator(tampered_path)

        print(f"\nValidation result:")
        print(f"  Success: {success}")
        print(f"  Failure reason: {failure_reason}")

        if not success and failure_reason == "LEDGER_HASH_MISMATCH":
            print(f"\n✅ T-HW-1 PASSED: Boot validator correctly detected ledger corruption")
            return True
        else:
            print(f"\n❌ T-HW-1 FAILED: Expected LEDGER_HASH_MISMATCH, got {failure_reason}")
            return False
    finally:
        tampered_path.unlink()

# =============================================================================
# T-HW-2: SEAL BINDING MUTATION
# =============================================================================

def test_t_hw_2_seal_mutation():
    """
    T-HW-2: Corrupt the seal's final_cum_hash reference.
    Expected: Boot validator detects SEAL_BINDING_MISMATCH and fails closed.
    """
    print("\n" + "=" * 80)
    print("T-HW-2: SEAL BINDING MUTATION TEST")
    print("=" * 80)

    # Load reference ledger
    events = load_ledger(REFERENCE_LEDGER)
    print(f"Loaded {len(events)} events from reference ledger")

    # Create tampered version: flip 1 nibble in seal event's final_cum_hash
    tampered = events.copy()
    seal_event_idx = len(tampered) - 1  # Last event should be seal
    assert tampered[seal_event_idx]["type"] == "seal", "Last event must be seal"

    refs = tampered[seal_event_idx]["payload"]["refs"]
    original_cum_hash = refs["final_ledger_cum_hash"]

    # Flip one nibble
    hash_list = list(original_cum_hash)
    hash_list[5] = chr((ord(hash_list[5]) + 1) % 256)
    if hash_list[5] > 'f' or (hash_list[5] >= '0' and hash_list[5] < 'a'):
        hash_list[5] = '0'
    tampered[seal_event_idx]["payload"]["refs"]["final_ledger_cum_hash"] = "".join(hash_list)

    corrupted_hash = tampered[seal_event_idx]["payload"]["refs"]["final_ledger_cum_hash"]
    print(f"\nTampering seal event (event {seal_event_idx}):")
    print(f"  Original final_cum_hash: {original_cum_hash[:16]}...")
    print(f"  Corrupted final_cum_hash: {corrupted_hash[:16]}...")

    # Write to temp file and validate
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False) as f:
        tampered_path = Path(f.name)
        save_ledger(tampered, tampered_path)

    try:
        success, failure_reason = run_boot_validator(tampered_path)

        print(f"\nValidation result:")
        print(f"  Success: {success}")
        print(f"  Failure reason: {failure_reason}")

        if not success and failure_reason == "SEAL_BINDING_MISMATCH":
            print(f"\n✅ T-HW-2 PASSED: Boot validator correctly detected seal corruption")
            return True
        else:
            print(f"\n❌ T-HW-2 FAILED: Expected SEAL_BINDING_MISMATCH, got {failure_reason}")
            return False
    finally:
        tampered_path.unlink()

# =============================================================================
# T-HW-3: REPLAY / REORDERING
# =============================================================================

def test_t_hw_3_reordering():
    """
    T-HW-3: Swap two adjacent ledger events (reordering attack).
    Expected: Boot validator detects chain break (prev_cum_hash mismatch) and fails closed.
    """
    print("\n" + "=" * 80)
    print("T-HW-3: REPLAY / REORDERING TEST")
    print("=" * 80)

    # Load reference ledger
    events = load_ledger(REFERENCE_LEDGER)
    print(f"Loaded {len(events)} events from reference ledger")

    # Create tampered version: swap events 1 and 2 (don't touch seal)
    tampered = events.copy()
    swap_idx_a = 1
    swap_idx_b = 2

    print(f"\nReordering attack:")
    print(f"  Swapping event {swap_idx_a} (type={tampered[swap_idx_a]['type']}) "
          f"with event {swap_idx_b} (type={tampered[swap_idx_b]['type']})")

    # Swap
    tampered[swap_idx_a], tampered[swap_idx_b] = tampered[swap_idx_b], tampered[swap_idx_a]

    print(f"  New sequence: {[e.get('type') for e in tampered]}")

    # Write to temp file and validate
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False) as f:
        tampered_path = Path(f.name)
        save_ledger(tampered, tampered_path)

    try:
        success, failure_reason = run_boot_validator(tampered_path)

        print(f"\nValidation result:")
        print(f"  Success: {success}")
        print(f"  Failure reason: {failure_reason}")

        if not success and failure_reason in ["LEDGER_HASH_MISMATCH", "SEQUENCE_VIOLATION"]:
            print(f"\n✅ T-HW-3 PASSED: Boot validator detected reordering attack")
            return True
        else:
            print(f"\n❌ T-HW-3 FAILED: Expected hash/sequence failure, got {failure_reason}")
            return False
    finally:
        tampered_path.unlink()

# =============================================================================
# MAIN
# =============================================================================

def main():
    print("\n" + "=" * 80)
    print("CWL v1.0.1 TAMPER DETECTION TEST SUITE (T-HW-1/2/3)")
    print("=" * 80)
    print(f"\nReference ledger: {REFERENCE_LEDGER}")
    print(f"Exists: {REFERENCE_LEDGER.exists()}")

    if not REFERENCE_LEDGER.exists():
        print(f"ERROR: Reference ledger not found at {REFERENCE_LEDGER}")
        return False

    results = []

    # Run all tests
    results.append(("T-HW-1: Ledger Mutation", test_t_hw_1_ledger_mutation()))
    results.append(("T-HW-2: Seal Binding", test_t_hw_2_seal_mutation()))
    results.append(("T-HW-3: Reordering", test_t_hw_3_reordering()))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} passed")

    if passed == total:
        print("\n🎯 ALL TAMPER DETECTION TESTS PASSED")
        print("Boot validator is FAIL-CLOSED under adversarial mutation.")
        return True
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
