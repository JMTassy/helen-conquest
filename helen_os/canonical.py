"""
canonical.py - JCS canonicalization and SHA-256 hashing.

All hashing in HELEN must be deterministic and identical across implementations.
This module enforces RFC 8785 (JSON Canonical Serialization) and SHA-256.

Core law: same object → same bytes → same hash
"""

import hashlib
import json
from typing import Any, Union


def canonical_json_bytes(obj: Any) -> bytes:
    """
    Serialize object to canonical JSON (RFC 8785 JCS).

    Properties:
    - Deterministic: same object → same bytes always
    - Order-independent: key order does not affect output
    - Minimal: no extra whitespace

    Returns bytes, not string, to avoid encoding ambiguity.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    """
    Compute SHA-256 hash of bytes.

    Returns hex string (lowercase, 64 chars).
    """
    return hashlib.sha256(data).hexdigest()


def sha256_prefixed(data_or_obj: Union[bytes, Any]) -> str:
    """
    Compute SHA-256 with "sha256:" prefix.

    If passed bytes, hash directly.
    If passed object, canonicalize first, then hash.

    Returns format: "sha256:abcd1234..."
    """
    if isinstance(data_or_obj, bytes):
        digest = sha256_bytes(data_or_obj)
    else:
        digest = sha256_bytes(canonical_json_bytes(data_or_obj))
    return f"sha256:{digest}"


def canonical_json_string(obj: Any) -> str:
    """
    Serialize object to canonical JSON string (for debugging/logging).

    Identical to canonical_json_bytes but returns str instead of bytes.
    """
    return canonical_json_bytes(obj).decode("utf-8")


# Export public API
__all__ = [
    "canonical_json_bytes",
    "canonical_json_string",
    "sha256_bytes",
    "sha256_prefixed",
]
