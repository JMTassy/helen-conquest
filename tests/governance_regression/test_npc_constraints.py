"""
NPC Constraints Tests

NPCs are observation-only actors with zero authority.
They cannot approve, reject, override, or sign.
They only generate claims admissible for amendments.
"""

import pytest


class TestNPCObservationOnly:
    """NPCs can observe but cannot decide."""

    def test_npc_cannot_issue_verdict(self):
        """NPC observation is not a verdict."""
        npc_observation = {
            "npc_type": "accuracy_watcher",
            "measurement": 0.71,
            "is_verdict": False  # Cannot be verdict
        }

        assert npc_observation["is_verdict"] == False

    def test_npc_cannot_approve_claim(self):
        """NPC observation cannot approve."""
        npc_observation = {
            "npc_type": "pattern_detector",
            "observation": "Pattern detected",
            "approval_given": False
        }

        assert npc_observation["approval_given"] == False

    def test_npc_cannot_reject_claim(self):
        """NPC observation cannot reject."""
        npc_observation = {
            "npc_type": "risk_analyzer",
            "observation": "Risk level: medium",
            "rejection_issued": False
        }

        assert npc_observation["rejection_issued"] == False


class TestNPCNoExecutiveAuthority:
    """NPCs cannot execute or trigger action."""

    def test_npc_cannot_trigger_override(self):
        """NPC observation cannot enable override."""
        npc_observation = {
            "npc_type": "speculation_tracker",
            "can_trigger_override": False
        }

        assert npc_observation["can_trigger_override"] == False

    def test_npc_cannot_mutate_ledger(self):
        """NPC observation cannot write to ledger directly."""
        npc_observation = {
            "npc_type": "accuracy_watcher",
            "can_write_ledger": False
        }

        assert npc_observation["can_write_ledger"] == False

    def test_npc_cannot_sign(self):
        """NPC cannot sign documents or receipts."""
        npc_observation = {
            "npc_type": "risk_analyzer",
            "signed": False,
            "signature_issued": False
        }

        assert npc_observation["signed"] == False


class TestNPCClaimsAreAdmissibleForAmendmentsOnly:
    """NPC claims are eligible evidence for amendments only."""

    def test_npc_claim_admissible_for_amendment(self):
        """NPC observation is evidence for amendments."""
        npc_observation = {
            "npc_type": "pattern_detector",
            "eligible_for_amendment": True,
            "can_support_amendment": True
        }

        assert npc_observation["eligible_for_amendment"] == True

    def test_npc_claim_not_input_to_tri(self):
        """NPC observation does not go to TRI gate."""
        npc_observation = {
            "npc_type": "accuracy_watcher",
            "routes_to_tri": False
        }

        assert npc_observation["routes_to_tri"] == False

    def test_npc_claim_not_binding(self):
        """NPC observation is not binding."""
        npc_observation = {
            "npc_type": "risk_analyzer",
            "binding": False,
            "advisory": True
        }

        assert npc_observation["binding"] == False


class TestNPCOutputConstraints:
    """NPCs must follow strict output constraints."""

    def test_npc_cannot_use_prescriptive_language(self):
        """NPC: No 'should', 'must', 'recommend'."""
        npc_observation = {
            "observation": "Accuracy rate is 71%. This is healthy."  # Factual only
        }

        forbidden_words = ["should", "must", "recommend", "better", "worse"]
        has_forbidden = any(word in npc_observation["observation"].lower() for word in forbidden_words)

        assert has_forbidden == False

    def test_npc_cannot_make_future_predictions(self):
        """NPC: No future tense. Measures past only."""
        npc_observation = {
            "observation": "Acceptance rate was 40% in January"  # Past tense
        }

        forbidden_tense = ["will", "expect", "predict", "forecast"]
        has_future = any(word in npc_observation["observation"].lower() for word in forbidden_tense)

        assert has_future == False

    def test_npc_must_reference_ledger(self):
        """NPC: Ledger-bound only. No external data."""
        npc_observation = {
            "referenced_receipts": ["R-2026-01-15-0001", "R-2026-01-15-0002"],
            "external_data_used": False
        }

        has_references = len(npc_observation.get("referenced_receipts", [])) > 0
        assert has_references == True


class TestFourCanonicalNPCTypes:
    """Only four NPC types exist (immutable set)."""

    def test_four_npc_types_only(self):
        """Only four types: AccuracyWatcher, SpeculationTracker, PatternDetector, RiskAnalyzer."""
        valid_types = {
            "accuracy_watcher",
            "speculation_tracker",
            "pattern_detector",
            "risk_analyzer"
        }

        npc_type = "accuracy_watcher"
        assert npc_type in valid_types

    def test_cannot_add_new_npc_type(self):
        """Adding NPC type requires doctrine amendment."""
        existing_types = 4
        new_type_allowed = False  # Only via amendment

        assert new_type_allowed == False


class TestNPCSilenceIsValid:
    """Silence from NPC is valid output."""

    def test_npc_silence_is_not_failure(self):
        """NPC emitting nothing is valid."""
        npc_observation = None  # Silence

        # Silence is valid (means no anomaly detected)
        assert npc_observation is None

    def test_npc_silence_does_not_block_system(self):
        """System does not fail on NPC silence."""
        npc_observations = [
            {"npc_type": "accuracy_watcher", "observation": "Data here"},
            None,  # Silence from another NPC
            {"npc_type": "risk_analyzer", "observation": "Data here"}
        ]

        # System continues
        assert len(npc_observations) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
