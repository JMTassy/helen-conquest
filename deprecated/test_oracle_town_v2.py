#!/usr/bin/env python3
"""
Test ORACLE TOWN V2 with governance kernel.

Tests the claim:
"You are not lost. What you pasted is simply two incompatible architectures..."
→ Should result in SHIP (meta-commentary, no obligations) or NO_SHIP (if treated as technical claim)
"""
import asyncio
from oracle_town.core.factory import Factory, Briefcase, Attestation
from oracle_town.core.mayor_v2 import MayorV2


async def test_user_claim():
    """Test with user's actual claim about architectural mismatch"""

    user_claim_text = """
    You are not "lost." What you pasted is simply two incompatible architectures accidentally merged:
    1. ChatDev / AI-Town style cognition simulator (turns, contributions, questions, confidence, "GO/NO_GO"), and
    2. LEGORACLE v2 law-bound truth machine (obligations → attestations → mayor-only verdict).

    Right now your generated oracle-town/ codebase is architecturally non-compliant with the v2 constitution you wrote.
    It will feel exciting, but it will not scale into "NO_RECEIPT = NO_SHIP" governance.
    """

    print("=" * 80)
    print("ORACLE TOWN V2 TEST")
    print("=" * 80)
    print(f"\nCLAIM:\n{user_claim_text[:200]}...\n")

    # Scenario 1: Treat as meta-commentary (no obligations)
    print("\n" + "=" * 80)
    print("SCENARIO 1: Meta-commentary (no technical obligations)")
    print("=" * 80)

    briefcase1 = Briefcase(
        run_id="RUN_METACOMMENT_001",
        claim_id="CLM_ARCH_ANALYSIS",
        required_obligations=[],  # Meta-commentary has no obligations
        requested_tests=[],
        kill_switch_policies=[],
        metadata={"claim_type": "analysis", "domain": "meta"}
    )

    factory1 = Factory(ledger_path="test_v2_ledger.jsonl")
    attestations1 = await factory1.verify_briefcase(briefcase1)

    mayor1 = MayorV2()
    decision1 = await mayor1.decide(briefcase1, attestations1)

    print(f"\n✅ Decision: {decision1.decision}")
    print(f"   Blocking obligations: {decision1.blocking_obligations}")
    print(f"   Attestations checked: {decision1.attestations_checked}")

    # Save decision record (required for pass conditions)
    decision1.save()
    print(f"\n💾 Saved: decision_{decision1.run_id}.json")

    if decision1.decision == "SHIP":
        print("\n✅ SHIP: Meta-commentary approved (no obligations to satisfy)")

    # Scenario 2: Treat as technical claim requiring refactor
    print("\n" + "=" * 80)
    print("SCENARIO 2: Technical claim (refactoring obligations)")
    print("=" * 80)

    briefcase2 = Briefcase(
        run_id="RUN_REFACTOR_001",
        claim_id="CLM_ARCH_REFACTOR",
        required_obligations=[
            {
                "name": "remove_confidence_from_mayor",
                "type": "CODE_PROOF",
                "severity": "HARD",
                "required_evidence": ["test_mayor_no_confidence_pass"],
                "description": "Mayor must not use confidence in decision logic"
            },
            {
                "name": "add_attestation_ledger",
                "type": "CODE_PROOF",
                "severity": "HARD",
                "required_evidence": ["test_ledger_append_only"],
                "description": "Factory must write append-only attestation ledger"
            },
            {
                "name": "enforce_no_receipt_no_ship",
                "type": "CODE_PROOF",
                "severity": "HARD",
                "required_evidence": ["test_no_attestation_blocks_ship"],
                "description": "Mayor must block SHIP if attestations missing"
            },
        ],
        requested_tests=[
            {
                "obligation_name": "remove_confidence_from_mayor",
                "test_command": "pytest tests/test_mayor_v2.py::test_no_confidence",
            },
            {
                "obligation_name": "add_attestation_ledger",
                "test_command": "pytest tests/test_factory.py::test_ledger_append",
            },
            {
                "obligation_name": "enforce_no_receipt_no_ship",
                "test_command": "pytest tests/test_mayor_v2.py::test_blocks_without_attestation",
            },
        ],
        kill_switch_policies=[],
        metadata={"claim_type": "refactor", "domain": "technical"}
    )

    factory2 = Factory(ledger_path="test_v2_ledger.jsonl")
    attestations2 = await factory2.verify_briefcase(briefcase2)

    print(f"\n📋 Obligations: {len(briefcase2.required_obligations)}")
    print(f"📋 Attestations generated: {len(attestations2)}")

    for att in attestations2:
        status = "✅" if att.is_satisfied() else "❌"
        print(f"   {status} {att.obligation_name}: policy_match={att.policy_match}")

    mayor2 = MayorV2()
    decision2 = await mayor2.decide(briefcase2, attestations2)

    print(f"\n✅ Decision: {decision2.decision}")
    print(f"   Blocking obligations: {decision2.blocking_obligations}")

    # Save decision record (always, regardless of verdict)
    decision2.save()
    print(f"\n💾 Saved: decision_{decision2.run_id}.json")

    if decision2.decision == "NO_SHIP":
        remediation = await mayor2.generate_remediation(briefcase2, decision2)
        print(f"\n📋 Remediation plan: {len(remediation.suggested_actions)} actions")
        for action in remediation.suggested_actions:
            print(f"   → {action['action']}: {action['command']}")

        # Save remediation
        remediation.save()
        print(f"💾 Saved: remediation_{decision2.run_id}.json")

    # Scenario 3: Kill-switch test (LEGAL team blocks)
    print("\n" + "=" * 80)
    print("SCENARIO 3: Kill-switch (LEGAL team blocks)")
    print("=" * 80)

    briefcase3 = Briefcase(
        run_id="RUN_KILLSWITCH_001",
        claim_id="CLM_KILL_TEST",
        required_obligations=[],
        requested_tests=[],
        kill_switch_policies=["LEGAL_VETO"],
    )

    factory3 = Factory(ledger_path="test_v2_ledger.jsonl")
    attestations3 = await factory3.verify_briefcase(briefcase3)

    mayor3 = MayorV2()
    decision3 = await mayor3.decide(
        briefcase3, attestations3, kill_switch_signals=["LEGAL"]
    )

    print(f"\n🚨 Decision: {decision3.decision}")
    print(f"   Kill-switch: {decision3.kill_switch_triggered}")

    # Save decision record
    decision3.save()
    print(f"\n💾 Saved: decision_{decision3.run_id}.json")

    if decision3.kill_switch_triggered:
        print("\n🚨 LEGAL team triggered kill-switch → immediate NO_SHIP")

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Scenario 1 (Meta-commentary): {decision1.decision}")
    print(f"Scenario 2 (Technical refactor): {decision2.decision}")
    print(f"Scenario 3 (Kill-switch): {decision3.decision}")
    print("\n✅ All scenarios tested successfully!")


if __name__ == "__main__":
    asyncio.run(test_user_claim())
