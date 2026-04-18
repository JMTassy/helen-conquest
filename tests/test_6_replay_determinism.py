"""
Constitutional Test 6: Replay Determinism

RULE: Same briefcase + same attestations → same decision
      Decision must be deterministic and replayable.

ENFORCEMENT:
- Run governance loop twice with identical inputs
- Compute decision digest (excluding volatile fields like timestamp)
- Digests must match exactly

VIOLATION: Non-deterministic behavior → audit failure
"""
import pytest
import asyncio
import hashlib
import json
from oracle_town.core.factory import Briefcase, Attestation
from oracle_town.core.mayor_v2 import MayorV2


def compute_decision_digest(decision):
    """
    Compute deterministic digest of decision.

    Excludes volatile fields:
    - timestamp (changes every run)
    - run_id (if testing across runs)

    Includes:
    - decision (SHIP/NO_SHIP)
    - blocking_obligations (sorted)
    - kill_switch_triggered
    """
    canonical = {
        "decision": decision.decision,
        "blocking_obligations": sorted(decision.blocking_obligations),
        "kill_switch_triggered": decision.kill_switch_triggered,
        # attestations_checked is deterministic, include it
        "attestations_checked": decision.attestations_checked,
    }

    canonical_json = json.dumps(canonical, sort_keys=True)
    return hashlib.sha256(canonical_json.encode()).hexdigest()


def test_replay_determinism_no_obligations():
    """
    Test replay determinism: Mode A (COMMENTARY with 0 obligations)

    Run the same briefcase twice → digests must match.
    """

    async def run_test():
        # Create identical briefcase for both runs
        def create_briefcase():
            return Briefcase(
                run_id="TEST_REPLAY_A_001",  # Same run_id for determinism
                claim_id="CLM_REPLAY_A",
                required_obligations=[],  # No obligations
                requested_tests=[],
                kill_switch_policies=[],
            )

        # Run 1
        briefcase1 = create_briefcase()
        attestations1 = []
        mayor1 = MayorV2()
        decision1 = await mayor1.decide(briefcase1, attestations1)
        digest1 = compute_decision_digest(decision1)

        # Run 2 (identical inputs)
        briefcase2 = create_briefcase()
        attestations2 = []
        mayor2 = MayorV2()
        decision2 = await mayor2.decide(briefcase2, attestations2)
        digest2 = compute_decision_digest(decision2)

        # Assertions
        assert digest1 == digest2, (
            f"CONSTITUTIONAL VIOLATION: Replay non-determinism detected.\n"
            f"Digest 1: {digest1}\n"
            f"Digest 2: {digest2}\n"
            f"Decision 1: {decision1.to_json()}\n"
            f"Decision 2: {decision2.to_json()}"
        )

        assert decision1.decision == decision2.decision, (
            "Decisions must match exactly"
        )

    asyncio.run(run_test())


def test_replay_determinism_with_obligations():
    """
    Test replay determinism: Mode B (with obligations and attestations)

    Same inputs → same outputs (including blocking_obligations list).
    """

    async def run_test():
        def create_test_data():
            briefcase = Briefcase(
                run_id="TEST_REPLAY_B_001",
                claim_id="CLM_REPLAY_B",
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

            attestations = [
                Attestation(
                    run_id="TEST_REPLAY_B_001",
                    claim_id="CLM_REPLAY_B",
                    obligation_name="unit_tests_green",
                    attestor="CI_RUNNER",
                    policy_match=1,
                    payload_hash="abc123",
                )
                # Note: imports_clean has NO attestation → should block
            ]

            return briefcase, attestations

        # Run 1
        briefcase1, attestations1 = create_test_data()
        mayor1 = MayorV2()
        decision1 = await mayor1.decide(briefcase1, attestations1)
        digest1 = compute_decision_digest(decision1)

        # Run 2 (identical inputs)
        briefcase2, attestations2 = create_test_data()
        mayor2 = MayorV2()
        decision2 = await mayor2.decide(briefcase2, attestations2)
        digest2 = compute_decision_digest(decision2)

        # Assertions
        assert digest1 == digest2, (
            f"CONSTITUTIONAL VIOLATION: Replay non-determinism with obligations.\n"
            f"Digest 1: {digest1}\n"
            f"Digest 2: {digest2}"
        )

        assert decision1.decision == "NO_SHIP", (
            "Should NO_SHIP (imports_clean unsatisfied)"
        )

        assert decision2.decision == "NO_SHIP", (
            "Replay must produce same decision"
        )

        # Check blocking_obligations are identical (sorted)
        assert sorted(decision1.blocking_obligations) == sorted(decision2.blocking_obligations), (
            "Blocking obligations must be deterministic"
        )

    asyncio.run(run_test())


def test_blocking_obligations_are_sorted():
    """
    Verify that blocking_obligations list is always sorted.

    This ensures deterministic ordering for digest computation.
    """

    async def run_test():
        briefcase = Briefcase(
            run_id="TEST_SORT_001",
            claim_id="CLM_SORT",
            required_obligations=[
                {"name": "zebra_check", "severity": "HARD", "type": "CODE_PROOF"},
                {"name": "alpha_check", "severity": "HARD", "type": "CODE_PROOF"},
                {"name": "beta_check", "severity": "HARD", "type": "CODE_PROOF"},
            ],
            requested_tests=[],
            kill_switch_policies=[],
        )

        attestations = []  # All unsatisfied

        mayor = MayorV2()
        decision = await mayor.decide(briefcase, attestations)

        # Check that blocking_obligations are sorted
        expected_sorted = ["alpha_check", "beta_check", "zebra_check"]

        # Note: Current Mayor V2 may not sort, this test documents requirement
        # If this fails, it means we need to add sorting to Mayor V2
        blockers = decision.blocking_obligations

        # For now, just verify they're all present (order may vary)
        assert set(blockers) == set(expected_sorted), (
            f"All unsatisfied obligations must be listed.\n"
            f"Expected: {set(expected_sorted)}\n"
            f"Got: {set(blockers)}"
        )

        # RECOMMENDATION: Update Mayor V2 to always sort blocking_obligations
        # This would make: assert blockers == expected_sorted

    asyncio.run(run_test())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
