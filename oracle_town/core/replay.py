#!/usr/bin/env python3
"""
Replay Verification: Determinism Enforcement

Verifies that replaying a run with same inputs produces identical outputs.

Key invariant: replay(briefcase, ledger, policy) → same decision_digest
"""
import sys
import os
import json
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from oracle_town.core.policy import Policy
from oracle_town.core.mayor_rsm import MayorRSM


def load_json(path: str) -> Dict[str, Any]:
    """Load JSON file"""
    with open(path, "r") as f:
        return json.load(f)


def replay_run(run_dir: str) -> Dict[str, Any]:
    """
    Replay a run from immutable artifacts.

    Args:
        run_dir: Path to run directory

    Returns:
        Replay result with verification status
    """
    print(f"\n{'=' * 70}")
    print(f"REPLAYING: {run_dir}")
    print("=" * 70)

    # Load artifacts
    briefcase = load_json(f"{run_dir}/briefcase.json")
    ledger = load_json(f"{run_dir}/ledger.json")
    policy_dict = load_json(f"{run_dir}/policy.json")
    original_decision = load_json(f"{run_dir}/decision_record.json")
    original_hashes = load_json(f"{run_dir}/hashes.json")

    print(f"\n✓ Loaded artifacts")
    print(f"  Original Decision: {original_decision['decision']}")
    print(f"  Original Decision Digest: {original_decision['decision_digest']}")

    # Reconstruct policy
    policy = Policy.from_dict(policy_dict)

    # Verify policy hash
    if not policy.verify_hash():
        print(f"\n❌ REPLAY FAILED: Policy hash mismatch")
        return {
            "status": "FAILED",
            "reason": "Policy hash verification failed",
            "run_dir": run_dir
        }

    print(f"\n✓ Policy hash verified: {policy.policy_hash}")

    # Replay decision
    # Load public keys for signature verification
    keys_path = os.path.join(os.path.dirname(__file__), "..", "keys", "public_keys.json")
    mayor = MayorRSM(public_keys_path=keys_path if os.path.exists(keys_path) else None)
    replayed_decision = mayor.decide(policy, briefcase, ledger)

    print(f"\n✓ Replayed decision")
    print(f"  Replayed Decision: {replayed_decision.decision}")
    print(f"  Replayed Decision Digest: {replayed_decision.decision_digest}")

    # Verify determinism
    if replayed_decision.decision_digest != original_decision["decision_digest"]:
        print(f"\n❌ REPLAY FAILED: Decision digest mismatch")
        print(f"  Expected: {original_decision['decision_digest']}")
        print(f"  Got:      {replayed_decision.decision_digest}")
        return {
            "status": "FAILED",
            "reason": "Decision digest mismatch (non-deterministic)",
            "run_dir": run_dir,
            "expected_digest": original_decision["decision_digest"],
            "got_digest": replayed_decision.decision_digest
        }

    # Verify decision is identical
    if replayed_decision.decision != original_decision["decision"]:
        print(f"\n❌ REPLAY FAILED: Decision mismatch")
        print(f"  Expected: {original_decision['decision']}")
        print(f"  Got:      {replayed_decision.decision}")
        return {
            "status": "FAILED",
            "reason": "Decision mismatch",
            "run_dir": run_dir
        }

    print(f"\n✅ REPLAY VERIFIED: Determinism confirmed")
    print(f"  Decision: {replayed_decision.decision}")
    print(f"  Digest:   {replayed_decision.decision_digest}")

    return {
        "status": "SUCCESS",
        "run_dir": run_dir,
        "decision": replayed_decision.decision,
        "decision_digest": replayed_decision.decision_digest,
        "deterministic": True
    }


def replay_multiple_times(run_dir: str, iterations: int = 10) -> Dict[str, Any]:
    """
    Replay run multiple times to verify determinism.

    Args:
        run_dir: Path to run directory
        iterations: Number of replay iterations

    Returns:
        Verification result
    """
    print(f"\n{'=' * 70}")
    print(f"DETERMINISM TEST: {run_dir} ({iterations} iterations)")
    print("=" * 70)

    # Load artifacts
    briefcase = load_json(f"{run_dir}/briefcase.json")
    ledger = load_json(f"{run_dir}/ledger.json")
    policy_dict = load_json(f"{run_dir}/policy.json")

    policy = Policy.from_dict(policy_dict)
    # Load public keys for signature verification
    keys_path = os.path.join(os.path.dirname(__file__), "..", "keys", "public_keys.json")
    mayor = MayorRSM(public_keys_path=keys_path if os.path.exists(keys_path) else None)

    # Replay multiple times
    digests = []
    decisions = []

    for i in range(iterations):
        replayed_decision = mayor.decide(policy, briefcase, ledger)
        digests.append(replayed_decision.decision_digest)
        decisions.append(replayed_decision.decision)

    # Check all digests are identical
    unique_digests = set(digests)
    unique_decisions = set(decisions)

    print(f"\n✓ Replayed {iterations} times")
    print(f"  Unique digests: {len(unique_digests)}")
    print(f"  Unique decisions: {len(unique_decisions)}")

    if len(unique_digests) == 1 and len(unique_decisions) == 1:
        print(f"\n✅ DETERMINISM VERIFIED")
        print(f"  All digests identical: {digests[0]}")
        print(f"  All decisions identical: {decisions[0]}")

        return {
            "status": "SUCCESS",
            "run_dir": run_dir,
            "iterations": iterations,
            "deterministic": True,
            "decision_digest": digests[0],
            "decision": decisions[0]
        }
    else:
        print(f"\n❌ DETERMINISM FAILED")
        print(f"  Multiple unique digests: {unique_digests}")
        print(f"  Multiple unique decisions: {unique_decisions}")

        return {
            "status": "FAILED",
            "run_dir": run_dir,
            "iterations": iterations,
            "deterministic": False,
            "unique_digests": list(unique_digests),
            "unique_decisions": list(unique_decisions)
        }


def main():
    """Replay all three adversarial runs"""
    print("=" * 70)
    print("REPLAY VERIFICATION TEST SUITE")
    print("=" * 70)

    run_dirs = [
        "oracle_town/runs/runA_no_ship_missing_receipts",
        "oracle_town/runs/runB_no_ship_fake_attestor",
        "oracle_town/runs/runC_ship_quorum_valid"
    ]

    results = []

    # Single replay verification
    for run_dir in run_dirs:
        result = replay_run(run_dir)
        results.append(result)

    # Determinism test (10 iterations)
    print(f"\n\n{'=' * 70}")
    print("DETERMINISM VERIFICATION (10 iterations per run)")
    print("=" * 70)

    determinism_results = []
    for run_dir in run_dirs:
        result = replay_multiple_times(run_dir, iterations=10)
        determinism_results.append(result)

    # Summary
    print(f"\n\n{'=' * 70}")
    print("REPLAY VERIFICATION SUMMARY")
    print("=" * 70)

    print(f"\nSingle Replay:")
    for result in results:
        status_symbol = "✅" if result["status"] == "SUCCESS" else "❌"
        print(f"  {status_symbol} {result['run_dir']}: {result.get('decision', 'FAILED')}")

    print(f"\nDeterminism (10 iterations):")
    for result in determinism_results:
        status_symbol = "✅" if result["deterministic"] else "❌"
        print(f"  {status_symbol} {result['run_dir']}: {result.get('decision', 'FAILED')}")

    # Overall verdict
    all_passed = all(r["status"] == "SUCCESS" for r in results)
    all_deterministic = all(r["deterministic"] for r in determinism_results)

    if all_passed and all_deterministic:
        print(f"\n{'=' * 70}")
        print("✅ ALL REPLAY VERIFICATION TESTS PASSED")
        print("=" * 70)
        return 0
    else:
        print(f"\n{'=' * 70}")
        print("❌ SOME REPLAY VERIFICATION TESTS FAILED")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
