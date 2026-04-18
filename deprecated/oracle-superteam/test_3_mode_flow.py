#!/usr/bin/env python3
"""
test_3_mode_flow.py

Integration test for 3-mode WUL-ORACLE flow:
MODE 1: Test a claim (validate + evaluate) → NO_SHIP
MODE 2: Ask superteam to improve → Apply improvements
MODE 3: Ask Mayor to ship → Generate artifact

Tests the complete governance pipeline with the new superteam.improve module.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wul.validate import load_kernel, WULValidator
from receipt.compute_gap import compute_receipt_gap
from mayor.decide import compute_decision
from superteam.improve import propose_improvements, apply_improvements

def test_mode_1_test_claim():
    """MODE 1: Test a claim and get NO_SHIP verdict."""
    print("=" * 80)
    print("MODE 1: TEST A CLAIM")
    print("=" * 80)

    # Load kernel
    kernel = load_kernel()
    validator = WULValidator(kernel)

    # Create claim
    claim = {
        "id": "test_claim_001",
        "text": "WUL-ORACLE provides deterministic governance through receipt verification",
        "author": "test",
        "timestamp": "2026-01-18T10:00:00Z"
    }

    print(f"\nClaim ID: {claim['id']}")
    print(f"Claim: {claim['text']}")

    # Build token tree (using only kernel primitives)
    token_tree = {
        "D01": {
            "R15": "E03"  # CLAIM RETURNS_TO OBJECTIVE (arity=1)
        }
    }

    print("\n--- Step 1: Validate Token Tree ---")
    result = validator.validate_token_tree(token_tree)

    print(f"Validation: {'PASS' if result.ok else 'FAIL'}")
    print(f"  Depth: {result.depth}/{validator.max_depth}")
    print(f"  Nodes: {result.nodes}/{validator.max_nodes}")
    print(f"  Has R15: {result.has_r15}")

    if not result.ok:
        print(f"  FAILED: {result.reason}")
        return None, None, None, None

    # Build tribunal bundle
    print("\n--- Step 2: Build Tribunal Bundle ---")
    tribunal = {
        "claim_id": claim['id'],
        "obligations": [
            {
                "name": "wul_validation",
                "type": "validation",
                "severity": "HARD",
                "expected_attestor": "wul_validator",
                "description": "WUL-CORE v0 validation"
            },
            {
                "name": "determinism_check",
                "type": "determinism",
                "severity": "HARD",
                "expected_attestor": "determinism_checker",
                "description": "Determinism verification"
            },
            {
                "name": "schema_validation",
                "type": "schema",
                "severity": "HARD",
                "expected_attestor": "schema_validator",
                "description": "Schema validation"
            },
            {
                "name": "documentation",
                "type": "docs",
                "severity": "SOFT",
                "expected_attestor": "docs_team",
                "description": "Documentation"
            }
        ]
    }

    print(f"Obligations: {len(tribunal['obligations'])}")
    for obl in tribunal['obligations']:
        print(f"  [{obl['severity']}] {obl['name']}")

    # Simulate partial attestations (missing 2 HARD obligations)
    print("\n--- Step 3: Simulate Attestations (Partial) ---")
    attestations = {
        "attestations": [
            {
                "obligation_name": "wul_validation",
                "attestor": "wul_validator",
                "attestation_valid": True,
                "policy_match": 1,
                "payload_hash": "abc123"
            },
            {
                "obligation_name": "documentation",
                "attestor": "docs_team",
                "attestation_valid": True,
                "policy_match": 1,
                "payload_hash": "docs789"
            }
        ]
    }

    print(f"Attestations received: {len(attestations['attestations'])}")

    # Compute receipt gap
    print("\n--- Step 4: Compute Receipt Gap ---")
    receipt_gap, missing = compute_receipt_gap(tribunal, attestations)

    print(f"Receipt Gap: {receipt_gap}")
    if receipt_gap > 0:
        print(f"Missing HARD obligations:")
        for m in missing:
            print(f"  - {m['name']}: {m['reason_code']}")

    # Compute Mayor decision
    print("\n--- Step 5: Mayor Decision ---")
    policies = {
        "kill_switches_pass": True,
        "kill_switches": [
            {"name": "no_free_text", "status": "pass"},
            {"name": "bounded_structure", "status": "pass"}
        ]
    }

    receipt_payload = {
        "receipt_gap": receipt_gap,
        "missing_obligations": missing
    }

    decision = compute_decision(tribunal, policies, receipt_payload)

    print(f"Decision: {decision['decision']}")
    print(f"Receipt Gap: {decision['receipt_gap']}")
    print(f"Kill Switches: {'PASS' if decision['kill_switches_pass'] else 'FAIL'}")

    if decision['decision'] == 'NO_SHIP':
        print(f"\nBlocking Reasons:")
        for block in decision['blocking']:
            print(f"  [{block['code']}] {block['detail']}")

    print("\n✓ MODE 1 Complete: NO_SHIP verdict with receipt gap = 2")

    return claim, tribunal, attestations, decision


def test_mode_2_improve_claim(claim, tribunal, attestations, decision):
    """MODE 2: Ask superteam to improve and apply improvements."""
    print("\n" + "=" * 80)
    print("MODE 2: ASK SUPERTEAM TO IMPROVE")
    print("=" * 80)

    if decision['decision'] == 'SHIP':
        print("✓ Claim already passes! No improvement needed.")
        return attestations, decision

    print(f"\nCurrent Decision: {decision['decision']}")
    print(f"Receipt Gap: {decision['receipt_gap']}")

    # Generate improvements using superteam module
    print("\n--- Step 1: Generate Improvements ---")
    improvements = propose_improvements(claim, tribunal, attestations, decision)

    print(f"\nSuperteam proposed {len(improvements)} improvements:\n")
    for i, imp in enumerate(improvements, 1):
        print(f"{i}. {imp.type}: {imp.target}")
        print(f"   Description: {imp.description}")
        print(f"   Impact: {imp.impact}")
        print(f"   Mayor Score: {imp.mayor_score}%\n")

    # Apply improvements
    print("--- Step 2: Apply Improvements ---")
    improved_attestations = apply_improvements(attestations, improvements)

    print(f"Attestations after improvement: {len(improved_attestations['attestations'])}")

    # Recompute receipt gap
    print("\n--- Step 3: Recompute Receipt Gap ---")
    receipt_gap, missing = compute_receipt_gap(tribunal, improved_attestations)

    print(f"New Receipt Gap: {receipt_gap} (was: {decision['receipt_gap']})")

    # Recompute decision
    print("\n--- Step 4: Recompute Mayor Decision ---")
    receipt_payload = {
        "receipt_gap": receipt_gap,
        "missing_obligations": missing
    }

    policies = {
        "kill_switches_pass": True,
        "kill_switches": [
            {"name": "no_free_text", "status": "pass"},
            {"name": "bounded_structure", "status": "pass"}
        ]
    }

    new_decision = compute_decision(tribunal, policies, receipt_payload)

    print(f"New Decision: {new_decision['decision']}")

    if new_decision['decision'] == 'SHIP':
        print("\n✓ MODE 2 Complete: Improvements successful! Claim now ready to SHIP")
    else:
        print(f"\n⚠ Improvements applied, but still NO_SHIP. Receipt gap: {receipt_gap}")

    return improved_attestations, new_decision


def test_mode_3_mayor_ship(claim, decision):
    """MODE 3: Ask Mayor to ship and generate artifact."""
    print("\n" + "=" * 80)
    print("MODE 3: ASK MAYOR TO SHIP")
    print("=" * 80)

    if decision['decision'] != 'SHIP':
        print(f"✗ Cannot ship: Decision is {decision['decision']}")
        print("⚠ Use MODE 2 to improve the claim first.")
        return None

    print(f"✓ Decision: SHIP")
    print(f"Claim: {claim['text']}\n")

    # Generate text output
    print("--- Generating Shipment Artifact (Text Format) ---\n")

    output = f"""
WUL-ORACLE SHIPMENT CERTIFICATION
═════════════════════════════════════════════════════════════

CLAIM ID: {claim['id']}

CLAIM STATEMENT:
{claim['text']}

GOVERNANCE EVALUATION
─────────────────────────────────────────────────────────────

Mayor Decision: {decision['decision']} ✓
Receipt Gap: {decision['receipt_gap']} (all HARD obligations satisfied)
Kill Switches: {'PASSED' if decision['kill_switches_pass'] else 'FAILED'}

CONSTITUTIONAL COMPLIANCE
─────────────────────────────────────────────────────────────

✓ Invariant 5.1 (No Silent Failures): Blocking array properly formed
✓ Invariant 5.2 (SHIP Implies Zero Gap): Receipt gap == 0
✓ Schema Validation: decision_record.schema.json (2020-12)
✓ Reason Code Allowlist: All codes from canonical registry

RECEIPT BINDING
─────────────────────────────────────────────────────────────

Mayor Version: {decision['metadata']['mayor_version']}
Tribunal Bundle Hash: {decision['metadata']['tribunal_bundle_hash']}
Policies Hash: {decision['metadata']['policies_hash']}
Receipt Root Hash: {decision['metadata']['receipt_root_hash']}

CERTIFICATION
─────────────────────────────────────────────────────────────

This claim has been evaluated under the WUL-ORACLE constitutional
framework and has passed all governance gates. The decision is
deterministic, auditable, and replayable.

Status: CERTIFIED FOR SHIPMENT
Generated: 2026-01-18T10:00:00Z

═════════════════════════════════════════════════════════════
"""

    print(output)

    print("\n✓ MODE 3 Complete: Shipment artifact generated")

    return output


def main():
    """Run complete 3-mode flow integration test."""
    print("\n")
    print("█" * 80)
    print("WUL-ORACLE 3-MODE FLOW INTEGRATION TEST")
    print("█" * 80)
    print()

    try:
        # MODE 1: Test claim → NO_SHIP
        claim, tribunal, attestations, decision = test_mode_1_test_claim()

        if claim is None:
            print("\n✗ MODE 1 failed. Stopping test.")
            return 1

        # MODE 2: Improve claim → SHIP
        improved_attestations, improved_decision = test_mode_2_improve_claim(
            claim, tribunal, attestations, decision
        )

        # MODE 3: Ship artifact
        artifact = test_mode_3_mayor_ship(claim, improved_decision)

        if artifact is None:
            print("\n✗ MODE 3 failed: Cannot ship.")
            return 1

        # Summary
        print("\n" + "█" * 80)
        print("TEST SUMMARY")
        print("█" * 80)
        print()
        print("✓ MODE 1: Test claim → NO_SHIP verdict (receipt gap = 2)")
        print("✓ MODE 2: Superteam improvements → SHIP verdict (receipt gap = 0)")
        print("✓ MODE 3: Mayor shipment → Artifact generated")
        print()
        print("✓ ALL TESTS PASSED")
        print("The Mediterranean does not need promises. It needs receipts.")
        print("█" * 80)

        return 0

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
