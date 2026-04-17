"""
validators.py - Strict validators enforcing constitutional rules.

These validators go beyond JSON Schema:
- Check for forbidden fields (verdict, truth claims, doctrine mutations)
- Enforce non-sovereignty attestation
- Verify hash formats
- Check for undeclared extra fields

Constitutional rule: Any artifact entering the kernel must pass these checks.
"""

from typing import Any, Dict, List, Set


class ValidationError(Exception):
    """Raised when artifact fails constitutional validation."""
    pass


def check_no_forbidden_fields(artifact: Dict[str, Any], forbidden: Set[str]) -> None:
    """
    Check that artifact does not contain forbidden fields.

    Used to enforce non-sovereignty: production artifacts must not contain
    verdicts, truth claims, or doctrine mutations.

    Args:
        artifact: The artifact to check
        forbidden: Set of forbidden field names

    Raises:
        ValidationError if any forbidden field is found
    """
    for field in forbidden:
        if field in artifact:
            raise ValidationError(
                f"Forbidden field '{field}' found in artifact. "
                f"Production layer cannot emit verdicts or claim truth."
            )

        # Also check nested objects
        for key, value in artifact.items():
            if isinstance(value, dict):
                check_no_forbidden_fields(value, forbidden)


def check_non_sovereign_attestation(artifact: Dict[str, Any]) -> None:
    """
    Verify non_sovereign_attestation fields are all false.

    This is the membrane's primary defense: production layer must declare
    that it is NOT sovereign (no verdict, no truth, no doctrine mutation).
    """
    attestation = artifact.get("non_sovereign_attestation", {})

    required_false_fields = [
        "verdict_emitted",
        "truth_claimed",
        "doctrine_mutated",
    ]

    for field in required_false_fields:
        value = attestation.get(field)
        if value is not True:  # Expect False explicitly
            raise ValidationError(
                f"non_sovereign_attestation.{field} must be false, "
                f"got {value}. Production layer cannot claim sovereignty."
            )


def check_hash_format(value: Any, field_name: str, allow_prefix: bool = False) -> None:
    """
    Validate SHA-256 hash format.

    Args:
        value: The hash value to check
        field_name: Name of field (for error messages)
        allow_prefix: If True, allow "sha256:" prefix. If False, expect bare hex.

    Raises:
        ValidationError if format is invalid
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"{field_name} must be string, got {type(value).__name__}"
        )

    if allow_prefix:
        if value.startswith("sha256:"):
            hex_part = value[7:]
        else:
            hex_part = value
    else:
        hex_part = value

    if len(hex_part) != 64:
        raise ValidationError(
            f"{field_name} must be 64 hex chars (or sha256:64hex), "
            f"got {len(hex_part)} chars: {value}"
        )

    try:
        int(hex_part, 16)
    except ValueError:
        raise ValidationError(
            f"{field_name} must be valid hex, got: {value}"
        )


def check_schema_version(artifact: Dict[str, Any], expected: str) -> None:
    """
    Verify artifact has correct schema identity.

    Supports both conventions:
    - Constitutional (current): schema_name="FAILURE_REPORT_V1" + schema_version="1.0.0"
    - Legacy: schema_version="FAILURE_REPORT_V1" (name-as-version)

    GOVERNANCE_DECISION_V1 SCHEMA-AUTHORITY-2026-04-16: constitutional is canonical.
    Legacy check retained for backward compatibility during transition.
    """
    # Constitutional check (preferred): schema_name field
    schema_name = artifact.get("schema_name")
    if schema_name is not None:
        if schema_name != expected:
            raise ValidationError(
                f"Schema name mismatch: expected {expected}, got {schema_name}"
            )
        return  # Constitutional shape — schema_version is "1.0.0", not the name
    # Legacy fallback: schema_version carries the name
    actual = artifact.get("schema_version")
    if actual != expected:
        raise ValidationError(
            f"Schema version mismatch: expected {expected}, got {actual}"
        )


def check_canonicalization_label(artifact: Dict[str, Any]) -> None:
    """
    Verify canonicalization field is JCS_SHA256_V1.

    Constitutional schemas do not require this field (it's implicit).
    Only enforced when the field is present.
    """
    label = artifact.get("canonicalization")
    if label is None:
        return  # Constitutional schema — canonicalization is implicit
    if label != "JCS_SHA256_V1":
        raise ValidationError(
            f"Invalid canonicalization: expected JCS_SHA256_V1, got {label}. "
            f"All HELEN artifacts must use RFC 8785 JSON canonical form."
        )


def check_handoff_phase(artifact: Dict[str, Any], valid_phases: List[str]) -> None:
    """
    Verify handoff_phase is one of allowed values.

    Ensures different types of handoffs are properly routed.
    """
    phase = artifact.get("handoff_phase")
    if phase not in valid_phases:
        raise ValidationError(
            f"Invalid handoff_phase: {phase}. "
            f"Must be one of: {', '.join(valid_phases)}"
        )


def validate_execution_envelope(envelope: Dict[str, Any]) -> None:
    """
    Validate EXECUTION_ENVELOPE_V1.

    Checks:
    - Schema version
    - Canonicalization label
    - Hash formats
    - No forbidden fields
    """
    check_schema_version(envelope, "EXECUTION_ENVELOPE_V1")
    check_canonicalization_label(envelope)

    hash_fields = [
        "environment_manifest_hash",
        "tool_trace_hash",
        "stdout_hash",
        "stderr_hash",
    ]
    for field in hash_fields:
        if field in envelope:
            check_hash_format(envelope[field], field, allow_prefix=True)

    # No verdicts or authority in envelope
    forbidden = {"SHIP", "NO_SHIP", "verdict", "decision", "approved"}
    check_no_forbidden_fields(envelope, forbidden)


def validate_failure_report(report: Dict[str, Any]) -> None:
    """
    Validate FAILURE_REPORT_V1.

    Checks:
    - Schema version
    - Canonicalization label
    - Hash formats
    - No verdicts (failures are observable, not adjudicated)
    """
    check_schema_version(report, "FAILURE_REPORT_V1")
    check_canonicalization_label(report)

    hash_fields = [
        "tool_trace_hash",
        "stdout_hash",
        "stderr_hash",
        "environment_manifest_hash",
    ]
    for field in hash_fields:
        if field in report:
            check_hash_format(report[field], field, allow_prefix=True)

    # No verdicts in failure report (it's an observable fact, not a judgment)
    forbidden = {"SHIP", "NO_SHIP", "verdict", "decision", "approved"}
    check_no_forbidden_fields(report, forbidden)


def validate_skill_promotion_packet(packet: Dict[str, Any]) -> None:
    """
    Validate SKILL_PROMOTION_PACKET_V1.

    Checks:
    - Schema version
    - Canonicalization
    - Hash formats
    - No verdicts (packet is proposal, not decision)
    """
    check_schema_version(packet, "SKILL_PROMOTION_PACKET_V1")
    check_canonicalization_label(packet)

    hash_fields = [
        "skill_folder_hash",
        "skill_diff_hash",
        "capability_manifest_hash",
    ]
    for field in hash_fields:
        if field in packet:
            check_hash_format(packet[field], field, allow_prefix=True)

    # Rollback target must have hash
    if "rollback_target" in packet:
        target = packet["rollback_target"]
        if "manifest_hash" in target:
            check_hash_format(target["manifest_hash"], "rollback_target.manifest_hash", allow_prefix=True)

    # No verdicts in packet (only proposal, not decision)
    forbidden = {"SHIP", "NO_SHIP", "verdict", "decision", "admitted", "promoted"}
    check_no_forbidden_fields(packet, forbidden)


def validate_skill_promotion_decision(decision: Dict[str, Any]) -> None:
    """
    Validate SKILL_PROMOTION_DECISION_V1.

    Checks:
    - Schema version
    - Canonicalization
    - Decision is one of allowed values
    - Ledger pointer has hash
    """
    check_schema_version(decision, "SKILL_PROMOTION_DECISION_V1")
    check_canonicalization_label(decision)

    # Decision must be binary
    valid_decisions = ["ADMITTED", "QUARANTINED", "REJECTED", "ROLLED_BACK"]
    actual = decision.get("decision")
    if actual not in valid_decisions:
        raise ValidationError(
            f"Invalid decision: {actual}. Must be one of: {', '.join(valid_decisions)}"
        )

    # Ledger pointer hash must be valid
    if "ledger_pointer" in decision:
        pointer = decision["ledger_pointer"]
        if "entry_hash" in pointer:
            check_hash_format(pointer["entry_hash"], "ledger_pointer.entry_hash", allow_prefix=True)


def validate_helen_handoff(handoff: Dict[str, Any]) -> None:
    """
    Validate HELEN_HANDOFF_V1.

    Checks:
    - Schema version
    - Canonicalization
    - Non-sovereign attestation (all false)
    - Hash formats
    - Handoff phase is valid
    - No forbidden fields
    """
    check_schema_version(handoff, "HELEN_HANDOFF_V1")
    check_canonicalization_label(handoff)
    check_non_sovereign_attestation(handoff)

    valid_phases = [
        "PRODUCTION_RESULT",
        "FAILURE_RESULT",
        "SKILL_PROPOSAL",
        "SKILL_EVAL",
    ]
    check_handoff_phase(handoff, valid_phases)

    hash_fields = [
        "source_manifest_hash",
        "payload_sha256",
        "law_surface_hash",
    ]
    for field in hash_fields:
        if field in handoff:
            check_hash_format(handoff[field], field, allow_prefix=False)

    # Forbidden: any production layer must not claim sovereignty
    forbidden = {"SHIP", "NO_SHIP", "verdict", "decision", "truth", "authority"}
    check_no_forbidden_fields(handoff, forbidden)


# Validator registry
VALIDATORS = {
    "EXECUTION_ENVELOPE_V1": validate_execution_envelope,
    "FAILURE_REPORT_V1": validate_failure_report,
    "SKILL_PROMOTION_PACKET_V1": validate_skill_promotion_packet,
    "SKILL_PROMOTION_DECISION_V1": validate_skill_promotion_decision,
    "HELEN_HANDOFF_V1": validate_helen_handoff,
}


def validate_strict(artifact: Dict[str, Any], schema_name: str) -> None:
    """
    Run strict constitutional validators.

    This goes beyond JSON Schema: enforces non-sovereignty, hash formats, etc.

    Raises ValidationError if any check fails.
    """
    if schema_name not in VALIDATORS:
        # No strict validator defined, but that's OK
        return

    validator = VALIDATORS[schema_name]
    validator(artifact)


__all__ = [
    "ValidationError",
    "validate_strict",
    "check_non_sovereign_attestation",
    "check_hash_format",
    "check_no_forbidden_fields",
]
