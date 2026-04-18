"""HELEN Render — canonical serialization and hashing."""
from __future__ import annotations

import dataclasses
import hashlib
import json


def canonical_json(obj) -> str:
    """Deterministic JSON: sort_keys, no spaces."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_prefixed(s: str) -> str:
    return "sha256:" + sha256_hex(s)


def hash_dataclass(dc) -> str:
    """Canonical hash of any dataclass."""
    return sha256_hex(canonical_json(dataclasses.asdict(dc)))
