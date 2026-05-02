"""
tests/test_hash_chain_payload_hash.py

PAYLOAD_HASH_V1 enforcement tests for tools/validate_hash_chain.py.

Pinned semantics:
    payload_hash = SHA256(CANON_JSON_V1(payload))
                 = sha256_hex(canon_json_bytes(payload))

Validators MUST recompute payload_hash from payload, not trust the
envelope. These tests construct ledger fixtures that violate the rule
and verify the validator rejects them.

Tests are pure-Python; no kernel binary required. They exercise the
validate_hash_chain.py module directly via its main() entrypoint.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.conftest_kernel import (
    GENESIS_HASH,
    chain_hash_v1,
    compute_expected,
    compute_payload_hash,
    sha256_hex,
)
from kernel.canonical_json import canon_json_bytes


# ---------------------------------------------------------------------------
# Fixture helpers — build a valid ledger event line, then mutate as needed
# ---------------------------------------------------------------------------

def _build_event(
    seq: int,
    payload: dict,
    prev_cum_hash: str,
    *,
    override_payload_hash: str | None = None,
    override_cum_hash: str | None = None,
    override_payload: dict | None = None,
) -> dict:
    """
    Build a ledger event dict.

    By default produces a valid event whose payload_hash and cum_hash are
    derived from `payload`. Overrides allow injecting tampered fields for
    red-test fixtures.
    """
    payload_hash, cum_hash = compute_expected(payload, prev_cum_hash)
    return {
        "type": "ASSERTION",
        "seq": seq,
        "payload": override_payload if override_payload is not None else payload,
        "payload_hash": override_payload_hash or payload_hash,
        "prev_cum_hash": prev_cum_hash,
        "cum_hash": override_cum_hash or cum_hash,
    }


def _write_ledger(tmp_path: Path, events: list[dict]) -> Path:
    """Write events as NDJSON to a tmp file."""
    p = tmp_path / "ledger.ndjson"
    with p.open("w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")
    return p


def _run_hash_chain_validator(ledger_path: Path) -> int:
    """
    Invoke validate_hash_chain.main() in-process. Returns exit code.

    Forces scheme=HELEN_CUM_V1 so the test does not depend on
    registries/environment.v1.json content.
    """
    from tools import validate_hash_chain

    try:
        validate_hash_chain.main(str(ledger_path), scheme_override="HELEN_CUM_V1")
        return 0
    except SystemExit as e:
        return int(e.code) if e.code is not None else 0


# ---------------------------------------------------------------------------
# RED tests — must FAIL when the rule is violated
# ---------------------------------------------------------------------------

def test_envelope_payload_hash_does_not_match_canon_payload_fails(tmp_path):
    """
    Rule: envelope.payload_hash MUST equal sha256(canon_json(envelope.payload)).
    Tampered envelope must be rejected.
    """
    payload = {"schema": "TEST_V1", "value": 1}
    bad_event = _build_event(
        seq=0,
        payload=payload,
        prev_cum_hash=GENESIS_HASH,
        override_payload_hash="0" * 64,  # blatantly wrong
    )
    ledger = _write_ledger(tmp_path, [bad_event])
    assert _run_hash_chain_validator(ledger) != 0


def test_payload_changed_but_envelope_hash_unchanged_fails(tmp_path):
    """
    Rule: cannot change the payload after-the-fact while keeping the original
    payload_hash. Validator recomputes from payload and detects the drift.
    """
    original_payload = {"schema": "TEST_V1", "value": 1}
    tampered_payload = {"schema": "TEST_V1", "value": 999}
    payload_hash, cum_hash = compute_expected(original_payload, GENESIS_HASH)
    bad_event = {
        "type": "ASSERTION",
        "seq": 0,
        "payload": tampered_payload,           # body changed
        "payload_hash": payload_hash,          # hash NOT updated
        "prev_cum_hash": GENESIS_HASH,
        "cum_hash": cum_hash,
    }
    ledger = _write_ledger(tmp_path, [bad_event])
    assert _run_hash_chain_validator(ledger) != 0


def test_cum_hash_breaks_chain_fails(tmp_path):
    """
    Rule: cum_hash = SHA256("HELEN_CUM_V1" || prev_cum_bytes || payload_hash_bytes).
    A tampered cum_hash must be rejected.
    """
    payload = {"schema": "TEST_V1", "value": 7}
    bad_event = _build_event(
        seq=0,
        payload=payload,
        prev_cum_hash=GENESIS_HASH,
        override_cum_hash="f" * 64,  # not the real cum_hash
    )
    ledger = _write_ledger(tmp_path, [bad_event])
    assert _run_hash_chain_validator(ledger) != 0


def test_seq_non_monotonic_fails(tmp_path):
    """Rule: seq starts at 0 and increments by 1."""
    payload = {"schema": "TEST_V1", "value": 1}
    bad_event = _build_event(seq=42, payload=payload, prev_cum_hash=GENESIS_HASH)
    ledger = _write_ledger(tmp_path, [bad_event])
    assert _run_hash_chain_validator(ledger) != 0


# ---------------------------------------------------------------------------
# GREEN tests — must PASS when the rule is satisfied
# ---------------------------------------------------------------------------

def test_valid_single_event_passes(tmp_path):
    """A single, hash-honest event passes."""
    payload = {"schema": "TEST_V1", "value": 1}
    good_event = _build_event(seq=0, payload=payload, prev_cum_hash=GENESIS_HASH)
    ledger = _write_ledger(tmp_path, [good_event])
    assert _run_hash_chain_validator(ledger) == 0


def test_valid_multi_event_chain_passes(tmp_path):
    """A multi-event hash-honest chain passes."""
    events = []
    prev = GENESIS_HASH
    for i in range(5):
        payload = {"schema": "TEST_V1", "i": i}
        ev = _build_event(seq=i, payload=payload, prev_cum_hash=prev)
        events.append(ev)
        prev = ev["cum_hash"]
    ledger = _write_ledger(tmp_path, events)
    assert _run_hash_chain_validator(ledger) == 0


# ---------------------------------------------------------------------------
# Canonicalization sanity — same payload, identical hash across runs
# ---------------------------------------------------------------------------

def test_canon_json_v1_is_deterministic():
    """
    canon_json_bytes must produce byte-identical output for the same payload
    across runs (sort_keys=True, separators=(",",":"), ensure_ascii=False).
    """
    payload = {"b": 2, "a": 1, "nested": {"y": "ñ", "x": True}}
    a = canon_json_bytes(payload)
    b = canon_json_bytes({"a": 1, "nested": {"x": True, "y": "ñ"}, "b": 2})
    assert a == b
    # And the resulting hash is stable
    assert sha256_hex(a) == sha256_hex(b)


def test_payload_hash_matches_compute_payload_hash_helper():
    """compute_payload_hash matches sha256(canon_json_bytes(payload))."""
    payload = {"verdict_id": "V-000001", "decision": {"outcome": "DELIVER"}}
    assert compute_payload_hash(payload) == sha256_hex(canon_json_bytes(payload))
