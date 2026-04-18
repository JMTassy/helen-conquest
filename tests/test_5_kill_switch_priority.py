"""
Constitutional Test 5: Kill-Switch Absolute Priority

RULE: If kill-switch triggered → NO_SHIP (immediate)
      Even if all attestations satisfied.

ENFORCEMENT:
- Construct briefcase with satisfied attestations
- Trigger kill-switch signal
- Mayor must return NO_SHIP with kill_switch_triggered=true
- No attestation checks should matter

VIOLATION: SHIP despite kill-switch → safety violation
"""
import pytest
import asyncio
from oracle_town.core.factory import Briefcase, Attestation
from oracle_town.core.mayor_v2 import MayorV2


def test_kill_switch_blocks_even_with_satisfied_attestations():
    """
    Constitutional Test 5: Kill-Switch Absolute Priority

    Even if all obligations are satisfied, kill-switch must block SHIP.
    """

    async def run_test():
        # Create briefcase with obligations
        briefcase = Briefcase(
            run_id="TEST_KILL_001",
            claim_id="CLM_TEST_KILL",
            required_obligations=[
                {
                    "name": "unit_tests_green",
                    "type": "CODE_PROOF",
                    "severity": "HARD",
                },
            ],
            requested_tests=[],
            kill_switch_policies=["LEGAL_VETO"],  # Policy exists but not enforced here
        )

        # ALL obligations satisfied
        attestations = [
            Attestation(
                run_id="TEST_KILL_001",
                claim_id="CLM_TEST_KILL",
                obligation_name="unit_tests_green",
                attestor="CI_RUNNER",
                policy_match=1,
                payload_hash="abc123",
            )
        ]

        # Kill-switch triggered by LEGAL team
        mayor = MayorV2()
        decision = await mayor.decide(
            briefcase,
            attestations,
            kill_switch_signals=["LEGAL"]  # LEGAL triggers kill-switch
        )

        # Assertions
        assert decision.decision == "NO_SHIP", (
            "CONSTITUTIONAL VIOLATION: Kill-switch must block SHIP"
        )

        assert decision.kill_switch_triggered == True, (
            "kill_switch_triggered must be True when signal provided"
        )

        assert decision.blocking_obligations == [], (
            "blocking_obligations should be empty (kill-switch takes priority)"
        )

    asyncio.run(run_test())


def test_kill_switch_teams_are_limited():
    """
    Test that only authorized teams can trigger kill-switch.

    Default: LEGAL, SECURITY
    Random signals should not trigger kill-switch.
    """

    async def run_test():
        briefcase = Briefcase(
            run_id="TEST_KILL_002",
            claim_id="CLM_TEST_KILL_2",
            required_obligations=[],
            requested_tests=[],
            kill_switch_policies=[],
        )

        attestations = []

        # Try to trigger kill-switch with unauthorized signal
        mayor = MayorV2()
        decision = await mayor.decide(
            briefcase,
            attestations,
            kill_switch_signals=["RANDOM_TEAM", "UNAUTHORIZED"]
        )

        # Should NOT trigger kill-switch (signals not authorized)
        assert decision.kill_switch_triggered == False, (
            "Only LEGAL/SECURITY should trigger kill-switch"
        )

        assert decision.decision == "SHIP", (
            "Should SHIP when kill-switch not triggered and no obligations"
        )

    asyncio.run(run_test())


def test_legal_and_security_can_kill_switch():
    """
    Verify that LEGAL and SECURITY teams can trigger kill-switch.
    """

    async def run_test():
        briefcase = Briefcase(
            run_id="TEST_KILL_003",
            claim_id="CLM_TEST_KILL_3",
            required_obligations=[],
            requested_tests=[],
            kill_switch_policies=[],
        )

        attestations = []
        mayor = MayorV2()

        # Test LEGAL
        decision_legal = await mayor.decide(
            briefcase, attestations, kill_switch_signals=["LEGAL"]
        )
        assert decision_legal.kill_switch_triggered == True, (
            "LEGAL should trigger kill-switch"
        )

        # Test SECURITY
        decision_security = await mayor.decide(
            briefcase, attestations, kill_switch_signals=["SECURITY"]
        )
        assert decision_security.kill_switch_triggered == True, (
            "SECURITY should trigger kill-switch"
        )

        # Test case-insensitive
        decision_lowercase = await mayor.decide(
            briefcase, attestations, kill_switch_signals=["legal"]
        )
        assert decision_lowercase.kill_switch_triggered == True, (
            "Kill-switch should be case-insensitive"
        )

    asyncio.run(run_test())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
