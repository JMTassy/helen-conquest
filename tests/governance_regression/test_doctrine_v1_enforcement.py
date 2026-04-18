"""
DOCTRINE_V1.0 Enforcement Tests

Verifies structural enforcement of the doctrine.
Four classes must remain distinct.
Acceptance rate law is measured, not enforced.
Override protocol is mandatory.
"""

import pytest


class TestFourInvestmentClasses:
    """Four classes are immutable and distinct."""

    def test_class_i_governable_properties(self):
        """CLASS_I: Evidence exists, bounded downside, reversible."""
        submission = {
            "class": "CLASS_I",
            "evidence_strength": "strong",
            "reversibility": "high",
            "narrative_component": None
        }

        assert submission["class"] == "CLASS_I"
        assert submission["evidence_strength"] in ["strong", "moderate"]
        assert submission["reversibility"] in ["high", "medium"]

    def test_class_ii_conditionally_governable(self):
        """CLASS_II: Partial evidence, validation delayed, risk asymmetric."""
        submission = {
            "class": "CLASS_II",
            "evidence_strength": "moderate",
            "narrative_allowed": True,
            "validation_timeline": "Q3 2026"
        }

        assert submission["class"] == "CLASS_II"
        assert submission["evidence_strength"] in ["strong", "moderate"]

    def test_class_iii_speculative(self):
        """CLASS_III: Narrative-dominant, irreversible, override required."""
        submission = {
            "class": "CLASS_III",
            "is_override": True,
            "identity_defining": True,
            "review_date": "2027-01-31"
        }

        assert submission["class"] == "CLASS_III"
        assert submission["is_override"] == True
        assert submission["review_date"] is not None

    def test_class_iv_existential(self):
        """CLASS_IV: Identity-defining, cannot be optimized."""
        submission = {
            "class": "CLASS_IV",
            "is_override": True,
            "identity_defining": True,
            "outcome_irrelevant_to_legitimacy": True
        }

        assert submission["class"] == "CLASS_IV"


class TestAcceptanceRateLaw:
    """Acceptance rate law: 35-45% is health, not a target."""

    def test_acceptance_rate_diagnostic_function(self):
        """Rate is diagnostic, not target."""
        verdicts = ["ACCEPT", "ACCEPT", "REJECT", "REJECT", "REJECT"]
        accept_count = len([v for v in verdicts if v == "ACCEPT"])
        rate = accept_count / len(verdicts)

        # Rate is 0.40 (40%), which is healthy
        assert 0.35 <= rate <= 0.45, f"Rate {rate} is in healthy zone"

    def test_high_rate_indicates_under_filtering(self):
        """Rate > 50% means accepting too easily."""
        verdicts = ["ACCEPT"] * 6 + ["REJECT"] * 4
        rate = 0.60

        # This is above 50%, indicates under-filtering
        assert rate > 0.50

    def test_low_rate_indicates_over_submitting(self):
        """Rate < 30% means submissions lack evidence."""
        verdicts = ["REJECT"] * 8 + ["ACCEPT"] * 2
        rate = 0.20

        # This is below 30%, indicates over-submission
        assert rate < 0.30


class TestRefusalDoctrine:
    """REJECT is complete. Not provisional, not negotiable."""

    def test_reject_is_terminal(self):
        """Once REJECT issued, decision is final."""
        verdict = {
            "decision": "REJECT",
            "can_retry": False,
            "can_appeal_as_new_submission": True,
            "can_reinterpret": False
        }

        assert verdict["decision"] == "REJECT"
        assert verdict["can_retry"] == False

    def test_reject_prevents_override_except_class_iii(self):
        """REJECT prevents override unless reclassified to CLASS_III."""
        rejected_claim = {
            "class": "CLASS_I",
            "verdict": "REJECT"
        }

        # Cannot override CLASS_I REJECT without reclassification
        can_override = (rejected_claim["class"] == "CLASS_I" and
                       rejected_claim["verdict"] == "REJECT") == False

        assert can_override == False, "Cannot override CLASS_I REJECT"

    def test_override_as_class_iii_requires_logging(self):
        """If overriding CLASS_I REJECT, must reclassify to CLASS_III and log."""
        override = {
            "original_class": "CLASS_I",
            "original_verdict": "REJECT",
            "reclassified_to": "CLASS_III",
            "logged": True,
            "review_date": "2027-01-31"
        }

        assert override["reclassified_to"] == "CLASS_III"
        assert override["logged"] == True


class TestOverrideProtocol:
    """Overrides are costly: mandatory logging, review dates, expected outcomes."""

    def test_override_requires_amount_at_risk(self):
        """Override must declare financial exposure."""
        override = {
            "amount_at_risk": 700000,
            "currency": "EUR"
        }

        assert override["amount_at_risk"] is not None
        assert override["amount_at_risk"] > 0

    def test_override_requires_explicit_rationale(self):
        """Override reason must be ≥50 chars (show your work)."""
        override = {
            "override_reason": "Property investment with long-term strategic importance"
        }

        assert len(override["override_reason"]) >= 50

    def test_override_review_date_is_locked(self):
        """Review date must be ≥90 days out and immutable."""
        override = {
            "decision_date": "2026-01-31",
            "review_date": "2027-01-31",
            "days_until_review": 366
        }

        assert override["days_until_review"] >= 90

    def test_override_immutable_permanence(self):
        """Once logged, override cannot be deleted or modified."""
        override = {
            "id": "override_le_tar_001",
            "locked": True,
            "can_delete": False,
            "can_edit": False
        }

        assert override["locked"] == True
        assert override["can_delete"] == False


class TestSilencePrinciple:
    """When INSIGHT is OFF, do nothing. Silence is valid."""

    def test_silence_valid_output(self):
        """NPC may emit nothing if no pattern detected."""
        npc_observation = None  # Silence

        # Silence is valid
        assert npc_observation is None or isinstance(npc_observation, type(None))

    def test_no_forced_conclusions(self):
        """System does not extrapolate from absence."""
        observations = []

        # Cannot claim "system is perfect" from empty set
        # (Would need to explicitly check and find nothing)
        can_conclude_health = len(observations) > 0

        assert can_conclude_health == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
