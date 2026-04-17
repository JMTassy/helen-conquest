#!/usr/bin/env python3
"""
run_scf_tests.py

Master test runner for SCF integration tests (T5–T8).

T5: SCF Determinism
T6: SCF Authority Ban
T7: SCF Filtering Accuracy
T8: SCF Telemetry Integrity

Runs all tests sequentially and reports summary.
"""

import subprocess
import sys
from pathlib import Path


def run_test(test_module: str) -> bool:
    """Run a single test module. Return True if passed."""
    result = subprocess.run(
        [sys.executable, test_module],
        cwd=Path(__file__).parent,
        capture_output=False,
    )
    return result.returncode == 0


def main():
    print("\n" + "=" * 70)
    print("SCF INTEGRATION TEST SUITE (T5–T8)")
    print("=" * 70)

    tests = [
        ("T5", "test_scf_determinism.py"),
        ("T6", "test_scf_authority_ban.py"),
        ("T7", "test_scf_filtering_accuracy.py"),
        ("T8", "test_scf_telemetry_integrity.py"),
    ]

    results = {}

    for test_name, test_module in tests:
        print(f"\n[{test_name}] Running {test_module}...")
        passed = run_test(test_module)
        results[test_name] = passed

    # Summary
    print("\n" + "=" * 70)
    print("SCF TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")

    passed_count = sum(1 for p in results.values() if p)
    total_count = len(results)

    print(f"\nTotal: {passed_count}/{total_count} passed")

    if passed_count == total_count:
        print("\n✅ ALL TESTS PASSED")
        return 0
    else:
        print(f"\n❌ {total_count - passed_count} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
