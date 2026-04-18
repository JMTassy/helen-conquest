from __future__ import annotations
import hashlib
import json
from typing import Any

def canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def stable_id(prefix: str, payload: dict[str, Any]) -> str:
    return f"{prefix}-{sha256_hex(canon(payload))[:12]}"
