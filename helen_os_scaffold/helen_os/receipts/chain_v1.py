"""
Receipt Chain v1 — Append-Only Integrity Chain
==============================================
Implements tamper-evident receipt chaining (AWS CloudTrail pattern).

Every receipt entry includes:
- prev_hash: SHA256 of previous entry (creates the chain)
- entry_hash: SHA256 of current entry (proof of this entry)
- context_hash: SHA256 of query+hits context (audit trail)

All writes are atomic (fcntl.flock + fsync) to guarantee durability.
Verification: check that chain is unbroken and hashes match expected values.

References:
  - AWS CloudTrail digest (append-only log with chaining)
  - RFC6962 (Merkle Tree commitment, transparency logs)
"""

import os
import json
import hashlib
import fcntl
from typing import Dict, Any, Optional
from pathlib import Path


def canonical_json(obj: Any) -> str:
    """
    Serialize object to canonical JSON (sorted keys, no whitespace).
    Ensures same object always produces same hash.
    """
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def sha256_hex(text: str) -> str:
    """Compute SHA256 hash of text, return as hex string."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


class ReceiptChain:
    """Manage append-only receipt chain with hash integrity."""

    def __init__(self, ledger_path: str = "receipts/memory_hits.jsonl"):
        """
        Initialize receipt chain.

        Args:
            ledger_path: Path to receipt ledger (NDJSON format, one JSON per line)
        """
        self.ledger_path = ledger_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.ledger_path) or ".", exist_ok=True)

    def _get_last_entry_hash(self) -> str:
        """Read the last entry from ledger and return its hash."""
        if not os.path.exists(self.ledger_path):
            return ""
        try:
            with open(self.ledger_path, 'r') as f:
                lines = f.readlines()
                if not lines:
                    return ""
                last_line = lines[-1].strip()
                if not last_line:
                    return ""
                last_entry = json.loads(last_line)
                return last_entry.get("entry_hash", "")
        except Exception as e:
            print(f"[WARN] Failed to read last entry: {e}")
            return ""

    def append(self, entry: Dict[str, Any], fail_on_error: bool = True) -> Optional[str]:
        """
        Append a receipt entry to the chain with atomic write.

        Process:
        1. Read last entry hash (prev_hash)
        2. Compute entry_hash for new entry
        3. Write atomically (fcntl.flock + fsync)

        Args:
            entry: Dictionary to append (will be enriched with hashes)
            fail_on_error: If True, raise Exception on write failure.
                          If False, log and return None.

        Returns:
            The entry_hash of the appended entry, or None on failure.

        Raises:
            RuntimeError: If fail_on_error=True and write fails.
        """
        try:
            prev_hash = self._get_last_entry_hash()

            # Build entry with context
            enriched_entry = dict(entry)
            enriched_entry["prev_hash"] = prev_hash

            # Compute entry_hash (hash of entry WITHOUT entry_hash field)
            tmp = dict(enriched_entry)
            tmp.pop("entry_hash", None)
            entry_hash = sha256_hex(canonical_json(tmp))
            enriched_entry["entry_hash"] = entry_hash

            # Atomic write
            with open(self.ledger_path, "a") as f:
                # Exclusive lock
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    # Move to end (in case concurrent reads happened)
                    f.seek(0, os.SEEK_END)
                    # Write entry
                    f.write(canonical_json(enriched_entry) + "\n")
                    # Flush to kernel buffer
                    f.flush()
                    # Fsync to disk (CRITICAL: guarantees durability)
                    os.fsync(f.fileno())
                finally:
                    # Release lock
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            return entry_hash

        except Exception as e:
            error_msg = f"[ERROR] Failed to append receipt: {e}"
            if fail_on_error:
                raise RuntimeError(error_msg)
            else:
                print(error_msg)
                return None

    def verify_chain(self) -> bool:
        """
        Verify integrity of the entire receipt chain.

        Checks:
        1. Each entry's prev_hash matches previous entry's entry_hash
        2. Each entry's entry_hash matches computed hash of entry contents

        Returns:
            True if chain is valid, False otherwise.
        """
        if not os.path.exists(self.ledger_path):
            print(f"[INFO] Ledger does not exist: {self.ledger_path}")
            return True

        prev_entry_hash = ""
        line_num = 0

        try:
            with open(self.ledger_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    entry = json.loads(line)

                    # Check prev_hash
                    if entry.get("prev_hash") != prev_entry_hash:
                        print(
                            f"[ERROR] Line {line_num}: prev_hash mismatch. "
                            f"Expected '{prev_entry_hash}', got '{entry.get('prev_hash')}'"
                        )
                        return False

                    # Check entry_hash
                    tmp = dict(entry)
                    tmp.pop("entry_hash", None)
                    expected_hash = sha256_hex(canonical_json(tmp))
                    actual_hash = entry.get("entry_hash")

                    if actual_hash != expected_hash:
                        print(
                            f"[ERROR] Line {line_num}: entry_hash mismatch. "
                            f"Expected '{expected_hash}', got '{actual_hash}'"
                        )
                        return False

                    # Check context_hash (if present)
                    if "context_hash" in entry:
                        query_hash = entry.get("query_hash", "")
                        hits = entry.get("hits", [])
                        context_data = {"query_hash": query_hash, "hits": hits}
                        expected_context_hash = sha256_hex(canonical_json(context_data))
                        actual_context_hash = entry.get("context_hash")

                        if actual_context_hash != expected_context_hash:
                            print(
                                f"[ERROR] Line {line_num}: context_hash mismatch. "
                                f"Expected '{expected_context_hash}', got '{actual_context_hash}'"
                            )
                            return False

                    prev_entry_hash = actual_hash

        except json.JSONDecodeError as e:
            print(f"[ERROR] Line {line_num}: JSON decode error: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Verification failed: {e}")
            return False

        print(f"[INFO] Receipt chain verified: {line_num} entries, all valid")
        return True

    def get_digest(self) -> Optional[str]:
        """
        Get the cumulative digest (hash of last entry).
        This is what you'd sign for tamper-evidence proof.

        Returns:
            The entry_hash of the last entry, or None if ledger is empty.
        """
        last_hash = self._get_last_entry_hash()
        return last_hash if last_hash else None


# Convenience functions for HELEN integration
def append_memory_hit(
    query: str,
    hits: list,
    fail_closed: bool = True,
    ledger_path: str = "receipts/memory_hits.jsonl"
) -> Optional[str]:
    """
    Log a memory retrieval hit to the receipt chain.

    Args:
        query: The query string
        hits: List of {id, source, score} dicts
        fail_closed: If True, raise on write failure (SECURE)
        ledger_path: Path to ledger

    Returns:
        The receipt entry_hash, or None on failure
    """
    chain = ReceiptChain(ledger_path)

    # Build entry
    entry = {
        "type": "memory_hit",
        "query": query,
        "query_hash": sha256_hex(query),
        "hits": [{"id": h.get("id"), "source": h.get("source"), "score": int(h.get("score", 0))}
                 for h in hits],
    }

    # Compute context_hash
    context_data = {"query_hash": entry["query_hash"], "hits": entry["hits"]}
    entry["context_hash"] = sha256_hex(canonical_json(context_data))

    # Append with atomic write
    return chain.append(entry, fail_on_error=fail_closed)


if __name__ == "__main__":
    # Test: create and verify a small chain
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        ledger = os.path.join(tmpdir, "test_receipts.jsonl")
        chain = ReceiptChain(ledger)

        # Append some entries
        print("[TEST] Appending 3 entries...")
        h1 = chain.append({"type": "test", "msg": "entry 1"})
        h2 = chain.append({"type": "test", "msg": "entry 2"})
        h3 = chain.append({"type": "test", "msg": "entry 3"})
        print(f"  Entry 1 hash: {h1}")
        print(f"  Entry 2 hash: {h2}")
        print(f"  Entry 3 hash: {h3}")

        # Verify
        print("\n[TEST] Verifying chain...")
        is_valid = chain.verify_chain()
        print(f"  Valid: {is_valid}")

        # Get digest
        print("\n[TEST] Get cumulative digest...")
        digest = chain.get_digest()
        print(f"  Digest: {digest}")
