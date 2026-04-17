"""Test: Failure bridge only accepts schema-valid FAILURE_REPORT_V1."""
from __future__ import annotations

from helen_os.governance.validators import validate_schema


def test_untyped_failure_rejected():
    """Untyped failures (random dicts) are rejected."""
    raw = {"error": "something", "type": "unknown"}
    valid, _ = validate_schema("FAILURE_REPORT_V1", "1.0.0", raw)
    assert not valid


def test_typed_failure_accepted():
    """Schema-valid FAILURE_REPORT_V1 is accepted."""
    raw = {
        "schema_name": "FAILURE_REPORT_V1",
        "schema_version": "1.0.0",
        "failure_report_id": "F1",
        "failure_class": "SCHEMA_MISMATCH",
        "reason_code": "ERR_SCHEMA_INVALID",
        "typed_failure": {"message": "test", "detected_at": "2026-03-13T00:00:00Z"},
    }
    valid, err = validate_schema("FAILURE_REPORT_V1", "1.0.0", raw)
    assert valid, f"expected valid, got error: {err}"


def test_failure_report_with_extra_field_rejected():
    """Extra fields cause rejection (additionalProperties: false)."""
    raw = {
        "schema_name": "FAILURE_REPORT_V1",
        "schema_version": "1.0.0",
        "failure_report_id": "F1",
        "failure_class": "SCHEMA_MISMATCH",
        "reason_code": "ERR_SCHEMA_INVALID",
        "typed_failure": {"message": "test", "detected_at": "2026-03-13T00:00:00Z"},
        "extra_field": "should_not_be_here",
    }
    valid, _ = validate_schema("FAILURE_REPORT_V1", "1.0.0", raw)
    assert not valid


def test_failure_report_missing_required_field():
    """Missing required fields cause rejection."""
    raw = {
        "schema_name": "FAILURE_REPORT_V1",
        "schema_version": "1.0.0",
        "failure_report_id": "F1",
        # missing failure_class
        "reason_code": "ERR_SCHEMA_INVALID",
        "typed_failure": {"message": "test", "detected_at": "2026-03-13T00:00:00Z"},
    }
    valid, _ = validate_schema("FAILURE_REPORT_V1", "1.0.0", raw)
    assert not valid
