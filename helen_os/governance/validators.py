"""Schema validation and hash verification."""
from __future__ import annotations

import jsonschema
from typing import Any, Mapping

from .canonical import canonical_json_bytes, sha256_prefixed, sha256_hex_from_bytes
from .schema_registry import SCHEMA_STORE


def validate_schema(
    name: str, version: str, obj: Mapping[str, Any]
) -> tuple[bool, str | None]:
    """
    Validate an object against a schema.

    Args:
        name: Schema name (e.g., "EXECUTION_ENVELOPE_V1")
        version: Schema version (e.g., "1.0.0")
        obj: Object to validate

    Returns:
        (is_valid, error_message)
    """
    key = f"{name}/{version}"
    if key not in SCHEMA_STORE:
        return False, f"unknown schema: {key}"
    try:
        jsonschema.validate(instance=obj, schema=SCHEMA_STORE[key])
        return True, None
    except jsonschema.ValidationError as e:
        return False, str(e)


def verify_hash(
    obj: Mapping[str, Any], expected: str, *, exclude: set[str] | None = None
) -> bool:
    """
    Verify that an object's canonical hash matches expected value.

    Args:
        obj: Object to hash
        expected: Expected hash (e.g., "sha256:abcd...")
        exclude: Fields to exclude from hash (e.g., {"sha256"})

    Returns:
        True if hash matches, False otherwise
    """
    exclude = exclude or set()
    stripped = {k: v for k, v in obj.items() if k not in exclude}
    computed = sha256_prefixed(stripped)
    return computed == expected
