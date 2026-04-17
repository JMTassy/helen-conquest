#!/usr/bin/env python3
# Canonical JSON + SHA256 helpers (kernel core v0.1)

import json
import hashlib
from typing import Any


def _no_floats(obj: Any) -> None:
    if isinstance(obj, float):
        raise ValueError("floats are forbidden in payload")
    if isinstance(obj, dict):
        for v in obj.values():
            _no_floats(v)
    elif isinstance(obj, list):
        for v in obj:
            _no_floats(v)


def canon(obj: Any) -> str:
    _no_floats(obj)
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_hex_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()
