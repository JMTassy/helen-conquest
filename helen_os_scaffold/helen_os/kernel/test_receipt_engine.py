"""
test_receipt_engine.py — Receipt Engine Tests

Unit tests for the shared receipt verification engine.
Verifies that receipts are correctly computed and verified across all scenarios.
"""

import pytest
from helen_os.kernel.receipt_engine import (
    compute_receipt_sha256,
    verify_receipt,
    add_receipt_to_artifact,
    validate_artifact_with_receipt,
)


class TestReceiptComputation:
    """Test receipt SHA-256 computation."""

    def test_receipt_computation_basic(self):
        """Compute receipt for simple artifact."""
        artifact = {
            "schema_version": "MANIFEST_V1",
            "data": {"value": 42},
        }

        receipt = compute_receipt_sha256(artifact)

        # Receipt should be 64-char hex string
        assert isinstance(receipt, str)
        assert len(receipt) == 64
        assert all(c in "0123456789abcdef" for c in receipt)

    def test_receipt_computation_deterministic(self):
        """Compute receipt twice for same artifact, must be identical."""
        artifact = {
            "schema_version": "MANIFEST_V1",
            "data": {"value": 42},
        }

        receipt1 = compute_receipt_sha256(artifact)
        receipt2 = compute_receipt_sha256(artifact)

        assert receipt1 == receipt2

    def test_receipt_computation_order_independent(self):
        """Receipt must be independent of key order (JCS canonicalization)."""
        artifact_a = {
            "a": 1,
            "b": 2,
            "c": 3,
        }

        artifact_b = {
            "c": 3,
            "a": 1,
            "b": 2,
        }

        receipt_a = compute_receipt_sha256(artifact_a)
        receipt_b = compute_receipt_sha256(artifact_b)

        # Both should compute identical receipt (same semantic content)
        assert receipt_a == receipt_b

    def test_receipt_computation_detects_changes(self):
        """Different artifacts must produce different receipts."""
        artifact1 = {"data": {"value": 42}}
        artifact2 = {"data": {"value": 43}}

        receipt1 = compute_receipt_sha256(artifact1)
        receipt2 = compute_receipt_sha256(artifact2)

        assert receipt1 != receipt2


class TestReceiptVerification:
    """Test receipt verification."""

    def test_receipt_verification_valid(self):
        """Valid receipt must pass verification."""
        artifact = {
            "schema_version": "MANIFEST_V1",
            "data": {"value": 42},
        }

        # Compute and add receipt
        receipt = compute_receipt_sha256(artifact)
        artifact_with_receipt = {**artifact, "receipt_sha256": receipt}

        # Verify
        assert verify_receipt(artifact_with_receipt)

    def test_receipt_verification_invalid(self):
        """Invalid receipt must fail verification."""
        artifact = {
            "schema_version": "MANIFEST_V1",
            "data": {"value": 42},
            "receipt_sha256": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        }

        # This receipt is wrong (doesn't match content)
        assert not verify_receipt(artifact)

    def test_receipt_verification_missing_field(self):
        """Artifact without receipt_sha256 should raise KeyError."""
        artifact = {
            "schema_version": "MANIFEST_V1",
            "data": {"value": 42},
        }

        with pytest.raises(KeyError):
            verify_receipt(artifact)

    def test_receipt_verification_detects_tampering(self):
        """Changing artifact content must make receipt invalid."""
        artifact = {
            "schema_version": "MANIFEST_V1",
            "data": {"value": 42},
        }

        # Compute receipt
        receipt = compute_receipt_sha256(artifact)
        artifact_with_receipt = {**artifact, "receipt_sha256": receipt}

        # Verify is valid
        assert verify_receipt(artifact_with_receipt)

        # Tamper with data
        artifact_with_receipt["data"]["value"] = 99

        # Verification must fail
        assert not verify_receipt(artifact_with_receipt)


class TestAddReceiptToArtifact:
    """Test adding receipt to artifact."""

    def test_add_receipt_basic(self):
        """Add receipt to artifact."""
        artifact = {
            "schema_version": "MANIFEST_V1",
            "data": {"value": 42},
        }

        result = add_receipt_to_artifact(artifact)

        # Result should have receipt_sha256 field
        assert "receipt_sha256" in result
        assert result["receipt_sha256"] != ""

        # Original fields should be preserved
        assert result["schema_version"] == "MANIFEST_V1"
        assert result["data"] == {"value": 42}

    def test_add_receipt_no_mutation(self):
        """Adding receipt must not mutate original artifact."""
        artifact = {
            "schema_version": "MANIFEST_V1",
            "data": {"value": 42},
        }

        original_keys = set(artifact.keys())

        result = add_receipt_to_artifact(artifact)

        # Original must not have receipt
        assert "receipt_sha256" not in artifact
        assert set(artifact.keys()) == original_keys

        # Result must have receipt
        assert "receipt_sha256" in result

    def test_add_receipt_result_verifiable(self):
        """Artifact with added receipt must be verifiable."""
        artifact = {
            "schema_version": "MANIFEST_V1",
            "data": {"value": 42},
        }

        result = add_receipt_to_artifact(artifact)

        # Must pass verification
        assert verify_receipt(result)


class TestValidateArtifactWithReceipt:
    """Test full artifact validation."""

    def test_validate_artifact_valid(self):
        """Valid artifact must pass validation."""
        artifact = {
            "schema_version": "MANIFEST_V1",
            "data": {"value": 42},
        }

        artifact = add_receipt_to_artifact(artifact)

        is_valid, reason = validate_artifact_with_receipt(artifact)

        assert is_valid
        assert reason == "ok"

    def test_validate_artifact_not_dict(self):
        """Non-dict artifact must fail."""
        is_valid, reason = validate_artifact_with_receipt("not a dict")

        assert not is_valid
        assert reason == "artifact_not_dict"

    def test_validate_artifact_missing_receipt(self):
        """Artifact without receipt must fail."""
        artifact = {
            "schema_version": "MANIFEST_V1",
            "data": {"value": 42},
        }

        is_valid, reason = validate_artifact_with_receipt(artifact)

        assert not is_valid
        assert reason == "missing_receipt_sha256"

    def test_validate_artifact_invalid_receipt(self):
        """Artifact with invalid receipt must fail."""
        artifact = {
            "schema_version": "MANIFEST_V1",
            "data": {"value": 42},
            "receipt_sha256": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        }

        is_valid, reason = validate_artifact_with_receipt(artifact)

        assert not is_valid
        assert reason == "receipt_verification_failed"


class TestReceiptComplexStructures:
    """Test receipts with complex artifact structures."""

    def test_receipt_nested_objects(self):
        """Receipts must handle nested objects correctly."""
        artifact = {
            "metadata": {
                "version": "v1",
                "nested": {
                    "deep": {
                        "value": 42,
                    }
                }
            },
            "data": [1, 2, 3],
        }

        artifact = add_receipt_to_artifact(artifact)
        assert verify_receipt(artifact)

    def test_receipt_arrays(self):
        """Receipts must handle arrays correctly."""
        artifact = {
            "items": [
                {"id": 1, "name": "a"},
                {"id": 2, "name": "b"},
                {"id": 3, "name": "c"},
            ]
        }

        artifact = add_receipt_to_artifact(artifact)
        assert verify_receipt(artifact)

    def test_receipt_mixed_types(self):
        """Receipts must handle mixed types correctly."""
        artifact = {
            "string": "value",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "null": None,
            "array": [1, "two", 3.0],
            "object": {"nested": "value"},
        }

        artifact = add_receipt_to_artifact(artifact)
        assert verify_receipt(artifact)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
