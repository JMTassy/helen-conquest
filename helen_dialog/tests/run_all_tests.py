#!/usr/bin/env python3
"""
run_all_tests.py

Master test runner for dialogue box receipt-grade validation.

Runs T1–T4 in sequence, reports results, and exits with success only if all pass.
"""

import subprocess
import sys
from pathlib import Path


def run_test(test_file: Path) -> bool:
    """Run a single test file, return True if passed."""
    print(f"\n{'='*70}")
    print(f"Running: {test_file.name}")
    print(f"{'='*70}")

    result = subprocess.run([sys.executable, str(test_file)], cwd=test_file.parent)
    return result.returncode == 0


def main():
    """Run all tests in order."""
    test_dir = Path(__file__).parent
    tests = [
        test_dir / "test_dialogue_replay_determinism.py",
        test_dir / "test_dialogue_appendonly_discipline.py",
        test_dir / "test_dialogue_authority_ban.py",
        test_dir / "test_dialogue_moment_purity.py",
    ]

    print("\n" + "=" * 70)
    print("DIALOGUE BOX RECEIPT-GRADE VALIDATION SUITE")
    print("=" * 70)
    print("Running 4 mechanical tests: T1–T4")

    results = {}
    for test_file in tests:
        test_name = test_file.stem
        passed = run_test(test_file)
        results[test_name] = passed

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:50s} {status}")
        if not passed:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n🎯 ALL TESTS PASSED (T1–T4)")
        print("\nDialogue box is receipt-grade stable:")
        print("  ✓ Deterministic replay verified")
        print("  ✓ Append-only discipline verified")
        print("  ✓ Authority leakage banned")
        print("  ✓ Moment detector is pure function")
        print("\nReady for SCF integration.\n")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
