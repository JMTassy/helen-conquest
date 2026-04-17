from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from jsonschema import Draft202012Validator
from helen_os.state.ledger_replay_v1 import replay_ledger_to_state
from .canonical import canonical_json_bytes, sha256_prefixed

CANONICAL_PHRASE = (
    "Toute décision valide peut étendre l'histoire. "
    "Seule une décision autorisée par le reducer peut muter l'état gouverné."
)


# -------------------------
# Canonicalization wrappers (delegates to canonical.py)
# -------------------------


def entry_hash_of(entry_without_hash: Dict[str, Any]) -> str:
    """Compute entry hash using canonical primitives."""
    return sha256_prefixed(entry_without_hash)


def hash_state(state: Dict[str, Any]) -> str:
    """Compute state hash using canonical primitives."""
    return sha256_prefixed(state)


# -------------------------
# Schema loading + validation
# -------------------------


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_against(schema: Dict[str, Any], obj: Any) -> List[str]:
    v = Draft202012Validator(schema)
    errs = sorted(v.iter_errors(obj), key=lambda e: list(e.path))
    out: List[str] = []
    for e in errs:
        p = "/".join(map(str, e.path))
        out.append(f"ERR_SCHEMA_INVALID:{p}:{e.message}")
    return out


# -------------------------
# Ledger prefix helper (for rollback proof)
# -------------------------


def make_ledger_prefix(ledger: Dict[str, Any], end_index: int) -> Dict[str, Any]:
    """
    Return a ledger object with entries truncated to entries[:end_index].
    Keeps top-level metadata stable for deterministic replay.

    Used for ROLLED_BACK verification: replaying entries[0:target_index]
    must yield the prior_state_hash claimed in the rollback decision.
    """
    prefix = dict(ledger)
    prefix["entries"] = list(ledger.get("entries", []))[:end_index]
    return prefix


# -------------------------
# Validation result
# -------------------------


@dataclass(frozen=True)
class LedgerValidationResult:
    ok: bool
    reason_codes: List[str]
    admitted_entry_indexes: List[int]


# -------------------------
# Main validator
# -------------------------


def validate_decision_ledger_v1(
    *,
    ledger: Dict[str, Any],
    schemas_dir: Path,
    initial_state: Dict[str, Any],
    decision_schema_filename: str = "skill_promotion_decision_v1.json",
    ledger_schema_filename: str = "decision_ledger_v1.json",
) -> LedgerValidationResult:
    """
    Enforces:
      - ledger schema validity (decision opaque)
      - entry_index == position
      - first prev_entry_hash == null
      - prev_entry_hash chains on prior entry_hash
      - entry_hash recomputation (sha256:JCS(entry_without_entry_hash))
      - decision full validation against SKILL_PROMOTION_DECISION_V1
      - ROLLED_BACK semantics:
          * rollback_target_entry_index < current index
          * target entry decision_type == ADMITTED
          * prior_state_hash == hash(replay(entries[0:target_index], initial_state))
    """
    reasons: List[str] = []
    admitted_indexes: List[int] = []

    ledger_schema = load_json(schemas_dir / ledger_schema_filename)
    decision_schema = load_json(schemas_dir / decision_schema_filename)

    # 1) ledger schema (structure only)
    errs = validate_against(ledger_schema, ledger)
    if errs:
        return LedgerValidationResult(False, errs, [])

    if ledger.get("canonicalization") != "JCS_SHA256_V1":
        return LedgerValidationResult(False, ["ERR_CANONICALIZATION_MISMATCH"], [])

    entries = ledger["entries"]

    # 2) chain + decision schema + entry_hash
    prev_hash: Optional[str] = None
    decision_type_by_index: Dict[int, str] = {}

    for i, entry in enumerate(entries):
        if entry["entry_index"] != i:
            reasons.append("ERR_LEDGER_INDEX_MISMATCH")

        if i == 0:
            if entry["prev_entry_hash"] is not None:
                reasons.append("ERR_LEDGER_FIRST_PREV_NOT_NULL")
        else:
            if entry["prev_entry_hash"] != prev_hash:
                reasons.append("ERR_LEDGER_CHAIN_BROKEN")

        # recompute entry_hash
        entry_wo = dict(entry)
        entry_wo.pop("entry_hash", None)
        recomputed = entry_hash_of(entry_wo)
        if recomputed != entry["entry_hash"]:
            reasons.append("ERR_LEDGER_ENTRY_HASH_MISMATCH")

        # decision full validation (single source of truth)
        dec = entry["decision"]
        derrs = validate_against(decision_schema, dec)
        if derrs:
            reasons.extend(derrs)

        dt = dec.get("decision_type")
        if isinstance(dt, str):
            decision_type_by_index[i] = dt
            if dt == "ADMITTED":
                admitted_indexes.append(i)

        prev_hash = entry["entry_hash"]

    if reasons:
        return LedgerValidationResult(False, sorted(set(reasons)), admitted_indexes)

    # 3) ROLLED_BACK semantic verification
    for i, entry in enumerate(entries):
        dec = entry["decision"]
        if dec.get("decision_type") != "ROLLED_BACK":
            continue

        tgt = dec.get("rollback_target_entry_index")
        prior_state_hash = dec.get("prior_state_hash")

        # (a) target index integrity
        if not isinstance(tgt, int):
            return LedgerValidationResult(False, ["ERR_ROLLBACK_TARGET_MISSING"], admitted_indexes)
        if tgt < 0 or tgt >= i:
            return LedgerValidationResult(False, ["ERR_ROLLBACK_TARGET_OUT_OF_RANGE"], admitted_indexes)

        # (b) target must be ADMITTED
        if decision_type_by_index.get(tgt) != "ADMITTED":
            return LedgerValidationResult(False, ["ERR_ROLLBACK_TARGET_NOT_ADMITTED"], admitted_indexes)

        # (c) prior_state_hash format
        if not (isinstance(prior_state_hash, str) and prior_state_hash.startswith("sha256:") and len(prior_state_hash) == 71):
            return LedgerValidationResult(False, ["ERR_ROLLBACK_PRIOR_STATE_HASH_INVALID"], admitted_indexes)

        # (d) recompute expected prior state: replay(ledger[0:tgt]) using single primitive
        prefix_ledger = make_ledger_prefix(ledger, tgt)
        state_before = replay_ledger_to_state(ledger=prefix_ledger, initial_state=initial_state)
        expected = hash_state(state_before)

        if expected != prior_state_hash:
            return LedgerValidationResult(False, ["ERR_ROLLBACK_PRIOR_STATE_HASH_MISMATCH"], admitted_indexes)

    return LedgerValidationResult(True, [], admitted_indexes)
