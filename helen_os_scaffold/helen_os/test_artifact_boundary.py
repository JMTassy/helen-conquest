"""
test_artifact_boundary.py — Phase 2: Constitutional Boundary Tests

Tests that verify BUILDERS artifacts cannot leak sovereign state.
Tests that deterministic replay is stable under key reordering.
Tests that the artifact-law boundary is enforced at validation time.

These tests prove the first receipt-bearing system is working.
"""

import pytest
from helen_os.artifact import (
    ArtifactValidationError,
    InvariantViolation,
    SchemaValidationError,
    validate_artifact,
    canonical_json_bytes,
    sha256_hex,
)


class TestNonSovereignAttestationEnforced:
    """Non-sovereignty attestation is mandatory. HELEN_HANDOFF_V1 enforces all false."""

    def test_helen_handoff_with_verdict_emitted_true_rejected(self):
        """HELEN_HANDOFF_V1 with verdict_emitted=True must be rejected by schema."""
        payload = {
            "schema_version": "HELEN_HANDOFF_V1",
            "canonicalization": "JCS_SHA256_V1",
            "handoff_id": "HANDOFF-001",
            "source_system": "ORACLE_SUPER_2_BUILDERS",
            "run_id": "RUN-001",
            "brief_id": "BRIEF-001",
            "artifact_bundle_ref": "artifact_bundle.json",
            "final_artifact_ref": "final_artifact.md",
            "claims_log_ref": "claims_log.json",
            "phase_log_ref": "phase_log.json",
            "abort_report_ref": None,
            "payload_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "source_refs": [],
            "evidence_refs": [],
            "open_risks": [],
            "non_sovereign_attestation": {
                "verdict_emitted": True,  # ❌ FORBIDDEN by const: false
                "truth_claimed": False,
                "doctrine_mutated": False,
            },
        }

        # Schema validation enforces const: false via JSON Schema
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_artifact("helen_handoff_v1", payload)

        # Error should indicate false was expected
        assert "false" in str(exc_info.value).lower()

    def test_helen_handoff_with_truth_claimed_true_rejected(self):
        """HELEN_HANDOFF_V1 with truth_claimed=True must be rejected by schema."""
        payload = {
            "schema_version": "HELEN_HANDOFF_V1",
            "canonicalization": "JCS_SHA256_V1",
            "handoff_id": "HANDOFF-002",
            "source_system": "ORACLE_SUPER_2_BUILDERS",
            "run_id": "RUN-002",
            "brief_id": "BRIEF-002",
            "artifact_bundle_ref": "artifact_bundle.json",
            "final_artifact_ref": "final_artifact.md",
            "claims_log_ref": "claims_log.json",
            "phase_log_ref": "phase_log.json",
            "abort_report_ref": None,
            "payload_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "source_refs": [],
            "evidence_refs": [],
            "open_risks": [],
            "non_sovereign_attestation": {
                "verdict_emitted": False,
                "truth_claimed": True,  # ❌ FORBIDDEN by const: false
                "doctrine_mutated": False,
            },
        }

        # Schema validation enforces const: false via JSON Schema
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_artifact("helen_handoff_v1", payload)

        # Error should indicate false was expected
        assert "false" in str(exc_info.value).lower()

    def test_helen_handoff_with_doctrine_mutated_true_rejected(self):
        """HELEN_HANDOFF_V1 with doctrine_mutated=True must be rejected by schema."""
        payload = {
            "schema_version": "HELEN_HANDOFF_V1",
            "canonicalization": "JCS_SHA256_V1",
            "handoff_id": "HANDOFF-003",
            "source_system": "ORACLE_SUPER_2_BUILDERS",
            "run_id": "RUN-003",
            "brief_id": "BRIEF-003",
            "artifact_bundle_ref": "artifact_bundle.json",
            "final_artifact_ref": "final_artifact.md",
            "claims_log_ref": "claims_log.json",
            "phase_log_ref": "phase_log.json",
            "abort_report_ref": None,
            "payload_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            "source_refs": [],
            "evidence_refs": [],
            "open_risks": [],
            "non_sovereign_attestation": {
                "verdict_emitted": False,
                "truth_claimed": False,
                "doctrine_mutated": True,  # ❌ FORBIDDEN by const: false
            },
        }

        # Schema validation enforces const: false via JSON Schema
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_artifact("helen_handoff_v1", payload)

        # Error should indicate false was expected
        assert "false" in str(exc_info.value).lower()


class TestKeyReorderingPreservesPayloadHash:
    """Same semantic object with reordered keys yields identical payload_hash."""

    def test_canonical_json_bytes_preserves_hash_under_key_reordering(self):
        """Verify that canonical serialization produces stable hashes."""
        # Create a payload with keys in one order
        payload_1 = {
            "z_field": "last",
            "a_field": "first",
            "m_field": "middle",
            "canonicalization": "JCS_SHA256_V1",
        }

        # Create identical payload with keys in different order
        payload_2 = {
            "canonicalization": "JCS_SHA256_V1",
            "m_field": "middle",
            "z_field": "last",
            "a_field": "first",
        }

        # Canonical hashes must be identical
        bytes_1 = canonical_json_bytes(payload_1)
        bytes_2 = canonical_json_bytes(payload_2)

        assert bytes_1 == bytes_2, "Key reordering should not change canonical bytes"

        hash_1 = sha256_hex(bytes_1)
        hash_2 = sha256_hex(bytes_2)

        assert hash_1 == hash_2, "Key reordering should not change payload hash"


class TestValidHandoffPreservesHashIntegrity:
    """Valid HELEN_HANDOFF_V1 artifact returns stable hash."""

    def test_valid_handoff_artifact_returns_stable_hash(self):
        """Validate a correct HELEN_HANDOFF_V1 and verify hash output."""
        payload = {
            "schema_version": "HELEN_HANDOFF_V1",
            "canonicalization": "JCS_SHA256_V1",
            "handoff_id": "HANDOFF-001",
            "source_system": "ORACLE_SUPER_2_BUILDERS",
            "run_id": "RUN-001",
            "brief_id": "BRIEF-001",
            "artifact_bundle_ref": "artifact_bundle.json",
            "final_artifact_ref": "final_artifact.md",
            "claims_log_ref": "claims_log.json",
            "phase_log_ref": "phase_log.json",
            "abort_report_ref": None,
            "payload_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "source_refs": [],
            "evidence_refs": [],
            "open_risks": [],
            "non_sovereign_attestation": {
                "verdict_emitted": False,
                "truth_claimed": False,
                "doctrine_mutated": False,
            },
        }

        # Should validate successfully
        result = validate_artifact("helen_handoff_v1", payload)

        # Should return receipt-like object
        assert result["artifact_type"] == "helen_handoff_v1"
        assert result["canonicalization"] == "JCS_SHA256_V1"
        assert result["validated"] is True
        assert isinstance(result["payload_hash"], str)
        assert len(result["payload_hash"]) == 64  # SHA-256 hex is 64 chars

        # Revalidate same payload should produce same hash
        result_2 = validate_artifact("helen_handoff_v1", payload)
        assert result["payload_hash"] == result_2["payload_hash"]


class TestCanonicalizeationLabelFrozen:
    """Canonicalization label must be exactly JCS_SHA256_V1."""

    def test_wrong_canonicalization_label_rejected(self):
        """Any other canonicalization label must be rejected by schema."""
        payload = {
            "schema": "MISSION_V1",
            "mission_id": "M-001",
            "proposal_id": "P-001",
            "kind": "RESEARCH",
            "objective": "Test mission",
            "constraints": [],
            "inputs": [],
            "steps": [{"step_id": "S1", "action": "test", "expected_receipt_type": "EXECUTION_RECEIPT_V1"}],
            "status": "PLANNED",
            "canonicalization": "WRONG_LABEL",  # ❌ Not the frozen label
        }

        # Schema validation enforces const: "JCS_SHA256_V1" via JSON Schema
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_artifact("mission_v1", payload)

        # Error message should indicate the expected value
        assert "jcs_sha256_v1" in str(exc_info.value).lower()
        assert "expected" in str(exc_info.value).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
