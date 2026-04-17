"""Canonicalization and hashing primitives for HELEN OS MVP.

Law:
- There is exactly one canonical JSON serialization surface.
- There is exactly one prefixed SHA-256 hash surface.
- All governance-critical hashes must flow through this module.
- No other module may invent an alternative hash format.

Canonicalization regime:
- UTF-8 JSON bytes
- sorted keys
- no insignificant whitespace
- stable handling of nested dict/list structures
- allow_nan = False

Hash format:
- "sha256:<64 lowercase hex chars>"
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Final


CANONICALIZATION_VERSION: Final[str] = "JCS_SHA256_V1"
HASH_PREFIX: Final[str] = "sha256:"


def canonical_json_bytes(obj: Any) -> bytes:
    """
    Return canonical UTF-8 JSON bytes for obj.

    Properties:
    - deterministic for equivalent Python JSON-compatible objects
    - sorted keys
    - no insignificant whitespace
    - UTF-8 encoded
    - rejects NaN / Infinity via allow_nan=False

    Raises:
    - TypeError
    - ValueError
    if the object cannot be serialized canonically.
    """
    text = json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return text.encode("utf-8")


def sha256_hex_from_bytes(data: bytes) -> str:
    """
    Return raw lowercase SHA-256 hex digest for bytes.
    No prefix added.
    """
    return hashlib.sha256(data).hexdigest()


def sha256_prefixed(obj_or_bytes: Any) -> str:
    """
    Return prefixed SHA-256 digest.

    Accepted inputs:
    - bytes
    - any JSON-serializable object

    Output format:
    - 'sha256:<64 lowercase hex chars>'
    """
    if isinstance(obj_or_bytes, bytes):
        digest = sha256_hex_from_bytes(obj_or_bytes)
    else:
        digest = sha256_hex_from_bytes(canonical_json_bytes(obj_or_bytes))
    return f"{HASH_PREFIX}{digest}"


def is_prefixed_sha256(value: str) -> bool:
    """
    Return True iff value matches the canonical prefixed SHA-256 format.
    """
    if not isinstance(value, str):
        return False
    if not value.startswith(HASH_PREFIX):
        return False
    hex_part = value[len(HASH_PREFIX):]
    if len(hex_part) != 64:
        return False
    return all(ch in "0123456789abcdef" for ch in hex_part)


def assert_prefixed_sha256(value: str) -> None:
    """
    Raise ValueError iff value is not a canonical prefixed SHA-256 hash.
    """
    if not is_prefixed_sha256(value):
        raise ValueError(f"Invalid prefixed SHA-256 value: {value!r}")
