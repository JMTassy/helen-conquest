"""
Constitutional Test 4: NO RECEIPT = NO SHIP

RULE: Every HARD obligation requires a matching satisfied attestation.
      Missing attestations → NO_SHIP with blocking_obligations listed.

ENFORCEMENT:
- Construct briefcase with HARD obligations
- Empty attestation list
- Mayor must return NO_SHIP with exact list of unsatisfied obligations

VIOLATION: SHIP without receipts → constitutional violation
"""
import pytest
import asyncio
from oracle_town.core.factory import Briefcase, Attestation
from oracle_town.core.mayor_v2 import MayorV2


def test_no_receipt_no_ship_sync():
    """
    Constitutional Test 4: NO RECEIPT = NO SHIP

    Constructs briefcase with HARD obligations but no attestations.
    Mayor must block SHIP and list all unsatisfied obligations.
    """

    async def run_test():
        # Create briefcase with 2 HARD obligations
        briefcase = Briefcase(
            run_id="TEST_NO_RECEIPT_001",
            claim_id="CLM_TEST_001",
            required_obligations=[
                {
                    "name": "unit_tests_green",
                    "type": "CODE_PROOF",
                    "severity": "HARD",
                    "required_evidence": ["pytest_pass"],
                },
                {
                    "name": "imports_clean",
                    "type": "CODE_PROOF",
                    "severity": "HARD",
                    "required_evidence": ["import_success"],
                },
            ],
            requested_tests=[],
            kill_switch_policies=[],
        )

        # Empty attestation list (NO RECEIPTS)
        attestations = []

        # Mayor must return NO_SHIP
        mayor = MayorV2()
        decision = await mayor.decide(briefcase, attestations)

        # Assertions
        assert decision.decision == "NO_SHIP", (
            "CONSTITUTIONAL VIOLATION: Mayor allowed SHIP without receipts"
        )

        assert decision.kill_switch_triggered == False, (
            "Kill-switch should not trigger (this is a receipt gap)"
        )

        expected_blockers = {"unit_tests_green", "imports_clean"}
        actual_blockers = set(decision.blocking_obligations)

        assert actual_blockers == expected_blockers, (
            f"CONSTITUTIONAL VIOLATION: Blocking obligations mismatch.\n"
            f"Expected: {expected_blockers}\n"
            f"Actual: {actual_blockers}"
        )

    asyncio.run(run_test())


def test_partial_receipts_still_block():
    """
    Test that having SOME receipts but not ALL blocks SHIP.

    If 2 HARD obligations exist but only 1 has attestation → NO_SHIP.
    """

    async def run_test():
        briefcase = Briefcase(
            run_id="TEST_PARTIAL_001",
            claim_id="CLM_TEST_002",
            required_obligations=[
                {
                    "name": "unit_tests_green",
                    "type": "CODE_PROOF",
                    "severity": "HARD",
                },
                {
                    "name": "imports_clean",
                    "type": "CODE_PROOF",
                    "severity": "HARD",
                },
            ],
            requested_tests=[],
            kill_switch_policies=[],
        )

        # Only ONE attestation (unit_tests_green satisfied, imports_clean missing)
        attestations = [
            Attestation(
                run_id="TEST_PARTIAL_001",
                claim_id="CLM_TEST_002",
                obligation_name="unit_tests_green",
                attestor="CI_RUNNER",
                policy_match=1,
                payload_hash="abc123",
            )
        ]

        mayor = MayorV2()
        decision = await mayor.decide(briefcase, attestations)

        assert decision.decision == "NO_SHIP", (
            "CONSTITUTIONAL VIOLATION: Mayor allowed SHIP with partial receipts"
        )

        assert "imports_clean" in decision.blocking_obligations, (
            "Missing obligation must be listed in blocking_obligations"
        )

        assert "unit_tests_green" not in decision.blocking_obligations, (
            "Satisfied obligation should not be in blocking_obligations"
        )

    asyncio.run(run_test())


def test_soft_obligations_do_not_block():
    """
    Test that SOFT obligations do not block SHIP even if unsatisfied.

    Only HARD obligations enforce NO RECEIPT = NO SHIP.
    """

    async def run_test():
        briefcase = Briefcase(
            run_id="TEST_SOFT_001",
            claim_id="CLM_TEST_003",
            required_obligations=[
                {
                    "name": "replay_determinism",
                    "type": "TOOL_RESULT",
                    "severity": "SOFT",  # SOFT obligation
                },
            ],
            requested_tests=[],
            kill_switch_policies=[],
        )

        # No attestations (SOFT obligation unsatisfied)
        attestations = []

        mayor = MayorV2()
        decision = await mayor.decide(briefcase, attestations)

        assert decision.decision == "SHIP", (
            "CONSTITUTIONAL VIOLATION: SOFT obligations should not block SHIP"
        )

        assert decision.blocking_obligations == [], (
            "SOFT obligations should not appear in blocking_obligations"
        )

    asyncio.run(run_test())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
