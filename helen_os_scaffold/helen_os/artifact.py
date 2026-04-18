"""
helen_artifact.py — Phase 1 Artifact Law Implementation

Minimal phase: canonicalization, hashing, schema validation, invariant enforcement.

Frozen rules:
1. Canonicalization: JSON with sorted keys, no whitespace, UTF-8
2. Hashing: SHA-256 of canonical bytes only
3. Schema validation: frozen JSON Schema files only
4. Invariants: non-sovereignty checks beyond schema

No agent orchestration, no signatures, no database, no HTTP, no UI.
Only admissibility boundary enforcement.
"""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import jsonschema
    from jsonschema import ValidationError as JsonSchemaValidationError
except ImportError as exc:
    raise RuntimeError(
        "jsonschema is required for helen_artifact.py Phase 1"
    ) from exc


# ============================================================================
# Constants (Frozen)
# ============================================================================

CANONICALIZATION_LABEL = "JCS_SHA256_V1"
SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "schemas"

SCHEMA_FILES: Dict[str, str] = {
    "builders_brief_v1": "builders_brief_v1.schema.json",
    "builders_claim_v1": "builders_claim_v1.schema.json",
    "builders_run_v1": "builders_run_v1.schema.json",
    "helen_handoff_v1": "helen_handoff_v1.schema.json",
    "mission_v1": "mission_v1.schema.json",
    "proposal_v1": "proposal_v1.schema.json",
    "execution_receipt_v1": "execution_receipt_v1.schema.json",
    "evidence_bundle_v1": "evidence_bundle_v1.schema.json",
    "issue_list_v1": "issue_list_v1.schema.json",
    "run_manifest_v1": "run_manifest_v1.schema.json",
    "verdict_v1": "verdict_v1.schema.json",
}


# ============================================================================
# Exceptions (Constitutional)
# ============================================================================


class ArtifactValidationError(Exception):
    """Base class for all artifact-law failures."""


class SchemaValidationError(ArtifactValidationError):
    """Raised when a payload fails JSON Schema validation."""


class InvariantViolation(ArtifactValidationError):
    """Raised when a payload violates constitutional invariants."""


# ============================================================================
# Core Functions (Deterministic)
# ============================================================================


def canonical_json_bytes(obj: Dict[str, Any]) -> bytes:
    """
    Canonical JSON encoding for artifact hashing.

    Frozen rule:
    - UTF-8 encoding
    - sorted keys (alphabetical)
    - separators=(',', ':') — no spaces
    - ensure_ascii=False — allow Unicode
    - no pretty-printing

    This must produce identical bytes for identical semantic objects.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_hex(data: bytes | str) -> str:
    """
    Return SHA-256 hex digest of bytes or UTF-8 string.

    Frozen rule: always hex output, never raw bytes.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


@lru_cache(maxsize=None)
def load_schema(name: str) -> Dict[str, Any]:
    """
    Load one frozen schema by explicit artifact name.

    Schema lookup is explicit-file-only. No discovery. No magic resolution.
    Raises ArtifactValidationError if schema not found or invalid JSON.
    """
    if name not in SCHEMA_FILES:
        raise ArtifactValidationError(
            f"Unknown schema name: {name}. Known schemas: {list(SCHEMA_FILES.keys())}"
        )

    filename = SCHEMA_FILES[name]
    path = SCHEMA_DIR / filename

    if not path.exists():
        raise ArtifactValidationError(
            f"Schema file not found: {path} (expected in {SCHEMA_DIR})"
        )

    try:
        schema_text = path.read_text(encoding="utf-8")
        return json.loads(schema_text)
    except json.JSONDecodeError as exc:
        raise ArtifactValidationError(
            f"Invalid JSON in schema {path}: {exc}"
        ) from exc


def validate_schema(name: str, payload: Dict[str, Any]) -> None:
    """
    Validate payload against frozen JSON Schema.

    Raises SchemaValidationError if validation fails.
    """
    schema = load_schema(name)
    try:
        jsonschema.validate(instance=payload, schema=schema)
    except JsonSchemaValidationError as exc:
        raise SchemaValidationError(
            f"Schema validation failed for {name}: {exc.message}"
        ) from exc


# ============================================================================
# Invariant Enforcement (Constitutional)
# ============================================================================


def _require_frozen_canonicalization_if_present(
    payload: Dict[str, Any],
) -> None:
    """
    If payload declares canonicalization, it MUST be exactly the frozen label.

    This prevents silent canonicalization drift.
    """
    if "canonicalization" in payload:
        value = payload["canonicalization"]
        if value != CANONICALIZATION_LABEL:
            raise InvariantViolation(
                f"canonicalization must equal {CANONICALIZATION_LABEL!r}, "
                f"got {value!r}"
            )


def _enforce_non_sovereignty(name: str, payload: Dict[str, Any]) -> None:
    """
    Constitutional boundary checks: BUILDERS artifacts must not emit sovereign state.

    Phase 1 non-sovereignty laws:
    1. verdict_emitted must not be True
    2. truth_claimed must not be True
    3. doctrine_mutated must not be True

    These are checked for all BUILDERS-prefixed schemas.
    """
    if name.startswith("builders_"):
        # Law 1: No verdicts
        if payload.get("verdict_emitted") is True:
            raise InvariantViolation(
                f"{name} violates non-sovereignty invariant: "
                f"verdict_emitted=True is forbidden"
            )

        # Law 2: No truth claims
        if payload.get("truth_claimed") is True:
            raise InvariantViolation(
                f"{name} violates non-sovereignty invariant: "
                f"truth_claimed=True is forbidden"
            )

        # Law 3: No doctrine mutation
        if payload.get("doctrine_mutated") is True:
            raise InvariantViolation(
                f"{name} violates non-sovereignty invariant: "
                f"doctrine_mutated=True is forbidden"
            )


def enforce_invariants(name: str, payload: Dict[str, Any]) -> None:
    """
    Enforce constitutional rules not expressible in JSON Schema alone.

    Current Phase 1 laws:
    1. Canonicalization label must be frozen if present
    2. BUILDERS artifacts must satisfy non-sovereignty checks

    Raises InvariantViolation if any invariant is broken.
    """
    _require_frozen_canonicalization_if_present(payload)
    _enforce_non_sovereignty(name, payload)


# ============================================================================
# Public API
# ============================================================================


def validate_artifact(
    name: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Full Phase 1 artifact-law check: schema + invariants + hash.

    Returns a minimal receipt-like validation result if valid.
    Raises SchemaValidationError or InvariantViolation if validation fails.

    Args:
        name: Artifact schema name (e.g., 'builders_brief', 'verdict_v1')
        payload: The artifact payload dict to validate

    Returns:
        Dict with:
        - artifact_type: the schema name
        - canonicalization: frozen label
        - payload_hash: hex SHA-256 of canonical bytes
        - validated: True

    Example:
        >>> result = validate_artifact('verdict_v1', {
        ...     'schema': 'VERDICT_V1',
        ...     'verdict_id': 'V-001',
        ...     'subject_ref': 'PROP-001',
        ...     'decision': 'SHIP',
        ...     'missing_obligations': [],
        ...     'reason_codes': [],
        ...     'canonicalization': 'JCS_SHA256_V1'
        ... })
        >>> result['payload_hash']
        'abc123...'
    """
    # Step 1: Schema validation
    validate_schema(name, payload)

    # Step 2: Invariant enforcement
    enforce_invariants(name, payload)

    # Step 3: Compute canonical hash
    canonical_bytes = canonical_json_bytes(payload)
    payload_hash = sha256_hex(canonical_bytes)

    # Step 4: Return receipt-like object
    return {
        "artifact_type": name,
        "canonicalization": CANONICALIZATION_LABEL,
        "payload_hash": payload_hash,
        "validated": True,
    }
