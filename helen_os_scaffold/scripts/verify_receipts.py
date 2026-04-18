#!/usr/bin/env python3
"""
Receipt Chain Verification Script
==================================
Verify the integrity of HELEN's receipt chain.

Usage:
    python scripts/verify_receipts.py [--ledger LEDGER_PATH] [--verbose]
    python scripts/verify_receipts.py  # Uses default: receipts/memory_hits.jsonl

Exit codes:
    0 = Chain valid, all entries checked
    1 = Chain invalid (tampering detected)
    2 = File not found or I/O error
"""

import sys
import json
import hashlib
import argparse
from pathlib import Path


def canonical_json(obj):
    """Serialize to canonical JSON (sorted keys, no whitespace)."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def sha256_hex(text):
    """Compute SHA256 hash of text."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def verify_chain(ledger_path, verbose=False):
    """
    Verify receipt chain integrity.

    Args:
        ledger_path: Path to NDJSON ledger
        verbose: Print detailed info for each entry

    Returns:
        (is_valid: bool, num_entries: int, errors: list)
    """
    ledger_path = Path(ledger_path)

    if not ledger_path.exists():
        return False, 0, [f"Ledger not found: {ledger_path}"]

    errors = []
    prev_entry_hash = ""
    num_entries = 0

    try:
        with open(ledger_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                num_entries += 1

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError as e:
                    errors.append(f"Line {line_num}: JSON decode error: {e}")
                    continue

                # Check prev_hash
                actual_prev = entry.get("prev_hash", "")
                if actual_prev != prev_entry_hash:
                    errors.append(
                        f"Line {line_num}: prev_hash mismatch. "
                        f"Expected '{prev_entry_hash}', got '{actual_prev}'"
                    )
                    if verbose:
                        print(f"  [X] Entry {num_entries} (line {line_num}): prev_hash FAIL")
                else:
                    if verbose:
                        print(f"  [✓] Entry {num_entries} (line {line_num}): prev_hash OK")

                # Check entry_hash
                tmp = dict(entry)
                tmp.pop("entry_hash", None)
                expected_entry_hash = sha256_hex(canonical_json(tmp))
                actual_entry_hash = entry.get("entry_hash")

                if actual_entry_hash != expected_entry_hash:
                    errors.append(
                        f"Line {line_num}: entry_hash mismatch. "
                        f"Expected '{expected_entry_hash}', got '{actual_entry_hash}'"
                    )
                    if verbose:
                        print(f"  [X] Entry {num_entries} (line {line_num}): entry_hash FAIL")
                else:
                    if verbose:
                        print(f"  [✓] Entry {num_entries} (line {line_num}): entry_hash OK")

                # Check context_hash (if present)
                if "context_hash" in entry:
                    query_hash = entry.get("query_hash", "")
                    hits = entry.get("hits", [])
                    context_data = {"query_hash": query_hash, "hits": hits}
                    expected_context_hash = sha256_hex(canonical_json(context_data))
                    actual_context_hash = entry.get("context_hash")

                    if actual_context_hash != expected_context_hash:
                        errors.append(
                            f"Line {line_num}: context_hash mismatch. "
                            f"Expected '{expected_context_hash}', got '{actual_context_hash}'"
                        )
                        if verbose:
                            print(f"  [X] Entry {num_entries} (line {line_num}): context_hash FAIL")
                    else:
                        if verbose:
                            print(f"  [✓] Entry {num_entries} (line {line_num}): context_hash OK")

                prev_entry_hash = actual_entry_hash

    except Exception as e:
        errors.append(f"Verification failed with exception: {e}")
        return False, num_entries, errors

    is_valid = len(errors) == 0
    return is_valid, num_entries, errors


def main():
    parser = argparse.ArgumentParser(
        description="Verify HELEN's receipt chain integrity."
    )
    parser.add_argument(
        "--ledger",
        default="receipts/memory_hits.jsonl",
        help="Path to receipt ledger (default: receipts/memory_hits.jsonl)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed info for each entry"
    )

    args = parser.parse_args()

    print(f"Verifying receipt chain: {args.ledger}")
    print("-" * 70)

    is_valid, num_entries, errors = verify_chain(args.ledger, verbose=args.verbose)

    if is_valid:
        print(f"✅ Chain is valid. {num_entries} entries verified.")
        return 0
    else:
        print(f"❌ Chain is INVALID. {num_entries} entries checked, {len(errors)} errors found:\n")
        for error in errors:
            print(f"  {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
