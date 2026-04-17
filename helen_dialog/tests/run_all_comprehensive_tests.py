#!/usr/bin/env python3
"""
run_all_comprehensive_tests.py

Master test runner for FULL DIALOGUE + SCF INTEGRATION SUITE (T1–T8).

T1–T4: Dialogue Box Receipt-Grade Tests
  T1: Deterministic Replay
  T2: Append-Only Discipline
  T3: Authority Ban
  T4: Moment Purity

T5–T8: SCF Integration Tests
  T5: SCF Determinism
  T6: SCF Authority Ban
  T7: SCF Filtering Accuracy
  T8: SCF Telemetry Integrity

Runs all tests sequentially and produces summary report.
"""

import subprocess
import sys
from pathlib import Path


def run_test(test_module: str) -> bool:
    """Run a single test module. Return True if passed."""
    result = subprocess.run(
        [sys.executable, test_module],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
    )

    # Print output
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    return result.returncode == 0


def main():
    print("\n" + "=" * 70)
    print("COMPREHENSIVE DIALOGUE + SCF INTEGRATION TEST SUITE (T1–T8)")
    print("=" * 70)
    print()

    dialogue_tests = [
        ("T1", "test_dialogue_replay_determinism.py", "Deterministic Replay"),
        ("T2", "test_dialogue_appendonly_discipline.py", "Append-Only Discipline"),
        ("T3", "test_dialogue_authority_ban.py", "Authority Ban"),
        ("T4", "test_dialogue_moment_purity.py", "Moment Purity"),
    ]

    scf_tests = [
        ("T5", "test_scf_determinism.py", "SCF Determinism"),
        ("T6", "test_scf_authority_ban.py", "SCF Authority Ban"),
        ("T7", "test_scf_filtering_accuracy.py", "SCF Filtering Accuracy"),
        ("T8", "test_scf_telemetry_integrity.py", "SCF Telemetry Integrity"),
    ]

    all_tests = dialogue_tests + scf_tests
    results = {}

    # Run dialogue tests
    print("\n" + "=" * 70)
    print("PHASE 1: DIALOGUE BOX TESTS (T1–T4)")
    print("=" * 70)

    for test_id, test_module, test_name in dialogue_tests:
        print(f"\n[{test_id}] {test_name}...")
        print(f"    Running: {test_module}")
        passed = run_test(test_module)
        results[test_id] = (test_name, passed)
        print(f"    Result: {'✅ PASS' if passed else '❌ FAIL'}")

    # Run SCF tests
    print("\n" + "=" * 70)
    print("PHASE 2: SCF INTEGRATION TESTS (T5–T8)")
    print("=" * 70)

    for test_id, test_module, test_name in scf_tests:
        print(f"\n[{test_id}] {test_name}...")
        print(f"    Running: {test_module}")
        passed = run_test(test_module)
        results[test_id] = (test_name, passed)
        print(f"    Result: {'✅ PASS' if passed else '❌ FAIL'}")

    # Summary
    print("\n" + "=" * 70)
    print("COMPREHENSIVE TEST SUMMARY")
    print("=" * 70)

    print("\nDialogue Box Tests (T1–T4):")
    for test_id, test_name in [(t, n) for t, n, _ in dialogue_tests]:
        passed = results[test_id][1]
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_id}: {results[test_id][0]:<30} {status}")

    print("\nSCF Integration Tests (T5–T8):")
    for test_id, test_name in [(t, n) for t, n, _ in scf_tests]:
        passed = results[test_id][1]
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_id}: {results[test_id][0]:<30} {status}")

    # Overall summary
    print("\n" + "=" * 70)
    passed_count = sum(1 for _, (_, p) in results.items() if p)
    total_count = len(results)

    print(f"Total: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n✅ ALL TESTS PASSED — Dialogue + SCF integration is ready for deployment")
        return 0
    else:
        print(f"\n❌ {total_count - passed_count} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
