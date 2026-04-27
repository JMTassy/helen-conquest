"""Canonical JSON encoding and SHA-256 hashing for the event chain."""
from __future__ import annotations

import hashlib
import json
from typing import Any

GENESIS_HASH = "0" * 64


class ChainBreak(Exception):
    """Raised when the hash chain is invalid (mismatched prev or recomputed hash)."""


def canonical_json(obj: Any) -> bytes:
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_event_hash(event: dict) -> str:
    """sha256(canonical_json(event without event_hash))."""
    body = {k: v for k, v in event.items() if k != "event_hash"}
    return sha256_hex(canonical_json(body))


def verify_chain(events: list[dict]) -> None:
    prev = GENESIS_HASH
    for i, e in enumerate(events):
        if e.get("prev_event_hash") != prev:
            raise ChainBreak(
                f"chain break at index {i}: expected prev={prev[:8]}, got {e.get('prev_event_hash','?')[:8]}"
            )
        recomputed = compute_event_hash(e)
        if recomputed != e.get("event_hash"):
            raise ChainBreak(
                f"event_hash mismatch at index {i}: stored={e.get('event_hash','?')[:8]}, computed={recomputed[:8]}"
            )
        prev = e["event_hash"]
