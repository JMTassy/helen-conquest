"""Decision ledger append-only module.

Law: Only reducer-emitted, append-only decision records may extend governed history.

Single responsibility:
- Receive SKILL_PROMOTION_DECISION_V1
- Append one immutable entry with entry hash
- Return new ledger with prior entries preserved

Public API:
- make_empty_ledger(ledger_id) -> dict    ← canonical empty ledger factory
- append_decision_to_ledger(ledger, decision) -> dict
"""
from __future__ import annotations

from typing import Any, Mapping

from helen_os.governance.canonical import sha256_prefixed


def make_empty_ledger(ledger_id: str) -> dict[str, Any]:
    """
    Return a canonical empty DECISION_LEDGER_V1.

    Single source of truth for empty ledger construction.
    All callers (tests, batch, replay, autoresearch) should use this
    instead of constructing the dict inline — eliminates schema drift.
    """
    return {
        "schema_name":    "DECISION_LEDGER_V1",
        "schema_version": "1.0.0",
        "ledger_id":      ledger_id,
        "entries":        [],
    }


def append_decision_to_ledger(
    ledger: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Append a reducer-emitted decision to append-only ledger.

    Rules:
    - Only SKILL_PROMOTION_DECISION_V1 appends
    - Other objects return ledger unchanged
    - Ledger is immutable copy with new entry appended
    - Entry hash computed from decision + prior entry hash
    """
    # Validate ledger schema
    if not isinstance(ledger, dict):
        return ledger

    if ledger.get("schema_name") != "DECISION_LEDGER_V1":
        return ledger

    # Validate decision schema
    if not isinstance(decision, dict):
        return ledger

    if decision.get("schema_name") != "SKILL_PROMOTION_DECISION_V1":
        return ledger

    # Copy ledger
    new_ledger = {
        "schema_name": ledger["schema_name"],
        "schema_version": ledger["schema_version"],
        "ledger_id": ledger["ledger_id"],
        "entries": [dict(e) for e in ledger.get("entries", [])],
    }

    # Get previous entry hash
    prev_entries = new_ledger["entries"]
    if prev_entries:
        prev_entry_hash = prev_entries[-1]["entry_hash"]
    else:
        prev_entry_hash = None

    # Compute entry hash: SHA256(decision_json + prev_hash)
    # Canonicalize decision, then concatenate with prev_hash for chaining
    decision_hash = sha256_prefixed(decision)
    entry_hash_input = {
        "decision_hash": decision_hash,
        "prev_entry_hash": prev_entry_hash,
    }
    entry_hash = sha256_prefixed(entry_hash_input)

    # Create new entry
    entry_index = len(prev_entries)
    new_entry = {
        "entry_index": entry_index,
        "prev_entry_hash": prev_entry_hash,
        "decision": dict(decision),
        "entry_hash": entry_hash,
    }

    # Append to ledger
    new_ledger["entries"].append(new_entry)

    return new_ledger
