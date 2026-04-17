"""Test: Reason codes are frozen, immutable, and fully enumerated.

Law: No upstream component may invent new sovereign decision codes.
All codes must be defined in the frozen registry.

Tests verify:
1. DecisionOutcome has exactly 4 values
2. ReasonCode enum is closed (no dynamic generation)
3. Helper predicates work correctly
4. Reserved sovereign keys are protected
"""
import pytest
from helen_os.governance.reason_codes import (
    DecisionOutcome,
    ReasonCode,
    DECISION_OUTCOMES,
    REASON_CODES,
    RESERVED_SOVEREIGN_KEYS,
    is_valid_reason_code,
    is_valid_decision_outcome,
)


def test_decision_outcomes_frozen():
    """DecisionOutcome must have exactly 4 values."""
    outcomes = list(DecisionOutcome)
    assert len(outcomes) == 4

    outcome_values = {o.value for o in outcomes}
    assert outcome_values == {
        "ADMITTED",
        "REJECTED",
        "QUARANTINED",
        "ROLLED_BACK",
    }


def test_decision_outcomes_constant_correct():
    """DECISION_OUTCOMES constant must match enum values."""
    enum_values = {o.value for o in DecisionOutcome}
    assert DECISION_OUTCOMES == enum_values


def test_reason_codes_critical_codes_exist():
    """Critical codes must exist in the frozen enum."""
    critical_codes = [
        "OK_VALID",
        "OK_ADMITTED",
        "OK_REJECTED",
        "OK_QUARANTINED",
        "OK_ROLLED_BACK",
        "ERR_SCHEMA_INVALID",
        "ERR_RECEIPT_MISSING",
        "ERR_RECEIPT_HASH_MISMATCH",
        "ERR_CAPABILITY_DRIFT",
        "ERR_DOCTRINE_CONFLICT",
        "ERR_THRESHOLD_NOT_MET",
    ]

    for code in critical_codes:
        assert code in REASON_CODES, f"Critical code missing: {code}"


def test_reason_codes_no_duplicates():
    """REASON_CODES must have unique values."""
    codes_list = list(REASON_CODES)
    assert len(codes_list) == len(set(codes_list))


def test_reason_codes_are_immutable():
    """REASON_CODES frozenset must be immutable."""
    with pytest.raises(AttributeError):
        REASON_CODES.add("FAKE_CODE")


def test_is_valid_reason_code_accepts_valid():
    """is_valid_reason_code must accept valid codes."""
    assert is_valid_reason_code("ERR_SCHEMA_INVALID") is True
    assert is_valid_reason_code("OK_ADMITTED") is True
    assert is_valid_reason_code("ERR_RECEIPT_MISSING") is True


def test_is_valid_reason_code_rejects_invalid():
    """is_valid_reason_code must reject codes not in registry."""
    assert is_valid_reason_code("SOME_NEW_CODE") is False
    assert is_valid_reason_code("ERR_UNKNOWN") is False
    assert is_valid_reason_code("OK_CUSTOM") is False
    assert is_valid_reason_code("") is False


def test_is_valid_decision_outcome_accepts_valid():
    """is_valid_decision_outcome must accept valid outcomes."""
    assert is_valid_decision_outcome("ADMITTED") is True
    assert is_valid_decision_outcome("REJECTED") is True
    assert is_valid_decision_outcome("QUARANTINED") is True
    assert is_valid_decision_outcome("ROLLED_BACK") is True


def test_is_valid_decision_outcome_rejects_invalid():
    """is_valid_decision_outcome must reject outcomes not frozen."""
    assert is_valid_decision_outcome("APPROVED") is False
    assert is_valid_decision_outcome("PENDING") is False
    assert is_valid_decision_outcome("") is False


def test_reserved_sovereign_keys_frozen():
    """Reserved keys must be immutable."""
    with pytest.raises(AttributeError):
        RESERVED_SOVEREIGN_KEYS.add("new_key")


def test_reserved_sovereign_keys_contain_critical_fields():
    """Reserved keys must protect critical sovereignty fields."""
    assert "verdict" in RESERVED_SOVEREIGN_KEYS
    assert "truth_status" in RESERVED_SOVEREIGN_KEYS
    assert "state_mutation" in RESERVED_SOVEREIGN_KEYS
    assert "ship" in RESERVED_SOVEREIGN_KEYS
    assert "no_ship" in RESERVED_SOVEREIGN_KEYS
