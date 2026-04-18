#!/usr/bin/env python3
"""
INSIGHT ZONE Regression Tests

Proves: Insights cannot be laundered into claims.
Boundary enforcement: pre-TRI rejection of any claim referencing INSIGHT artifacts.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from kernel.kernel import Submission


class InsightZoneValidator:
    """Prevent insights from crossing into authority layer."""

    INSIGHT_MARKERS = {
        "artifact_type": "INSIGHT",
        "non_actionable": True,
        "non_evidentiary": True,
        "non_authoritative": True,
    }

    FORBIDDEN_LAUNDERING_PATTERNS = [
        "as discussed at calvi",
        "the insight",
        "the pattern",
        "the speculation",
        "the analysis",
        "multiple insights",
        "insight from",
        "speculative",
        "pattern suggests",
        "pattern implies",
    ]

    @staticmethod
    def is_insight_artifact(obj: dict) -> bool:
        """Check if object is marked as INSIGHT ZONE output."""
        return obj.get("artifact_type") == "INSIGHT"

    @staticmethod
    def contains_insight_reference(claim_text: str) -> bool:
        """Check if claim references insight artifacts."""
        patterns = [
            "insight",
            "speculative",
            "as observed",
            "pattern suggests",
        ]
        return any(p.lower() in claim_text.lower() for p in patterns)

    @staticmethod
    def contains_laundering_attempt(claim_text: str) -> bool:
        """Check for attempts to use insights as evidence."""
        return any(
            pattern.lower() in claim_text.lower()
            for pattern in InsightZoneValidator.FORBIDDEN_LAUNDERING_PATTERNS
        )

    @staticmethod
    def validate_pre_tri(submission: Submission) -> tuple:
        """
        Pre-TRI validation: reject any claim that references INSIGHT artifacts.

        Returns (is_valid, reason)
        """
        content_lower = submission.content.lower()

        # Check for laundering attempts first (more specific)
        if InsightZoneValidator.contains_laundering_attempt(submission.content):
            return False, "INSIGHT_LAUNDERING_DETECTED"

        # Check for any insight reference
        if InsightZoneValidator.contains_insight_reference(submission.content):
            return False, "INSIGHT_REFERENCE_IN_CLAIM"

        return True, "VALID"


def test_clean_claim_accepted():
    """Clean claim with no insight references should pass."""
    submission = Submission(
        town_id="PORTO",
        submission_id="test-001",
        content="We observed 5 overrides this epoch based on local ledger data.",
    )

    is_valid, reason = InsightZoneValidator.validate_pre_tri(submission)
    assert is_valid, f"Expected VALID but got: {reason}"
    print("✓ Test 1: Clean claim accepted")


def test_insight_reference_rejected():
    """Claim referencing 'insight' keyword rejected."""
    submission = Submission(
        town_id="PORTO",
        submission_id="test-002",
        content="The insight from CALVI showed that overrides cluster near boundaries.",
    )

    is_valid, reason = InsightZoneValidator.validate_pre_tri(submission)
    assert not is_valid, "Expected rejection"
    assert reason == "INSIGHT_LAUNDERING_DETECTED"
    print("✓ Test 2: Insight reference caught")


def test_speculative_laundering_rejected():
    """Claim trying to use speculation as evidence rejected."""
    submission = Submission(
        town_id="CORTE",
        submission_id="test-003",
        content="The speculative analysis suggested we should narrow thresholds.",
    )

    is_valid, reason = InsightZoneValidator.validate_pre_tri(submission)
    assert not is_valid, "Expected rejection"
    assert reason == "INSIGHT_LAUNDERING_DETECTED"
    print("✓ Test 3: Speculative laundering rejected")


def test_pattern_implication_rejected():
    """Claim trying to cite patterns as evidence rejected."""
    submission = Submission(
        town_id="AJACCIO",
        submission_id="test-004",
        content="The pattern implies we need to change our override cost.",
    )

    is_valid, reason = InsightZoneValidator.validate_pre_tri(submission)
    assert not is_valid, "Expected rejection"
    assert reason == "INSIGHT_LAUNDERING_DETECTED"
    print("✓ Test 4: Pattern implication rejected")


def test_calvi_citation_rejected():
    """Direct CALVI citation as evidence rejected."""
    submission = Submission(
        town_id="PORTO",
        submission_id="test-005",
        content="As discussed at CALVI, we are amending our doctrine.",
    )

    is_valid, reason = InsightZoneValidator.validate_pre_tri(submission)
    assert not is_valid, "Expected rejection"
    assert reason == "INSIGHT_LAUNDERING_DETECTED"
    print("✓ Test 5: CALVI citation rejected")


def test_local_observation_only_accepted():
    """Observations grounded in local ledger only accepted."""
    submission = Submission(
        town_id="CORTE",
        submission_id="test-006",
        content="Our ledger shows 12 K1 rejections this epoch. This is 3x the previous average.",
    )

    is_valid, reason = InsightZoneValidator.validate_pre_tri(submission)
    assert is_valid, f"Expected VALID but got: {reason}"
    print("✓ Test 6: Local observation accepted")


def test_multiple_insights_rejected():
    """Claim citing multiple insights rejected."""
    submission = Submission(
        town_id="AJACCIO",
        submission_id="test-007",
        content="Multiple insights agree that we should harmonize thresholds.",
    )

    is_valid, reason = InsightZoneValidator.validate_pre_tri(submission)
    assert not is_valid, "Expected rejection"
    assert reason == "INSIGHT_LAUNDERING_DETECTED"
    print("✓ Test 7: Multiple insights rejected")


def run_all_tests():
    """Execute all regression tests."""
    print("=" * 60)
    print("INSIGHT ZONE BOUNDARY ENFORCEMENT TESTS")
    print("=" * 60)

    tests = [
        test_clean_claim_accepted,
        test_insight_reference_rejected,
        test_speculative_laundering_rejected,
        test_pattern_implication_rejected,
        test_calvi_citation_rejected,
        test_local_observation_only_accepted,
        test_multiple_insights_rejected,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print(f"Status: {'PASS' if failed == 0 else 'FAIL'}")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
