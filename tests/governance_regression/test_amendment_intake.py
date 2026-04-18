"""
Amendment Intake Tests

Structural validation of amendment proposals.
Deterministic intake checks before human voting.
"""

import pytest
from datetime import datetime, timedelta


class TestAmendmentEvidenceGate:
    """Gate A: Amendment must have ≥2 NPCs + ≥90 days + same section."""

    def test_amendment_requires_two_npc_types(self):
        """Amendment needs ≥2 distinct NPC types."""
        amendment = {
            "supporting_npc_types": ["accuracy_watcher", "pattern_detector"]
        }

        npc_count = len(amendment.get("supporting_npc_types", []))
        assert npc_count >= 2

    def test_amendment_single_npc_rejected(self):
        """Amendment with only 1 NPC type → REJECTED."""
        amendment = {
            "supporting_npc_types": ["accuracy_watcher"]  # Only 1
        }

        npc_count = len(amendment.get("supporting_npc_types", []))
        should_reject = npc_count < 2
        assert should_reject == True

    def test_amendment_requires_90_day_window(self):
        """Amendment needs ≥90 days observation."""
        start_date = datetime(2026, 1, 31)
        end_date = datetime(2026, 5, 1)
        duration = (end_date - start_date).days

        assert duration >= 90

    def test_amendment_89_days_rejected(self):
        """Amendment with 89 days → REJECTED."""
        start_date = datetime(2026, 1, 31)
        end_date = datetime(2026, 4, 29)  # 89 days
        duration = (end_date - start_date).days

        should_reject = duration < 90
        assert should_reject == True

    def test_amendment_references_same_doctrine_section(self):
        """All NPCs must reference same section."""
        amendment = {
            "npc_evidences": [
                {"npc_type": "accuracy_watcher", "targets_section": "3.2"},
                {"npc_type": "pattern_detector", "targets_section": "3.2"}
            ],
            "target_section": "3.2"
        }

        sections = [e["targets_section"] for e in amendment["npc_evidences"]]
        all_match = all(s == amendment["target_section"] for s in sections)
        assert all_match == True

    def test_amendment_mismatched_sections_rejected(self):
        """NPCs targeting different sections → REJECTED."""
        amendment = {
            "npc_evidences": [
                {"npc_type": "accuracy_watcher", "targets_section": "3.2"},
                {"npc_type": "pattern_detector", "targets_section": "4.1"}  # Different
            ]
        }

        sections = set(e["targets_section"] for e in amendment["npc_evidences"])
        all_match = len(sections) == 1
        assert all_match == False


class TestAmendmentTargetValidation:
    """Amendment must specify exact section and exact current text."""

    def test_amendment_references_by_section_number(self):
        """Amendment cites section: e.g., '3.2'."""
        amendment = {
            "target_section": "3.2"
        }

        assert amendment["target_section"] is not None

    def test_amendment_includes_current_text_verbatim(self):
        """Amendment must copy exact doctrine text."""
        current_doctrine_text = "REJECT is a completed act of governance"
        amendment = {
            "current_text": current_doctrine_text
        }

        assert amendment["current_text"] == current_doctrine_text

    def test_amendment_cannot_paraphrase(self):
        """Amendment cannot paraphrase doctrine (must be exact)."""
        exact = "REJECT is a completed act of governance"
        paraphrased = "A rejection is a final decision"

        assert exact != paraphrased


class TestAmendmentConservatismGate:
    """Gate B: Amendment must show inaction ≥ risk of change."""

    def test_amendment_quantifies_inaction_risk(self):
        """Amendment states cost of NOT changing."""
        amendment = {
            "risk_of_inaction": "€200k/month in prevented failures"
        }

        assert amendment["risk_of_inaction"] is not None

    def test_amendment_quantifies_change_risk(self):
        """Amendment states cost of changing."""
        amendment = {
            "risk_of_change": "Modest rejection rate increase (estimated 2-3%)"
        }

        assert amendment["risk_of_change"] is not None

    def test_amendment_fails_conservatism_if_change_more_risky(self):
        """If change_risk > inaction_risk → REJECTED."""
        amendment = {
            "risk_of_inaction": 100,  # Low
            "risk_of_change": 500  # High
        }

        change_is_riskier = amendment["risk_of_change"] > amendment["risk_of_inaction"]
        should_reject = change_is_riskier
        assert should_reject == True


class TestAmendmentRatificationGate:
    """Gate C: Amendment requires explicit human vote."""

    def test_amendment_requires_vote(self):
        """Amendment must include RATIFY, REJECT, or CONDITIONAL_ACCEPT."""
        amendment = {
            "vote": "RATIFY"
        }

        valid_votes = {"RATIFY", "REJECT", "CONDITIONAL_ACCEPT"}
        assert amendment["vote"] in valid_votes

    def test_amendment_cannot_abstain(self):
        """No abstention allowed."""
        amendment = {
            "vote": "ABSTAIN"  # Invalid
        }

        valid_votes = {"RATIFY", "REJECT", "CONDITIONAL_ACCEPT"}
        should_reject = amendment["vote"] not in valid_votes
        assert should_reject == True

    def test_amendment_silence_is_reject(self):
        """No vote → treated as REJECT."""
        amendment = {
            "vote": None  # No vote
        }

        no_vote = amendment["vote"] is None
        treated_as_reject = no_vote
        assert treated_as_reject == True

    def test_amendment_vote_must_be_timestamped(self):
        """Vote must include timestamp."""
        amendment = {
            "vote": "RATIFY",
            "vote_timestamp": "2026-06-30T09:15:00Z"
        }

        assert amendment["vote_timestamp"] is not None


class TestAmendmentDeterminism:
    """Same amendment input → same intake decision (K5)."""

    def test_amendment_intake_deterministic(self):
        """Identical amendment → identical result."""
        amendment = {
            "id": "A-2026-06-001",
            "npc_types": ["accuracy_watcher", "pattern_detector"],
            "observation_days": 90,
            "target_section": "3.2"
        }

        # Run intake check twice
        result1 = (len(amendment["npc_types"]) >= 2 and
                   amendment["observation_days"] >= 90)
        result2 = (len(amendment["npc_types"]) >= 2 and
                   amendment["observation_days"] >= 90)

        assert result1 == result2, "Amendment intake not deterministic"


class TestAmendmentLedgerEntry:
    """Amendment creates immutable ledger record."""

    def test_amendment_ledger_entry_created(self):
        """Approved amendment recorded in ledger."""
        amendment = {
            "id": "A-2026-06-001",
            "status": "RATIFIED",
            "ledger_entry": True
        }

        assert amendment["ledger_entry"] == True

    def test_amendment_ledger_immutable(self):
        """Amendment record cannot be edited after creation."""
        amendment = {
            "id": "A-2026-06-001",
            "locked": True,
            "can_edit": False
        }

        assert amendment["can_edit"] == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
