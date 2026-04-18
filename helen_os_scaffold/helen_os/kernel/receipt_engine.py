"""
receipt_engine.py — Shared Receipt Verification Engine (Phase 3)

Unified receipt computation and verification across all VMs.
Implements spec UNIFIED_CI_REPLAY_HARNESS_V0 § 8.

Frozen rule: receipt_sha256 == sha256_jcs(artifact without receipt_sha256)
"""

from typing import Any, Dict
from helen_os.artifact import canonical_json_bytes, sha256_hex


def compute_receipt_sha256(artifact_without_receipt: Dict[str, Any]) -> str:
    """
    Compute receipt SHA-256 for artifact before receipt field is added.

    Args:
        artifact_without_receipt: Artifact dict (must NOT contain receipt_sha256)

    Returns:
        Hex SHA-256 digest of canonical artifact bytes.
    """
    canonical_bytes = canonical_json_bytes(artifact_without_receipt)
    return sha256_hex(canonical_bytes)


def verify_receipt(artifact: Dict[str, Any]) -> bool:
    """
    Verify receipt hash: receipt_sha256 == sha256_jcs(artifact without receipt_sha256).

    This is the authoritative receipt verification function used by all VMs.

    Args:
        artifact: Artifact dict (must contain receipt_sha256 field)

    Returns:
        True if receipt is valid, False otherwise.

    Raises:
        KeyError if artifact does not have receipt_sha256 field.
    """
    receipt_sha256 = artifact["receipt_sha256"]

    # Remove receipt field to compute expected hash
    without_receipt = {k: v for k, v in artifact.items() if k != "receipt_sha256"}

    # Compute expected receipt
    expected = compute_receipt_sha256(without_receipt)

    # Compare
    return receipt_sha256 == expected


def add_receipt_to_artifact(artifact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute receipt hash and add receipt_sha256 field to artifact.

    Args:
        artifact: Artifact dict (must NOT contain receipt_sha256)

    Returns:
        Artifact with receipt_sha256 field added.
    """
    receipt = compute_receipt_sha256(artifact)
    return {**artifact, "receipt_sha256": receipt}


def validate_artifact_with_receipt(artifact: Dict[str, Any]) -> tuple[bool, str]:
    """
    Full validation: verify receipt and ensure artifact structure is valid.

    Args:
        artifact: Artifact dict with receipt_sha256 field

    Returns:
        (is_valid: bool, reason: str)
    """
    if not isinstance(artifact, dict):
        return False, "artifact_not_dict"

    if "receipt_sha256" not in artifact:
        return False, "missing_receipt_sha256"

    if not verify_receipt(artifact):
        return False, "receipt_verification_failed"

    return True, "ok"
