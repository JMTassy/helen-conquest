#!/usr/bin/env python3
"""
Quick test of WUL-ORACLE emulator components
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from wul.validate import load_kernel, validate_token_tree
from wul_oracle_emulator_complete import (
    build_wul_token_tree,
    build_tribunal_bundle,
    build_policies,
    build_initial_attestations_ledger,
    build_receipt_root_payload,
    compute_progress_percent,
    propose_improvements,
    MayorInputs,
    RunState
)
from mayor.decide import compute_decision_payload
from receipt.compute_gap import compute_receipt_gap


def test_mode_1_flow():
    """Test Mode 1: Test a claim"""
    print("=" * 60)
    print("TEST: Mode 1 Flow (Test a Claim)")
    print("=" * 60)

    # Load kernel
    kernel_path = ROOT / "src" / "wul" / "core_kernel.json"
    kernel = load_kernel(kernel_path)
    print(f"✓ Loaded kernel: {kernel['version']}")

    # Example claim
    claim = "Publish a deterministic decision_record payload under SHIP only."
    print(f"\nClaim: {claim}")

    # Build artifacts
    token_tree = build_wul_token_tree(claim)
    tribunal = build_tribunal_bundle(claim)
    policies = build_policies(claim)
    receipt_root = build_receipt_root_payload(token_tree, tribunal, policies)
    ledger = build_initial_attestations_ledger("partial")

    print("\n--- WUL Validation ---")
    res = validate_token_tree(token_tree, kernel, require_r15=True)
    if res.ok:
        print(f"✓ PASSED (depth: {res.depth}, nodes: {res.nodes})")
    else:
        print(f"✗ FAILED: {res.reason}")

    # Compute decision
    print("\n--- Mayor Decision ---")
    inp = MayorInputs(
        tribunal_bundle=tribunal,
        attestations_ledger=ledger,
        policies=policies,
        receipt_root_payload=receipt_root
    )
    decision = compute_decision_payload(inp)

    print(f"Decision: {decision['decision']}")
    print(f"Receipt Gap: {decision['receipt_gap']}")
    print(f"Kill Switches: {'PASS' if decision['kill_switches_pass'] else 'FAIL'}")

    if decision['blocking']:
        print("\nBlocking Reasons:")
        for b in decision['blocking']:
            print(f"  [{b['code']}] {b.get('detail', '')}")

    progress = compute_progress_percent(tribunal, ledger, policies)
    print(f"\nProgress: {progress}%")

    return decision['decision'] == 'NO_SHIP'  # Expected


def test_mode_2_flow():
    """Test Mode 2: Superteam improvements"""
    print("\n" + "=" * 60)
    print("TEST: Mode 2 Flow (Superteam Improve)")
    print("=" * 60)

    # Load kernel
    kernel_path = ROOT / "src" / "wul" / "core_kernel.json"
    kernel = load_kernel(kernel_path)

    claim = "Publish a deterministic decision_record payload under SHIP only."
    token_tree = build_wul_token_tree(claim)
    tribunal = build_tribunal_bundle(claim)
    policies = build_policies(claim)
    receipt_root = build_receipt_root_payload(token_tree, tribunal, policies)
    ledger = build_initial_attestations_ledger("partial")

    # Create state
    state = RunState(
        claim_text=claim,
        token_tree=token_tree,
        tribunal_bundle=tribunal,
        policies=policies,
        attestations_ledger=ledger,
        receipt_root_payload=receipt_root
    )

    current_decision = state.recompute_decision()
    print(f"Current Decision: {current_decision['decision']}")
    print(f"Current Gap: {current_decision['receipt_gap']}")

    # Generate improvements
    improvements = propose_improvements(
        state.tribunal_bundle,
        state.attestations_ledger,
        state.policies,
        state.receipt_root_payload
    )

    print(f"\n--- Superteam Proposals ({len(improvements)}) ---")
    for i, imp in enumerate(improvements, 1):
        print(f"\n{i}. {imp.title}")
        print(f"   Mayor Eval: {imp.mayor_percent}% (Δ{imp.delta_percent:+d}%)")
        print(f"   Predicted: {imp.predicted_decision}")

    # Apply best improvement
    if improvements:
        best = improvements[0]
        state.attestations_ledger = best.new_attestations_ledger
        state.policies = best.new_policies
        new_decision = state.recompute_decision()

        print(f"\n✓ Applied: {best.title}")
        print(f"New Decision: {new_decision['decision']}")
        print(f"New Gap: {new_decision['receipt_gap']}")

        return new_decision['decision'] == 'SHIP'  # Expected after improvement

    return False


def main():
    print("WUL-ORACLE Emulator Component Tests\n")

    try:
        # Test Mode 1
        test1_pass = test_mode_1_flow()
        print(f"\n{'✓' if test1_pass else '✗'} Test 1: {'PASS' if test1_pass else 'FAIL'}")

        # Test Mode 2
        test2_pass = test_mode_2_flow()
        print(f"\n{'✓' if test2_pass else '✗'} Test 2: {'PASS' if test2_pass else 'FAIL'}")

        print("\n" + "=" * 60)
        if test1_pass and test2_pass:
            print("ALL TESTS PASSED ✓")
        else:
            print("SOME TESTS FAILED ✗")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
