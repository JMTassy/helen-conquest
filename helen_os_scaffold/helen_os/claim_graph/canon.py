"""
helen_os/claim_graph/canon.py — Canonicalization helpers for CLAIM_GRAPH_V1.

Re-uses the kernel's canonical_json scheme (sort_keys + compact separators)
so that claim graph hashes are consistent with the GovernanceVM hash chain.

Functions:
  canonical_json(obj)  → str   — deterministic JSON string
  sha256_canon(obj)    → str   — SHA256(canonical_json(obj))
  sha256_text(text)    → str   — SHA256(raw text bytes) — for source_digest
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(obj: Any) -> str:
    """
    Produce a deterministic JSON string (sort_keys + compact separators).

    Handles Pydantic models (calls .model_dump()) and plain dicts/lists.
    Compatible with GovernanceVM._canonicalize() so hashes chain correctly.
    """
    if hasattr(obj, "model_dump"):
        obj = obj.model_dump()
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha256_canon(obj: Any) -> str:
    """SHA256 of canonical_json(obj). Used for artifact and graph hashing."""
    return hashlib.sha256(canonical_json(obj).encode()).hexdigest()


def sha256_text(text: str) -> str:
    """SHA256 of raw text (UTF-8 encoded). Used for source_digest."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
