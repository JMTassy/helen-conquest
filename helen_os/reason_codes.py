"""
reason_codes.py - Frozen reason code registry.

Constitutional rule: Reducer outputs may not contain ad hoc strings.
All promotion decisions and failure reports use only these frozen codes.

This prevents semantic drift in governance decisions.
"""

# Failure/rejection reason codes
# Used when a skill promotion is rejected or fails validation
FAILURE_CODES = {
    "ERR_SCHEMA_INVALID": "Packet or receipt failed JSON schema validation",
    "ERR_RECEIPT_MISSING": "Referenced receipt does not exist or cannot be resolved",
    "ERR_RECEIPT_HASH_MISMATCH": "Receipt hash does not match computed value",
    "ERR_CAPABILITY_DRIFT": "Declared capability inconsistent with actual behavior",
    "ERR_DOCTRINE_CONFLICT": "Packet violates active doctrine or law surface",
    "ERR_THRESHOLD_NOT_MET": "Evaluation metric did not exceed required threshold",
    "ERR_ROLLBACK_TRIGGER": "Prior skill version triggered rollback condition",
}

# Success reason codes
# Used when a skill promotion is accepted or quarantined
SUCCESS_CODES = {
    "OK_ADMITTED": "All gates passed, skill admitted to active library",
    "OK_QUARANTINED": "Performance promising but evidence incomplete, quarantine recommended",
}

# Combined registry (for reducer validation)
ALL_CODES = {**FAILURE_CODES, **SUCCESS_CODES}

# Decision-to-code mapping (which codes are valid for which decisions)
CODE_BY_DECISION = {
    "ADMITTED": ["OK_ADMITTED"],
    "REJECTED": [
        "ERR_SCHEMA_INVALID",
        "ERR_RECEIPT_MISSING",
        "ERR_RECEIPT_HASH_MISMATCH",
        "ERR_CAPABILITY_DRIFT",
        "ERR_DOCTRINE_CONFLICT",
        "ERR_THRESHOLD_NOT_MET",
        "ERR_ROLLBACK_TRIGGER",
    ],
    "QUARANTINED": ["OK_QUARANTINED"],
    "ROLLED_BACK": ["ERR_ROLLBACK_TRIGGER"],
}


def is_valid_code(code: str) -> bool:
    """Check if code is in frozen registry."""
    return code in ALL_CODES


def is_valid_decision_code(decision: str, code: str) -> bool:
    """Check if code is valid for given decision."""
    valid_codes = CODE_BY_DECISION.get(decision, [])
    return code in valid_codes


def get_code_description(code: str) -> str:
    """Get human-readable description of reason code."""
    return ALL_CODES.get(code, "UNKNOWN CODE")


# Export public API
__all__ = [
    "FAILURE_CODES",
    "SUCCESS_CODES",
    "ALL_CODES",
    "CODE_BY_DECISION",
    "is_valid_code",
    "is_valid_decision_code",
    "get_code_description",
]
