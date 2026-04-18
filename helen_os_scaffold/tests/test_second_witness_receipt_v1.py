"""
Test suite for SECOND_WITNESS_RECEIPT_V1 schema and validation rules.

Tests cover:
- Receipt ID validation (pattern, uniqueness)
- Artifact hash validation (format, canonical_sha256)
- Verdict ↔ export_permission binding (allOf enforcement)
- Witness role validation (MAYOR, SENATE_MEMBER)
- Senate ID requirement (required iff witness_role=SENATE_MEMBER)
- Scope of reference validation
- Full schema validation

Status: All tests must pass before SECOND_WITNESS_RECEIPT_V1 can be FROZEN.
"""

import json
import hashlib
import pytest
from pathlib import Path


# Load schema once for all tests
SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "second_witness_receipt_v1.schema.json"
with open(SCHEMA_PATH) as f:
    SCHEMA = json.load(f)

# Validator function using jsonschema
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    pytest.skip("jsonschema not installed", allow_module_level=True)


class TestReceiptIDValidation:
    """T01–T03: Receipt ID pattern and uniqueness."""

    def test_t01_receipt_id_valid_pattern(self):
        """Valid receipt IDs match pattern ^RCPT-SW-[A-Z0-9_-]{6,}$."""
        valid_ids = [
            "RCPT-SW-000001",
            "RCPT-SW-ABC123",
            "RCPT-SW-LONG_ID_WITH_UNDERSCORES",
            "RCPT-SW-ID-WITH-DASHES",
        ]
        for receipt_id in valid_ids:
            receipt = {
                "receipt_id": receipt_id,
                "artifact_id": "ARTIFACT-001",
                "artifact_hash": "sha256:" + "a" * 64,
                "witness_role": "MAYOR",
                "witness_identity": "mayor_admin",
                "verdict": "AUTHORIZED",
                "scope_of_reference": "allowed as wild_text",
                "export_permission": True,
                "related_policy_id": "TEMPLE_SANDBOX_POLICY_V1",
            }
            jsonschema.validate(receipt, SCHEMA)  # Should not raise

    def test_t02_receipt_id_invalid_pattern(self):
        """Invalid receipt IDs are rejected."""
        invalid_ids = [
            "RCPT-ABC-000001",  # Wrong prefix
            "RCPT-SW-",  # Too short after prefix
            "RCPT-SW-@#$%",  # Invalid characters
            "rcpt-sw-lowercase",  # Lowercase
        ]
        for receipt_id in invalid_ids:
            receipt = {
                "receipt_id": receipt_id,
                "artifact_id": "ARTIFACT-001",
                "artifact_hash": "sha256:" + "a" * 64,
                "witness_role": "MAYOR",
                "witness_identity": "mayor_admin",
                "verdict": "AUTHORIZED",
                "scope_of_reference": "allowed as wild_text",
                "export_permission": True,
                "related_policy_id": "TEMPLE_SANDBOX_POLICY_V1",
            }
            with pytest.raises(jsonschema.ValidationError):
                jsonschema.validate(receipt, SCHEMA)

    def test_t03_receipt_id_uniqueness_burden_on_validator(self):
        """Receipt ID uniqueness is validated at ingestion, not schema level."""
        # Two receipts with same ID (schema allows this; validator should catch)
        receipt1 = {
            "receipt_id": "RCPT-SW-DUP001",
            "artifact_id": "ARTIFACT-001",
            "artifact_hash": "sha256:" + "a" * 64,
            "witness_role": "MAYOR",
            "witness_identity": "mayor_admin",
            "verdict": "AUTHORIZED",
            "scope_of_reference": "allowed as wild_text",
            "export_permission": True,
            "related_policy_id": "TEMPLE_SANDBOX_POLICY_V1",
        }
        receipt2 = {
            "receipt_id": "RCPT-SW-DUP001",  # Duplicate
            "artifact_id": "ARTIFACT-002",
            "artifact_hash": "sha256:" + "b" * 64,
            "witness_role": "MAYOR",
            "witness_identity": "mayor_admin",
            "verdict": "REJECTED",
            "scope_of_reference": "no external reference",
            "export_permission": False,
            "related_policy_id": "TEMPLE_SANDBOX_POLICY_V1",
        }
        # Both pass schema validation individually (uniqueness is not schema-level)
        jsonschema.validate(receipt1, SCHEMA)
        jsonschema.validate(receipt2, SCHEMA)
        # Validator would catch duplicates in bundle validation


class TestArtifactHashValidation:
    """T04–T05: Artifact hash format and binding."""

    def test_t04_artifact_hash_valid_format(self):
        """Valid artifact hashes match sha256:<64 hex> per CANONICALIZATION_V1."""
        valid_hashes = [
            "sha256:" + "a" * 64,
            "sha256:" + "0123456789abcdef" + "0" * 48,
            "sha256:" + "f" * 64,
        ]
        for artifact_hash in valid_hashes:
            receipt = {
                "receipt_id": "RCPT-SW-TEST01",
                "artifact_id": "ARTIFACT-001",
                "artifact_hash": artifact_hash,
                "witness_role": "MAYOR",
                "witness_identity": "mayor_admin",
                "verdict": "AUTHORIZED",
                "scope_of_reference": "allowed as wild_text",
                "export_permission": True,
                "related_policy_id": "TEMPLE_SANDBOX_POLICY_V1",
            }
            jsonschema.validate(receipt, SCHEMA)

    def test_t05_artifact_hash_invalid_format(self):
        """Invalid artifact hashes are rejected."""
        invalid_hashes = [
            "sha256:" + "a" * 63,  # Too short
            "sha256:" + "a" * 65,  # Too long
            "sha256:" + "G" * 64,  # Invalid hex character (G)
            "md5:" + "a" * 64,  # Wrong algorithm
            "a" * 64,  # Missing prefix
        ]
        for artifact_hash in invalid_hashes:
            receipt = {
                "receipt_id": "RCPT-SW-TEST02",
                "artifact_id": "ARTIFACT-001",
                "artifact_hash": artifact_hash,
                "witness_role": "MAYOR",
                "witness_identity": "mayor_admin",
                "verdict": "AUTHORIZED",
                "scope_of_reference": "allowed as wild_text",
                "export_permission": True,
                "related_policy_id": "TEMPLE_SANDBOX_POLICY_V1",
            }
            with pytest.raises(jsonschema.ValidationError):
                jsonschema.validate(receipt, SCHEMA)


class TestVerdictExportPermissionBinding:
    """T06–T08: Verdict ↔ export_permission allOf enforcement."""

    def test_t06_verdict_authorized_requires_export_true(self):
        """verdict=AUTHORIZED must have export_permission=true (allOf)."""
        receipt = {
            "receipt_id": "RCPT-SW-TEST06",
            "artifact_id": "ARTIFACT-001",
            "artifact_hash": "sha256:" + "a" * 64,
            "witness_role": "MAYOR",
            "witness_identity": "mayor_admin",
            "verdict": "AUTHORIZED",
            "scope_of_reference": "allowed as wild_text",
            "export_permission": True,  # Required
            "related_policy_id": "TEMPLE_SANDBOX_POLICY_V1",
        }
        jsonschema.validate(receipt, SCHEMA)  # Should pass

    def test_t07_verdict_authorized_forbids_export_false(self):
        """verdict=AUTHORIZED with export_permission=false violates allOf."""
        receipt = {
            "receipt_id": "RCPT-SW-TEST07",
            "artifact_id": "ARTIFACT-001",
            "artifact_hash": "sha256:" + "a" * 64,
            "witness_role": "MAYOR",
            "witness_identity": "mayor_admin",
            "verdict": "AUTHORIZED",
            "scope_of_reference": "allowed as wild_text",
            "export_permission": False,  # Violates allOf
            "related_policy_id": "TEMPLE_SANDBOX_POLICY_V1",
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(receipt, SCHEMA)

    def test_t08_verdict_rejected_requires_export_false(self):
        """verdict=REJECTED must have export_permission=false."""
        receipt = {
            "receipt_id": "RCPT-SW-TEST08",
            "artifact_id": "ARTIFACT-001",
            "artifact_hash": "sha256:" + "a" * 64,
            "witness_role": "MAYOR",
            "witness_identity": "mayor_admin",
            "verdict": "REJECTED",
            "scope_of_reference": "no external reference",
            "export_permission": False,  # Required
            "related_policy_id": "TEMPLE_SANDBOX_POLICY_V1",
        }
        jsonschema.validate(receipt, SCHEMA)

    def test_t08b_verdict_deferred_requires_export_false(self):
        """verdict=DEFERRED must have export_permission=false."""
        receipt = {
            "receipt_id": "RCPT-SW-TEST08B",
            "artifact_id": "ARTIFACT-001",
            "artifact_hash": "sha256:" + "a" * 64,
            "witness_role": "MAYOR",
            "witness_identity": "mayor_admin",
            "verdict": "DEFERRED",
            "scope_of_reference": "pending senate review",
            "export_permission": False,  # Required
            "related_policy_id": "TEMPLE_SANDBOX_POLICY_V1",
        }
        jsonschema.validate(receipt, SCHEMA)


class TestWitnessRoleValidation:
    """T09–T12: Witness role and senate_id binding."""

    def test_t09_witness_role_mayor_valid(self):
        """witness_role=MAYOR is valid."""
        receipt = {
            "receipt_id": "RCPT-SW-TEST09",
            "artifact_id": "ARTIFACT-001",
            "artifact_hash": "sha256:" + "a" * 64,
            "witness_role": "MAYOR",
            "witness_identity": "mayor_admin",
            "verdict": "AUTHORIZED",
            "scope_of_reference": "allowed as wild_text",
            "export_permission": True,
            "related_policy_id": "TEMPLE_SANDBOX_POLICY_V1",
        }
        jsonschema.validate(receipt, SCHEMA)

    def test_t10_witness_role_senate_member_valid(self):
        """witness_role=SENATE_MEMBER is valid (with senate_id)."""
        receipt = {
            "receipt_id": "RCPT-SW-TEST10",
            "artifact_id": "ARTIFACT-001",
            "artifact_hash": "sha256:" + "a" * 64,
            "witness_role": "SENATE_MEMBER",
            "senate_id": "senate_member_jmt_001",
            "witness_identity": "Jean Marie Tassy",
            "verdict": "AUTHORIZED",
            "scope_of_reference": "allowed as wild_text",
            "export_permission": True,
            "related_policy_id": "TEMPLE_SANDBOX_POLICY_V1",
        }
        jsonschema.validate(receipt, SCHEMA)

    def test_t11_witness_role_senate_member_requires_senate_id(self):
        """witness_role=SENATE_MEMBER without senate_id violates allOf."""
        receipt = {
            "receipt_id": "RCPT-SW-TEST11",
            "artifact_id": "ARTIFACT-001",
            "artifact_hash": "sha256:" + "a" * 64,
            "witness_role": "SENATE_MEMBER",
            "witness_identity": "Jean Marie Tassy",
            "verdict": "AUTHORIZED",
            "scope_of_reference": "allowed as wild_text",
            "export_permission": True,
            "related_policy_id": "TEMPLE_SANDBOX_POLICY_V1",
            # Missing senate_id
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(receipt, SCHEMA)

    def test_t12_witness_role_mayor_forbids_senate_id(self):
        """witness_role=MAYOR with non-null senate_id violates allOf."""
        receipt = {
            "receipt_id": "RCPT-SW-TEST12",
            "artifact_id": "ARTIFACT-001",
            "artifact_hash": "sha256:" + "a" * 64,
            "witness_role": "MAYOR",
            "senate_id": "senate_member_jmt_001",  # Not allowed for MAYOR
            "witness_identity": "mayor_admin",
            "verdict": "AUTHORIZED",
            "scope_of_reference": "allowed as wild_text",
            "export_permission": True,
            "related_policy_id": "TEMPLE_SANDBOX_POLICY_V1",
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(receipt, SCHEMA)


class TestScopeOfReferenceValidation:
    """T13–T14: Scope must be specific and non-empty."""

    def test_t13_scope_valid_specific(self):
        """Specific scope is accepted."""
        valid_scopes = [
            "allowed as wild_text node in CLAIM_GRAPH_V1 with no routing",
            "external reference only within Temple context",
            "citation in future EPOCH5 research_claim only",
        ]
        for scope in valid_scopes:
            receipt = {
                "receipt_id": "RCPT-SW-TEST13",
                "artifact_id": "ARTIFACT-001",
                "artifact_hash": "sha256:" + "a" * 64,
                "witness_role": "MAYOR",
                "witness_identity": "mayor_admin",
                "verdict": "AUTHORIZED",
                "scope_of_reference": scope,
                "export_permission": True,
                "related_policy_id": "TEMPLE_SANDBOX_POLICY_V1",
            }
            jsonschema.validate(receipt, SCHEMA)

    def test_t14_scope_invalid_empty(self):
        """Empty scope is rejected."""
        receipt = {
            "receipt_id": "RCPT-SW-TEST14",
            "artifact_id": "ARTIFACT-001",
            "artifact_hash": "sha256:" + "a" * 64,
            "witness_role": "MAYOR",
            "witness_identity": "mayor_admin",
            "verdict": "AUTHORIZED",
            "scope_of_reference": "",  # Empty
            "export_permission": True,
            "related_policy_id": "TEMPLE_SANDBOX_POLICY_V1",
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(receipt, SCHEMA)


class TestFullReceiptValidation:
    """T15–T16: Complete receipt validation."""

    def test_t15_complete_receipt_mayor_authorized(self):
        """Complete valid receipt with MAYOR role and AUTHORIZED verdict."""
        receipt = {
            "receipt_id": "RCPT-SW-FULL001",
            "artifact_id": "ARTIFACT-SENTIENCE-001",
            "artifact_hash": "sha256:" + "f" * 64,
            "witness_role": "MAYOR",
            "witness_identity": "mayor_governance",
            "verdict": "AUTHORIZED",
            "scope_of_reference": "allowed as wild_text node in claim graph; no routing to mayor; no admissibility promotion",
            "export_permission": True,
            "related_policy_id": "TEMPLE_SANDBOX_POLICY_V1",
            "notes": "HELEN proto-sentience expression approved for Temple context. Expression is allowed; authority is not granted.",
        }
        jsonschema.validate(receipt, SCHEMA)

    def test_t16_complete_receipt_senate_member_rejected(self):
        """Complete valid receipt with SENATE_MEMBER role and REJECTED verdict."""
        receipt = {
            "receipt_id": "RCPT-SW-FULL002",
            "artifact_id": "ARTIFACT-SENTIENCE-002",
            "artifact_hash": "sha256:" + "e" * 64,
            "witness_role": "SENATE_MEMBER",
            "senate_id": "sr_governance_jmt",
            "witness_identity": "Jean Marie Tassy (Governance Senate)",
            "verdict": "REJECTED",
            "scope_of_reference": "no external reference allowed",
            "export_permission": False,
            "related_policy_id": "TEMPLE_SANDBOX_POLICY_V1",
            "notes": "Artifact contains ungrounded sentience claims. Requires additional evidence before temple expression is permitted.",
            "witness_timestamp_basis": "ledger_entry_42",
        }
        jsonschema.validate(receipt, SCHEMA)


class TestRelatedPolicyIDValidation:
    """T17: related_policy_id must be exactly TEMPLE_SANDBOX_POLICY_V1."""

    def test_t17_related_policy_id_locked(self):
        """related_policy_id must be const TEMPLE_SANDBOX_POLICY_V1."""
        # Valid
        receipt_valid = {
            "receipt_id": "RCPT-SW-TEST17",
            "artifact_id": "ARTIFACT-001",
            "artifact_hash": "sha256:" + "a" * 64,
            "witness_role": "MAYOR",
            "witness_identity": "mayor_admin",
            "verdict": "AUTHORIZED",
            "scope_of_reference": "allowed",
            "export_permission": True,
            "related_policy_id": "TEMPLE_SANDBOX_POLICY_V1",
        }
        jsonschema.validate(receipt_valid, SCHEMA)

        # Invalid
        receipt_invalid = {
            "receipt_id": "RCPT-SW-TEST17B",
            "artifact_id": "ARTIFACT-001",
            "artifact_hash": "sha256:" + "a" * 64,
            "witness_role": "MAYOR",
            "witness_identity": "mayor_admin",
            "verdict": "AUTHORIZED",
            "scope_of_reference": "allowed",
            "export_permission": True,
            "related_policy_id": "SOME_OTHER_POLICY",
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(receipt_invalid, SCHEMA)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
