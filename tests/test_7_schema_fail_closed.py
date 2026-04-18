"""
Constitutional Test 7: Schema Validation is Fail-Closed

This test proves that boundary objects MUST conform to their schemas.
Invalid payloads cannot reach the Mayor or UI.

Test Strategy:
1. Construct invalid payloads (missing required fields, wrong types)
2. Call validate_or_raise()
3. Assert SchemaValidationError is raised

Receipt Value:
- Proves "schemas exist" is upgraded to "schemas are enforced"
- Prevents sloppy payloads from contaminating governance
- Enforces fail-closed semantics (no rescue, no fallback)
"""
from __future__ import annotations

import pytest

from oracle_town.core.schema_validation import SchemaValidationError, validate_or_raise


def test_ui_event_stream_schema_fail_closed_missing_required():
    """UI event stream with missing required fields must fail"""
    bad = {
        "schema_version": "1.0.0",
        "stream_id": "UIS-ABCDEF12",
        # Missing: run_id, created_at, ui_mode, events, hashes, constraints
    }
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_or_raise(bad, "ui_event_stream.schema.json")

    assert "ui_event_stream.schema.json" in str(exc_info.value)


def test_ui_event_stream_schema_fail_closed_wrong_type():
    """UI event stream with wrong type must fail"""
    bad = {
        "schema_version": "1.0.0",
        "stream_id": "UIS-ABCDEF12",
        "run_id": "RUN-001",
        "created_at": "2026-01-22T12:00:00Z",
        "ui_mode": "invalid_mode",  # Must be control_room / town_view / hybrid
        "events": [],
        "hashes": {"stream_sha256": "a" * 64},
        "constraints": {"non_sovereign": True, "no_attestation_forgery": True},
    }
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_or_raise(bad, "ui_event_stream.schema.json")

    assert "ui_mode" in str(exc_info.value).lower()


def test_ui_event_stream_schema_fail_closed_additional_properties():
    """UI event stream with additional properties must fail (additionalProperties: false)"""
    bad = {
        "schema_version": "1.0.0",
        "stream_id": "UIS-ABCDEF12",
        "run_id": "RUN-001",
        "created_at": "2026-01-22T12:00:00Z",
        "ui_mode": "control_room",
        "events": [],
        "hashes": {"stream_sha256": "a" * 64},
        "constraints": {"non_sovereign": True, "no_attestation_forgery": True},
        "sneaky_field": "this should fail",  # Not allowed
    }
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_or_raise(bad, "ui_event_stream.schema.json")

    # Schema should reject additional properties
    assert "additional" in str(exc_info.value).lower() or "sneaky_field" in str(exc_info.value).lower()


def test_ci_receipt_bundle_schema_fail_closed_missing_required():
    """CI receipt bundle with missing required fields must fail"""
    bad = {
        "schema_version": "1.0.0",
        "bundle_id": "RCPT-ABCDEF12",
        # Missing: run_id, briefcase_id, created_at, provenance, executions, attestations, hashes, constraints
    }
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_or_raise(bad, "ci_receipt_bundle.schema.json")

    assert "ci_receipt_bundle.schema.json" in str(exc_info.value)


def test_ci_receipt_bundle_schema_fail_closed_wrong_attestation_status():
    """CI receipt bundle with invalid attestation status must fail"""
    bad = {
        "schema_version": "1.0.0",
        "bundle_id": "RCPT-ABCDEF12",
        "run_id": "RUN-001",
        "briefcase_id": "BFC-001",
        "created_at": "2026-01-22T12:00:00Z",
        "provenance": {
            "attestor_id": "CI_RUNNER",
            "attestor_kind": "CI_RUNNER",
            "repo": {"name": "oracle-town", "url_or_origin": "https://example.com"},
            "git": {"commit_sha": "a" * 40, "dirty": False},
            "runtime": {"os": "linux", "arch": "x86_64", "container_image": "", "working_dir": "/app"},
            "tool_versions": {"python": "3.11", "pytest": "7.0"},
        },
        "executions": [
            {
                "exec_id": "EX-ABC123",
                "test_id": "T-001",
                "command": "pytest",
                "started_at": "2026-01-22T12:00:00Z",
                "ended_at": "2026-01-22T12:01:00Z",
                "exit_code": 0,
                "status": "PASS",
                "io_hashes": {"stdout_sha256": "a" * 64, "stderr_sha256": "b" * 64},
                "artifacts": [],
            }
        ],
        "attestations": [
            {
                "attestation_id": "ATT-001",
                "obligation_name": "tests_green",
                "expected_attestor": "CI_RUNNER",
                "status": "MAYBE",  # Invalid! Must be PASS or FAIL
                "based_on_exec_ids": ["EX-ABC123"],
                "evidence": {
                    "bundle_ref": {"bundle_id": "RCPT-ABCDEF12", "sha256": "a" * 64},
                    "exec_refs": [{"exec_id": "EX-ABC123"}],
                },
                "created_at": "2026-01-22T12:01:00Z",
            }
        ],
        "hashes": {"canonical_sha256": "a" * 64},
        "constraints": {"deterministic": True, "no_confidence_fields": True, "no_mayor_imports_claimed": True},
    }
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_or_raise(bad, "ci_receipt_bundle.schema.json")

    # Should reject status="MAYBE" (only PASS/FAIL allowed)
    assert "status" in str(exc_info.value).lower()


def test_ci_receipt_bundle_schema_fail_closed_confidence_field_forbidden():
    """CI receipt bundle must not contain confidence fields (no_confidence_fields: true)"""
    # Note: This test documents intent; the schema doesn't have a way to ban
    # arbitrary keys in payloads. The constraint field is documentary.
    # Real enforcement requires code review + AST scanning for "confidence" keyword.

    bad = {
        "schema_version": "1.0.0",
        "bundle_id": "RCPT-ABCDEF12",
        "run_id": "RUN-001",
        "briefcase_id": "BFC-001",
        "created_at": "2026-01-22T12:00:00Z",
        "provenance": {
            "attestor_id": "CI_RUNNER",
            "attestor_kind": "CI_RUNNER",
            "repo": {"name": "oracle-town", "url_or_origin": "https://example.com"},
            "git": {"commit_sha": "a" * 40, "dirty": False},
            "runtime": {"os": "linux", "arch": "x86_64", "container_image": "", "working_dir": "/app"},
            "tool_versions": {"python": "3.11", "pytest": "7.0"},
        },
        "executions": [
            {
                "exec_id": "EX-ABC123",
                "test_id": "T-001",
                "command": "pytest",
                "started_at": "2026-01-22T12:00:00Z",
                "ended_at": "2026-01-22T12:01:00Z",
                "exit_code": 0,
                "status": "PASS",
                "io_hashes": {"stdout_sha256": "a" * 64, "stderr_sha256": "b" * 64},
                "artifacts": [],
                "confidence": 0.95,  # Forbidden!
            }
        ],
        "attestations": [
            {
                "attestation_id": "ATT-001",
                "obligation_name": "tests_green",
                "expected_attestor": "CI_RUNNER",
                "status": "PASS",
                "based_on_exec_ids": ["EX-ABC123"],
                "evidence": {
                    "bundle_ref": {"bundle_id": "RCPT-ABCDEF12", "sha256": "a" * 64},
                    "exec_refs": [{"exec_id": "EX-ABC123"}],
                },
                "created_at": "2026-01-22T12:01:00Z",
            }
        ],
        "hashes": {"canonical_sha256": "a" * 64},
        "constraints": {"deterministic": True, "no_confidence_fields": True, "no_mayor_imports_claimed": True},
    }

    with pytest.raises(SchemaValidationError) as exc_info:
        validate_or_raise(bad, "ci_receipt_bundle.schema.json")

    # additionalProperties: false should reject "confidence" field
    assert "additional" in str(exc_info.value).lower() or "confidence" in str(exc_info.value).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
