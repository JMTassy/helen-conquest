"""Failure bridge: Routes only schema-valid FAILURE_REPORT_V1 failures.

Untyped failures and failures with leaked sovereign fields are dropped.
"""
from __future__ import annotations

from typing import Any, Mapping

from helen_os.governance.validators import validate_schema


def route_failure(raw: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """
    Route only schema-valid, uncontaminated failures.

    Rules:
    - Failure must be valid FAILURE_REPORT_V1
    - No sovereign fields (e.g., "decision", "receipt_hash") allowed
    - Untyped failures dropped (return None)
    - Contaminated failures dropped (return None)

    Args:
        raw: Raw failure object

    Returns:
        Typed failure object or None if invalid/contaminated
    """
    # Gate 1: Schema validity
    valid, _ = validate_schema("FAILURE_REPORT_V1", "1.0.0", raw)
    if not valid:
        return None

    # Gate 2: No sovereign leakage
    # Failures must not contain sovereign fields
    forbidden_keys = {"decision", "receipt_hash", "verdict", "approved"}
    if any(k in raw for k in forbidden_keys):
        return None

    return dict(raw)
