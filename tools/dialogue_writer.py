#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialogue Writer: Clean implementation of Payload/Meta split (40 lines)

Implements PAYLOAD_META_WRITER_SPEC exactly.
Every append() call:
  1. Computes payload_hash = SHA256(Canon(payload))
  2. Computes cum_hash = SHA256(bytes(prev_cum_hash) || bytes(payload_hash))
  3. Writes one NDJSON line with all fields
  4. Updates state for next call

Determinism proof: Same payload → Same cum_hash across runs.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional


class DialogueWriter:
    """NDJSON writer with payload/meta split and cumulative hashing."""

    def __init__(self, path: str = "./town/dialogue.ndjson"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.seq = 0
        self.prev_cum_hash = "0" * 64  # genesis

        # Load existing file to resume
        if self.path.exists():
            lines = [l for l in self.path.read_text().strip().split("\n") if l.strip()]
            if lines:
                last = json.loads(lines[-1])
                self.seq = last.get("seq", 0) + 1
                self.prev_cum_hash = last.get("cum_hash", self.prev_cum_hash)

    @staticmethod
    def canon(obj: Dict[str, Any]) -> str:
        """Canonical JSON: sorted keys, compact output."""
        return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)

    def append(
        self,
        type_: str,
        payload: Dict[str, Any],
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Append event to dialogue log.

        Args:
            type_: "turn", "milestone", "seal"
            payload: Hash-bound deterministic fields
            meta: Observational fields (timestamp, notes, etc.)

        Returns:
            Full event dict (for testing/verification)
        """
        # Compute payload_hash from canonical payload
        payload_hash = hashlib.sha256(
            self.canon(payload).encode("utf-8")
        ).hexdigest()

        # Compute cum_hash: SHA256(hex_decode(prev) || hex_decode(payload))
        prev_bytes = bytes.fromhex(self.prev_cum_hash)
        payload_bytes = bytes.fromhex(payload_hash)
        cum_hash = hashlib.sha256(prev_bytes + payload_bytes).hexdigest()

        # Build event
        event = {
            "type": type_,
            "seq": self.seq,
            "payload": payload,
            "meta": meta or {},
            "payload_hash": payload_hash,
            "prev_cum_hash": self.prev_cum_hash,
            "cum_hash": cum_hash,
        }

        # Write to NDJSON file
        with self.path.open("a", encoding="utf-8") as f:
            f.write(self.canon(event) + "\n")

        # Update state for next call
        self.seq += 1
        self.prev_cum_hash = cum_hash

        return event


# Convenience functions
def create_turn_payload(
    turn: int,
    hal: Dict[str, Any],
    channel_contract: str = "HER_HAL_V1",
) -> Dict[str, Any]:
    """Create a turn event payload."""
    return {
        "turn": turn,
        "channel_contract": channel_contract,
        "hal": hal,
    }


def create_hal_verdict(
    verdict: str,
    reasons_codes: list,
    required_fixes: list,
    refs: Dict[str, str],
    certificates: list = None,
    mutations: list = None,
) -> Dict[str, Any]:
    """Create a HAL_VERDICT_V1 object."""
    return {
        "certificate": certificates or [],
        "mutations": mutations or [],
        "reasons_codes": sorted(reasons_codes),  # Always sort
        "required_fixes": sorted(required_fixes),  # Always sort
        "refs": refs,
        "verdict": verdict,
    }
