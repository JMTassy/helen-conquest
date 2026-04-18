"""
helen_os/kernel/canonical_json.py

Deterministic canonical JSON serialization for CWL.

Guarantees: Same dict → same bytes (independent of Python internals, dict ordering, etc.)

Used for:
  - Payload hashing
  - Merkle leaf hashing
  - Receipt canonicalization
"""

import json


def canon(obj) -> str:
    """
    Deterministic canonical JSON representation of object.

    Args:
        obj: Python object (dict, list, str, int, etc.)

    Returns:
        Canonical JSON string (sorted keys, compact separators, UTF-8)

    Example:
        >>> obj = {"z": 1, "a": 2}
        >>> canon(obj)
        '{"a":2,"z":1}'
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,  # Fallback for non-JSON-serializable objects
    )
