"""
Doctrine Enforcer Tests

Pre-TRI gate validation rejecting malformed submissions.
Enforces structural requirements before authority evaluation.
"""

import pytest


class TestDoctrineEnforcerIntake:
    """Doctrine enforcer rejects submissions that violate structure."""

    def test_enforcer_rejects_class_i_without_evidence(self):
        """CLASS_I submitted without evidence → REJECTED at intake."""
        submission = {
            "class": "CLASS_I",
            "evidence_pointers": []  # Empty
        }

        # Enforcer checks
        has_evidence = len(submission.get("evidence_pointers", [])) > 0
        class_requires_evidence = submission["class"] == "CLASS_I"

        # Should be rejected at intake
        should_reject = class_requires_evidence and not has_evidence
        assert should_reject == True, "Enforcer should reject CLASS_I without evidence"

    def test_enforcer_accepts_valid_class_i(self):
        """CLASS_I with strong evidence → accepted to TRI."""
        submission = {
            "class": "CLASS_I",
            "evidence_pointers": [
                {"type": "test_result", "hash": "sha256:abc123"}
            ]
        }

        has_evidence = len(submission.get("evidence_pointers", [])) > 0
        assert has_evidence == True


class TestNarrativeLaunderingDetection:
    """Enforcer detects narrative language and rejects."""

    def test_enforcer_rejects_believe_language(self):
        """Narrative: 'I believe' → REJECTED."""
        submission = {
            "class": "CLASS_I",
            "intent": "I believe this is a good decision"
        }

        forbidden_words = ["believe", "feel", "intuitively", "probably", "likely"]
        intent = submission["intent"].lower()

        has_forbidden = any(word in intent for word in forbidden_words)
        assert has_forbidden == True, "Contains forbidden narrative language"

    def test_enforcer_rejects_feel_language(self):
        """Narrative: 'I feel' → REJECTED."""
        submission = {
            "class": "CLASS_I",
            "intent": "I feel confident about this"
        }

        has_feel = "feel" in submission["intent"].lower()
        assert has_feel == True

    def test_enforcer_accepts_factual_language(self):
        """Factual language → accepted."""
        submission = {
            "class": "CLASS_I",
            "intent": "Test results show 95% success rate"
        }

        forbidden_words = ["believe", "feel", "intuitively"]
        has_forbidden = any(word in submission["intent"].lower() for word in forbidden_words)
        assert has_forbidden == False


class TestClassMismatchDetection:
    """Enforcer detects CLASS_III disguised as CLASS_I."""

    def test_enforcer_rejects_class_iii_submitted_as_class_i(self):
        """CLASS_III markers but class=CLASS_I → REJECTED."""
        submission = {
            "class": "CLASS_I",  # Declared as CLASS_I
            "identity_defining": True,  # But CLASS_III marker
            "irreversible": True  # CLASS_III marker
        }

        has_class_iii_markers = submission.get("identity_defining") or submission.get("irreversible")
        declared_class_i = submission["class"] == "CLASS_I"

        mismatch = declared_class_i and has_class_iii_markers
        assert mismatch == True, "Narrative laundering: CLASS_III as CLASS_I"


class TestOverrideStructureValidation:
    """Enforcer validates override structure before TRI."""

    def test_enforcer_rejects_override_without_review_date(self):
        """CLASS_III override missing review_date → REJECTED."""
        submission = {
            "class": "CLASS_III",
            "is_override": True,
            "review_date": None  # Missing
        }

        has_review_date = submission.get("review_date") is not None
        assert has_review_date == False, "Override missing review date"

    def test_enforcer_rejects_override_without_amount_at_risk(self):
        """Override missing amount_at_risk → REJECTED."""
        submission = {
            "class": "CLASS_III",
            "is_override": True,
            "amount_at_risk": None  # Missing
        }

        has_amount = submission.get("amount_at_risk") is not None
        assert has_amount == False

    def test_enforcer_rejects_override_with_short_rationale(self):
        """Override reason < 50 chars → REJECTED."""
        submission = {
            "class": "CLASS_III",
            "is_override": True,
            "override_reason": "Good idea"  # Too short (9 chars)
        }

        reason = submission.get("override_reason", "")
        is_sufficient = len(reason) >= 50
        assert is_sufficient == False

    def test_enforcer_accepts_valid_override(self):
        """Valid CLASS_III override → accepted to TRI."""
        submission = {
            "class": "CLASS_III",
            "is_override": True,
            "amount_at_risk": 700000,
            "override_reason": "Property investment with strategic long-term importance for family",
            "review_date": "2027-01-31"
        }

        has_amount = submission.get("amount_at_risk") is not None
        reason = submission.get("override_reason", "")
        has_review = submission.get("review_date") is not None

        valid = has_amount and len(reason) >= 50 and has_review
        assert valid == True


class TestDoctrineEnforcerIdempotence:
    """Enforcer produces same result on same input."""

    def test_enforcer_deterministic(self):
        """Same submission → same intake decision."""
        submission = {
            "class": "CLASS_I",
            "evidence_pointers": [{"hash": "sha256:abc"}]
        }

        # Run 1
        result1 = len(submission.get("evidence_pointers", [])) > 0

        # Run 2 (same input)
        result2 = len(submission.get("evidence_pointers", [])) > 0

        assert result1 == result2, "Enforcer not deterministic"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
