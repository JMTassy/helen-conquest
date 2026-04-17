"""
Append-Only, Hash-Linked Ledger

This is the Mayor's only authoritative historical record. The ledger is:
- Append-only (no updates or deletes)
- Hash-linked (each entry references prev_hash)
- Deterministic (canonical JSON serialization)
- Tamper-detecting (verify_chain() fails on any modification)

Mayor reads ledger entries by reference only (seq + sha256).
UI never writes to the ledger; only Factory/CI runners append.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def canonical_json_bytes(obj: Any) -> bytes:
    """
    Deterministic JSON serialization for hashing.
    - Sorted keys
    - No whitespace variance
    - UTF-8 encoding
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    """SHA-256 hash as lowercase hex string"""
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class LedgerEntry:
    """
    Single ledger entry (immutable).

    Fields:
        seq: Monotonic sequence number (1-indexed)
        created_at: ISO 8601 timestamp (UTC)
        entry_type: Type discriminator (e.g., "RECEIPT_BUNDLE_REF", "DECISION_REF")
        payload: Type-specific data (must be JSON-serializable)
        prev_hash: SHA-256 of previous entry's canonical bytes (or "0"*64 for genesis)
        canonical_sha256: SHA-256 of this entry's canonical bytes (excluding this field)
    """
    seq: int
    created_at: str
    entry_type: str
    payload: dict[str, Any]
    prev_hash: str
    canonical_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "seq": self.seq,
            "created_at": self.created_at,
            "entry_type": self.entry_type,
            "payload": self.payload,
            "prev_hash": self.prev_hash,
            "canonical_sha256": self.canonical_sha256,
        }


class AppendOnlyLedger:
    """
    File-backed JSONL ledger with hash chaining.

    Properties:
    - Append-only by contract (enforced via file permissions + CI)
    - Each line is a JSON object (LedgerEntry)
    - Genesis entry has prev_hash = "0" * 64
    - Sequence numbers are strictly increasing (1, 2, 3, ...)
    - verify_chain() detects any tampering

    Usage:
        ledger = AppendOnlyLedger(Path("artifacts/ledger.jsonl"))
        entry = ledger.append("RECEIPT_BUNDLE_REF", {
            "bundle_id": "RCPT-ABC123",
            "sha256": "a1b2c3...",
            "run_id": "RUN-001"
        })
        ledger.verify_chain()  # Fails if any line was modified
    """

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def _read_lines(self) -> list[str]:
        """Read non-empty lines from ledger file"""
        return [
            line
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def _last_entry(self) -> Optional[dict[str, Any]]:
        """Get last entry as dict, or None if ledger is empty"""
        lines = self._read_lines()
        if not lines:
            return None
        return json.loads(lines[-1])

    def append(self, entry_type: str, payload: dict[str, Any]) -> LedgerEntry:
        """
        Append new entry to ledger.

        Args:
            entry_type: Entry type discriminator (e.g., "RECEIPT_BUNDLE_REF")
            payload: Entry-specific data (must be JSON-serializable)

        Returns:
            Immutable LedgerEntry with computed hash

        Note:
            This method is NOT thread-safe. For concurrent access,
            use file locking or single-threaded execution (AI Town pattern).
        """
        last = self._last_entry()
        prev_hash = last["canonical_sha256"] if last else ("0" * 64)
        seq = (last["seq"] + 1) if last else 1

        created_at = datetime.now(timezone.utc).isoformat()

        # Hash base (excludes canonical_sha256 itself)
        base = {
            "seq": seq,
            "created_at": created_at,
            "entry_type": entry_type,
            "payload": payload,
            "prev_hash": prev_hash,
        }

        canonical_sha256 = sha256_hex(canonical_json_bytes(base))

        entry = LedgerEntry(
            seq=seq,
            created_at=created_at,
            entry_type=entry_type,
            payload=payload,
            prev_hash=prev_hash,
            canonical_sha256=canonical_sha256,
        )

        # Append to file (atomic write on most filesystems)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

        return entry

    def verify_chain(self) -> None:
        """
        Verify ledger integrity.

        Checks:
        - Sequence numbers are strictly increasing (1, 2, 3, ...)
        - Each prev_hash matches previous entry's canonical_sha256
        - Each canonical_sha256 matches recomputed hash

        Raises:
            AssertionError: If any check fails (ledger is tampered)

        Usage:
            Run this in CI after every ledger operation:
            ledger.verify_chain()

            If this passes, the ledger is cryptographically tamper-proof.
        """
        lines = self._read_lines()
        prev_hash = "0" * 64

        for i, line in enumerate(lines, start=1):
            entry = json.loads(line)

            # Check sequence
            assert entry["seq"] == i, (
                f"Ledger integrity violation at line {i}:\n"
                f"Expected seq={i}, got seq={entry['seq']}\n"
                f"Ledger may have been reordered or entries removed."
            )

            # Check prev_hash linkage
            assert entry["prev_hash"] == prev_hash, (
                f"Ledger integrity violation at seq {i}:\n"
                f"Expected prev_hash={prev_hash}, got {entry['prev_hash']}\n"
                f"Ledger chain is broken."
            )

            # Recompute hash and verify
            base = {
                "seq": entry["seq"],
                "created_at": entry["created_at"],
                "entry_type": entry["entry_type"],
                "payload": entry["payload"],
                "prev_hash": entry["prev_hash"],
            }
            computed_hash = sha256_hex(canonical_json_bytes(base))

            assert computed_hash == entry["canonical_sha256"], (
                f"Ledger integrity violation at seq {i}:\n"
                f"Expected canonical_sha256={computed_hash}\n"
                f"Got {entry['canonical_sha256']}\n"
                f"Entry content has been modified."
            )

            prev_hash = entry["canonical_sha256"]

    def get_entries_by_type(self, entry_type: str) -> list[LedgerEntry]:
        """
        Get all entries of a specific type (for Mayor queries).

        Args:
            entry_type: Entry type filter (e.g., "RECEIPT_BUNDLE_REF")

        Returns:
            List of matching LedgerEntry objects
        """
        lines = self._read_lines()
        entries = []
        for line in lines:
            entry_dict = json.loads(line)
            if entry_dict["entry_type"] == entry_type:
                entries.append(LedgerEntry(**entry_dict))
        return entries
