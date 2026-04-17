"""Test: Verdict/decision leakage rejected at failure bridge."""
from __future__ import annotations

from helen_os.evolution.failure_bridge import route_failure


def test_verdict_leakage_rejected():
    """Failure with sovereign 'decision' field is rejected."""
    leaked = {
        "schema_name": "FAILURE_REPORT_V1",
        "schema_version": "1.0.0",
        "failure_report_id": "F_LEAK",
        "failure_class": "schema_invalid",
        "reason_code": "ERR_SCHEMA_INVALID",
        "typed_failure": {"message": "bad"},
        "decision": "ADMITTED",  # illegal sovereign leakage
    }

    result = route_failure(leaked)
    assert result is None
