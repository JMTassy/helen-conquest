from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from helen_os.governance.ledger_validator_v1 import (
    validate_decision_ledger_v1,
    entry_hash_of,
    hash_state,
    make_ledger_prefix,
    CANONICAL_PHRASE,
)
from helen_os.state.ledger_replay_v1 import replay_ledger_to_state

DECISION_TYPES = {"ADMITTED", "REJECTED", "QUARANTINED", "ROLLED_BACK"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class BatchResult:
    processed: int
    appended: int
    final_ledger: Dict[str, Any]
    final_state: Dict[str, Any]
    final_state_hash: str


def append_entry(
    ledger: Dict[str, Any],
    decision: Dict[str, Any],
    now_fn: Callable[[], str] = now_iso,
) -> None:
    """
    Append decision to ledger as immutable entry.

    now_fn: injectable clock for deterministic testing.
    """
    entries = ledger["entries"]
    idx = len(entries)
    prev = None if idx == 0 else entries[-1]["entry_hash"]

    entry_wo = {
        "entry_index": idx,
        "ts": now_fn(),
        "prev_entry_hash": prev,
        "decision": decision,  # opaque at ledger schema level
    }
    eh = entry_hash_of(entry_wo)
    entry = dict(entry_wo)
    entry["entry_hash"] = eh
    entries.append(entry)


def apply_ledger_governed(
    *,
    ledger: Dict[str, Any],
    initial_state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Governed semantics (append-only):
      - ADMITTED => state becomes replay(prefix i+1)
      - REJECTED/QUARANTINED => no change
      - ROLLED_BACK => state becomes replay(prefix target_index)

    Uses single primitive: replay_ledger_to_state (never local replay).
    """
    state = initial_state
    entries = ledger.get("entries", [])

    for i, entry in enumerate(entries):
        dec = entry["decision"]
        dt = dec.get("decision_type")

        if dt == "ADMITTED":
            # Replay entire ledger up to and including this entry
            prefix = make_ledger_prefix(ledger, i + 1)
            state = replay_ledger_to_state(ledger=prefix, initial_state=initial_state)

        elif dt in ("REJECTED", "QUARANTINED"):
            # No state mutation
            continue

        elif dt == "ROLLED_BACK":
            # Replay ledger up to target entry (undoing all entries from target+1 onwards)
            tgt = dec["rollback_target_entry_index"]
            prefix = make_ledger_prefix(ledger, tgt)
            state = replay_ledger_to_state(ledger=prefix, initial_state=initial_state)

        # fail closed: unknown types do nothing

    return state


def autoresearch_batch_v1(
    *,
    decisions: List[Dict[str, Any]],
    initial_ledger: Optional[Dict[str, Any]],
    initial_state: Dict[str, Any],
    schemas_dir: Path,
    max_items: int,
    now_fn: Callable[[], str] = now_iso,
) -> BatchResult:
    """
    Bounded, deterministic batch executor.

    Args:
        decisions: decisions to append (bounded to max_items)
        initial_ledger: starting ledger (or None to create empty)
        initial_state: starting state
        schemas_dir: path to frozen schemas
        max_items: max decisions to process
        now_fn: injectable clock for deterministic testing

    Returns:
        BatchResult: final ledger, state, state hash
    """
    ledger = initial_ledger or {
        "schema_name": "DECISION_LEDGER_V1",
        "schema_version": "1.0.0",
        "ledger_id": "LEDGER-0001",
        "canonicalization": "JCS_SHA256_V1",
        "entries": [],
    }

    processed = 0
    appended = 0

    # 1) bounded + ordered append
    for dec in decisions[:max_items]:
        processed += 1
        if dec.get("decision_type") not in DECISION_TYPES:
            continue
        append_entry(ledger, dec, now_fn=now_fn)
        appended += 1

    # 2) validate full ledger (chain + decision schema + rollback semantics)
    vres = validate_decision_ledger_v1(
        ledger=ledger,
        schemas_dir=schemas_dir,
        initial_state=initial_state,
        decision_schema_filename="skill_promotion_decision_v1.json",
        ledger_schema_filename="decision_ledger_v1.json",
    )
    if not vres.ok:
        # fail closed: no mutation if ledger invalid
        return BatchResult(processed, appended, ledger, initial_state, hash_state(initial_state))

    # 3) governed state application (ADMITTED/ROLLED_BACK only)
    final_state = apply_ledger_governed(ledger=ledger, initial_state=initial_state)
    return BatchResult(processed, appended, ledger, final_state, hash_state(final_state))
