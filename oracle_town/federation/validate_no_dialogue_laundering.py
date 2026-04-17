"""
oracle_town/federation/validate_no_dialogue_laundering.py

Dialogue Laundering Guard — D→E→L Separation Enforcement

Constitutional rule (from LAW_HELEN_BOUNDED_EMERGENCE_V1 + Key Concepts):
  "No SHIP mutation may cite dialog.ndjson directly.
   SHIP mutations may cite only: CLAIM_GRAPH_V1 artifact hashes,
   evaluation receipts, gate receipts, law inscription receipts."

This guard is called before any mutation payload is handed to GovernanceVM.propose().

Usage:
    from oracle_town.federation.validate_no_dialogue_laundering import (
        assert_no_dialogue_laundering,
        DialogueLaunderingError,
    )

    # In your mutation path, before kernel.propose():
    assert_no_dialogue_laundering(mutation_payload)
    kernel.propose(mutation_payload)

Violation codes:
    DL-001: Mutation payload contains a direct dialog.ndjson reference.
    DL-002: Mutation payload refs array contains a DIALOG_TURN_V1 type.
    DL-003: Mutation payload refs array contains a DIALOG_LOG type.
    DL-004: Mutation payload evidence field references dialog.ndjson path directly.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List


# ── Exception ─────────────────────────────────────────────────────────────────

class DialogueLaunderingError(Exception):
    """
    Raised when a mutation payload attempts to cite dialog.ndjson directly.

    This prevents "dialogue laundering" — the most common safety leak in
    architectures where dialogue and sovereign ledger share the same storage layer.
    """
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(f"[{code}] DIALOGUE_LAUNDERING_FORBIDDEN: {detail}")


# ── Banned ref types and path patterns ────────────────────────────────────────

BANNED_REF_TYPES: List[str] = [
    "DIALOG_TURN_V1",
    "DIALOG_LOG",
    "DIALOG_NDJSON",
    "DIALOGUE_TURN",
    "DIALOGUE_LOG",
]

BANNED_PATH_PATTERNS: List[str] = [
    # File-path / artifact tokens only — no module-name substrings.
    # "dialog_runner" intentionally excluded: false-positives on stack traces,
    # documentation, module imports. Restrict to ndjson paths and directory prefixes.
    "dialog.ndjson",
    "dialogue.ndjson",
    "helen_dialog/dialog",
]

# Allowed ref types (whitelist)
ALLOWED_REF_TYPES: List[str] = [
    "CLAIM_GRAPH_V1",
    "EVALUATION_RECEIPT",
    "GATE_RECEIPT",
    "LAW_INSCRIPTION_RECEIPT",
    "AUTHZ_RECEIPT_V1",
    "CROSS_RECEIPT_V1",
    "HAL_VERDICT_RECEIPT_V1",
    "BLOCK_RECEIPT_V1",
    "POLICY_UPDATE_RECEIPT_V1",
]


# ── Guard function ─────────────────────────────────────────────────────────────

def assert_no_dialogue_laundering(mutation_payload: Dict[str, Any]) -> None:
    """
    Assert that the mutation payload contains no direct dialog.ndjson references.

    Checks:
    1. Any string value in the payload containing a banned path pattern.
    2. Any `refs` array entry with a banned ref type.
    3. Any `evidence` field containing a banned path pattern.

    Raises:
        DialogueLaunderingError: if any banned reference is found.

    Args:
        mutation_payload: the dict to be handed to GovernanceVM.propose()
    """
    # Check order: typed checks FIRST (DL-002, DL-004), then general string scan (DL-001).
    # This ensures tests can assert specific error codes for semantic violations.

    # Check 2: scan refs array — banned type (DL-002) then unknown type (DL-005).
    # Fail-closed: any ref.type not in ALLOWED_REF_TYPES is rejected (DL-005).
    # This prevents new undeclared ref types becoming an ungoverned backdoor.
    refs = mutation_payload.get("refs", [])
    if isinstance(refs, list):
        for ref in refs:
            if isinstance(ref, dict):
                ref_type = ref.get("type", "")
                if ref_type in BANNED_REF_TYPES:
                    raise DialogueLaunderingError(
                        "DL-002",
                        f"refs array contains banned type '{ref_type}'. "
                        f"Only allowed: {ALLOWED_REF_TYPES}. "
                        "Lift dialogue through CLAIM_GRAPH_V1 pipeline first."
                    )
                if ref_type and ref_type not in ALLOWED_REF_TYPES:
                    raise DialogueLaunderingError(
                        "DL-005",
                        f"refs array contains unknown type '{ref_type}' not in allowlist. "
                        f"Allowlist: {ALLOWED_REF_TYPES}. "
                        "Schema is constitution: ungoverned ref types are rejected (fail-closed). "
                        "Add the new type to ALLOWED_REF_TYPES to permit it."
                    )

    # Check 3: evidence field path patterns (semantic check — DL-004)
    evidence = mutation_payload.get("evidence", "")
    if isinstance(evidence, str):
        for pattern in BANNED_PATH_PATTERNS:
            if pattern in evidence:
                raise DialogueLaunderingError(
                    "DL-004",
                    f"evidence field contains banned pattern '{pattern}'. "
                    "Evidence must reference receipt hashes, not dialogue paths."
                )
    elif isinstance(evidence, dict):
        _scan_string_values(evidence, prefix="evidence.")

    # Check 1: general string scan for path patterns in ALL OTHER fields (DL-001)
    # Skip 'refs' and 'evidence' keys — those have dedicated checks above.
    filtered = {k: v for k, v in mutation_payload.items() if k not in ("refs", "evidence")}
    _scan_string_values(filtered)


def _scan_string_values(
    obj: Any,
    prefix: str = "",
    _depth: int = 0,
) -> None:
    """Recursively scan string values for banned path patterns."""
    if _depth > 10:
        return  # Prevent infinite recursion on deeply nested payloads
    if isinstance(obj, dict):
        for key, val in obj.items():
            _scan_string_values(val, prefix=f"{prefix}{key}.", _depth=_depth + 1)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _scan_string_values(item, prefix=f"{prefix}[{i}].", _depth=_depth + 1)
    elif isinstance(obj, str):
        for pattern in BANNED_PATH_PATTERNS:
            if pattern in obj:
                raise DialogueLaunderingError(
                    "DL-001",
                    f"Field '{prefix.rstrip('.')}' contains banned path pattern '{pattern}'. "
                    "dialog.ndjson must not be cited directly in mutation payloads. "
                    "Lift dialogue through CLAIM_GRAPH_V1 pipeline first."
                )


# ── Convenience: validate a JSON string ───────────────────────────────────────

def validate_mutation_json(payload_json: str) -> None:
    """
    Validate a JSON-encoded mutation payload string.

    Raises:
        DialogueLaunderingError: if payload contains banned dialogue references.
        json.JSONDecodeError: if payload is not valid JSON.
    """
    payload = json.loads(payload_json)
    assert_no_dialogue_laundering(payload)
