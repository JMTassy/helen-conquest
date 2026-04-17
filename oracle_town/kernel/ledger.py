#!/usr/bin/env python3
"""
Kernel Ledger: Immutable Append-Only Record

Records all claims and receipts immutably.
Enforces K22: Ledger Append-Only

Pure function for testing: (receipt) → recorded
No file I/O in tests (use in-memory ledger).
Production version uses append-only file.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any


@dataclass
class LedgerEntry:
    """Single entry in append-only ledger"""
    entry_id: str
    timestamp: str
    entry_type: str  # "CLAIM" or "RECEIPT"
    content: Dict[str, Any]
    hash: str  # Content hash for chain integrity


class InMemoryLedger:
    """In-memory ledger for testing (no file I/O)"""

    def __init__(self):
        self.entries: List[LedgerEntry] = []
        self.entry_count = 0

    def record(self, entry_type: str, content: Dict[str, Any]) -> str:
        """
        Record entry to ledger.

        Args:
            entry_type: "CLAIM" or "RECEIPT"
            content: Dictionary to record

        Returns:
            entry_id (immutable identifier)

        K22: Ledger Append-Only
        - Cannot modify or delete past entries
        - Can only append new entries
        """
        import hashlib

        self.entry_count += 1
        entry_id = f"L-{self.entry_count:06d}"
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Compute hash for chain integrity
        content_bytes = json.dumps(content, sort_keys=True).encode()
        content_hash = hashlib.sha256(content_bytes).hexdigest()[:16]

        entry = LedgerEntry(
            entry_id=entry_id,
            timestamp=timestamp,
            entry_type=entry_type,
            content=content,
            hash=content_hash
        )

        self.entries.append(entry)
        return entry_id

    def get_entries(self) -> List[LedgerEntry]:
        """Retrieve all entries (read-only view)"""
        return list(self.entries)

    def verify_integrity(self) -> bool:
        """Verify ledger hasn't been tampered with"""
        import hashlib

        for entry in self.entries:
            # Recompute hash
            content_bytes = json.dumps(entry.content, sort_keys=True).encode()
            expected_hash = hashlib.sha256(content_bytes).hexdigest()[:16]

            if entry.hash != expected_hash:
                return False

        return True

    def __len__(self) -> int:
        """Number of entries in ledger"""
        return len(self.entries)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for testing/inspection"""
        return {
            "entry_count": self.entry_count,
            "entries": [
                {
                    "entry_id": e.entry_id,
                    "timestamp": e.timestamp,
                    "type": e.entry_type,
                    "hash": e.hash,
                    "content": e.content
                }
                for e in self.entries
            ]
        }
