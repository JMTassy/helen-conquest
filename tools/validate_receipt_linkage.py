#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_receipt_linkage.py v2.1.0
Production-hardened receipt linkage validator.

Rules enforced:
  1. Every RECEIPT payload with schema == "RECEIPT_PAYLOAD_V1" must have:
       - refs.verdict_id pointing to an existing VERDICT event
  2. Triple binding (per RECEIPT):
       refs.ref_verdict_payload_hash_hex == VERDICT_event.payload_hash   [leg 1]
       refs.ref_verdict_cum_hash_hex      == VERDICT_event.cum_hash       [leg 2]
       recomputed.verdict_payload_hash_hex == refs.ref_verdict_payload_hash_hex  [leg 3]
  3. NO RECEIPT = NO SHIP:
       Every VERDICT with verdict_kind == "SHIP" must have at least one
       RECEIPT_PAYLOAD_V1 RECEIPT bound to it.

Design: core logic (load_ledger, validate_receipt_linkage) raises ValueError.
        CLI wrapper (main) catches ValueError → prints [FAIL] → exits 1.
        This enables unit testing without subprocess overhead.
"""

import sys
import os as _os
_repo_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)
import json
import hashlib
from kernel.canonical_json import canon_json_bytes


# ──────────────────────────────────────────────────────────────────────────────
# Canonical JSON (matches ndjson_writer.py — CANON_JSON_V1)
# ──────────────────────────────────────────────────────────────────────────────

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ──────────────────────────────────────────────────────────────────────────────
# Ledger loading
# ──────────────────────────────────────────────────────────────────────────────

def load_ledger(ledger_path: str) -> list:
    """
    Load and parse NDJSON ledger.
    Returns list of (line_num, parsed_obj) tuples.
    Raises ValueError on file-not-found or invalid JSON.
    """
    try:
        with open(ledger_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        raise ValueError(f"File not found: {ledger_path}")

    events = []
    for i, line in enumerate(lines, start=1):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"Line {i}: Invalid JSON: {e}")
        events.append((i, obj))
    return events


# ──────────────────────────────────────────────────────────────────────────────
# Index builders
# ──────────────────────────────────────────────────────────────────────────────

def _build_verdict_map(events: list) -> dict:
    """
    Build index: verdict_id → {payload_hash, cum_hash, seq, verdict_kind, line_num}

    Only indexes events with:
      - type == "VERDICT" (case-insensitive)
      - payload.schema == "VERDICT_PAYLOAD_V1"

    Legacy VERDICT events (other schemas) are skipped silently.
    """
    verdict_map = {}
    for line_num, obj in events:
        if obj.get("type", "").upper() != "VERDICT":
            continue
        payload = obj.get("payload", {})
        if payload.get("schema") != "VERDICT_PAYLOAD_V1":
            continue
        verdict_id = payload.get("verdict_id", "")
        if not verdict_id:
            continue
        verdict_map[verdict_id] = {
            "payload_hash": obj.get("payload_hash", ""),
            "cum_hash": obj.get("cum_hash", ""),
            "seq": obj.get("seq", -1),
            "verdict_kind": payload.get("verdict_kind", ""),
            "line_num": line_num,
        }
    return verdict_map


def _build_receipt_bindings(events: list) -> dict:
    """
    Build index: verdict_id → [receipt_record, ...]

    Only indexes events with:
      - type == "RECEIPT" (case-insensitive)
      - payload.schema == "RECEIPT_PAYLOAD_V1"

    Raises ValueError if a RECEIPT_PAYLOAD_V1 event is missing refs.verdict_id.
    """
    receipt_bindings: dict = {}
    for line_num, obj in events:
        if obj.get("type", "").upper() != "RECEIPT":
            continue
        payload = obj.get("payload", {})
        if payload.get("schema") != "RECEIPT_PAYLOAD_V1":
            continue
        refs = payload.get("refs", {})
        verdict_id = refs.get("verdict_id", "")
        if not verdict_id:
            raise ValueError(
                f"Line {line_num}: RECEIPT_PAYLOAD_V1 event missing refs.verdict_id"
            )
        record = {
            "line_num": line_num,
            "seq": obj.get("seq", -1),
            "payload_hash": obj.get("payload_hash", ""),
            "cum_hash": obj.get("cum_hash", ""),
            "refs": refs,
            "recomputed": payload.get("recomputed", {}),
        }
        receipt_bindings.setdefault(verdict_id, []).append(record)
    return receipt_bindings


# ──────────────────────────────────────────────────────────────────────────────
# Triple-binding validation
# ──────────────────────────────────────────────────────────────────────────────

def _validate_triple_binding(receipt: dict, verdict: dict, verdict_id: str) -> None:
    """
    Validate the three binding legs for a single (receipt, verdict) pair.
    Raises ValueError with explicit leg identifier on failure.
    """
    refs = receipt["refs"]
    recomputed = receipt["recomputed"]
    rline = receipt["line_num"]

    # Leg 1 — payload_hash binding
    ref_ph = refs.get("ref_verdict_payload_hash_hex", "")
    verdict_ph = verdict["payload_hash"]
    if ref_ph != verdict_ph:
        raise ValueError(
            f"Line {rline}: RECEIPT triple-binding FAIL [leg 1 — payload_hash]: "
            f"receipt.refs.ref_verdict_payload_hash_hex='{ref_ph}' "
            f"!= VERDICT event payload_hash='{verdict_ph}' "
            f"(verdict_id='{verdict_id}')"
        )

    # Leg 2 — cum_hash binding
    ref_ch = refs.get("ref_verdict_cum_hash_hex", "")
    verdict_ch = verdict["cum_hash"]
    if ref_ch != verdict_ch:
        raise ValueError(
            f"Line {rline}: RECEIPT triple-binding FAIL [leg 2 — cum_hash]: "
            f"receipt.refs.ref_verdict_cum_hash_hex='{ref_ch}' "
            f"!= VERDICT event cum_hash='{verdict_ch}' "
            f"(verdict_id='{verdict_id}')"
        )

    # Leg 3 — recomputed consistency
    recomp_ph = recomputed.get("verdict_payload_hash_hex", "")
    if recomp_ph and recomp_ph != ref_ph:
        raise ValueError(
            f"Line {rline}: RECEIPT triple-binding FAIL [leg 3 — recomputed]: "
            f"recomputed.verdict_payload_hash_hex='{recomp_ph}' "
            f"!= refs.ref_verdict_payload_hash_hex='{ref_ph}' "
            f"(verdict_id='{verdict_id}')"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Main validation logic (pure — raises ValueError, no sys.exit)
# ──────────────────────────────────────────────────────────────────────────────

def validate_receipt_linkage(events: list) -> tuple:
    """
    Validate receipt linkage across all events.

    Returns (verdict_count, receipt_count) on success.
    Raises ValueError with a descriptive message on first violation.
    """
    verdict_map = _build_verdict_map(events)
    receipt_bindings = _build_receipt_bindings(events)

    # ── Validate each RECEIPT against its VERDICT ───────────────────────────
    for verdict_id, receipts in receipt_bindings.items():
        if verdict_id not in verdict_map:
            raise ValueError(
                f"RECEIPT.refs.verdict_id='{verdict_id}' not found in any "
                f"VERDICT_PAYLOAD_V1 event "
                f"(first RECEIPT at line {receipts[0]['line_num']})"
            )
        verdict = verdict_map[verdict_id]
        for receipt in receipts:
            _validate_triple_binding(receipt, verdict, verdict_id)

    # ── NO RECEIPT = NO SHIP ─────────────────────────────────────────────────
    for verdict_id, verdict in verdict_map.items():
        if verdict["verdict_kind"] == "SHIP":
            bound = receipt_bindings.get(verdict_id, [])
            if not bound:
                raise ValueError(
                    f"NO RECEIPT = NO SHIP violated: "
                    f"VERDICT verdict_id='{verdict_id}' has verdict_kind=SHIP "
                    f"but no RECEIPT_PAYLOAD_V1 RECEIPT is bound to it "
                    f"(VERDICT at line {verdict['line_num']})"
                )

    verdict_count = len(verdict_map)
    receipt_count = sum(len(rs) for rs in receipt_bindings.values())
    return verdict_count, receipt_count


# ──────────────────────────────────────────────────────────────────────────────
# CLI entry-point
# ──────────────────────────────────────────────────────────────────────────────

def main(ledger_path: str) -> None:
    """
    CLI wrapper. Loads ledger, runs validation, prints result, exits on failure.
    """
    try:
        events = load_ledger(ledger_path)
    except ValueError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        sys.exit(1)

    if not events:
        print("[PASS] Empty ledger (0 events)", file=sys.stderr)
        return

    try:
        verdict_count, receipt_count = validate_receipt_linkage(events)
    except ValueError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        sys.exit(1)

    print(
        f"[PASS] receipt linkage verified "
        f"({verdict_count} VERDICT events, {receipt_count} RECEIPT events, "
        f"triple-binding OK, NO RECEIPT = NO SHIP OK)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python3 validate_receipt_linkage.py <ledger.ndjson>",
            file=sys.stderr,
        )
        sys.exit(2)
    main(sys.argv[1])
