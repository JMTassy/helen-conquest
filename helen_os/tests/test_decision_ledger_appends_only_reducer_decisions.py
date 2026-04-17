"""Test: Decision ledger appends only reducer-emitted decisions."""
from __future__ import annotations

from helen_os.state.decision_ledger_v1 import append_decision_to_ledger


def _empty_ledger():
    return {
        "schema_name": "DECISION_LEDGER_V1",
        "schema_version": "1.0.0",
        "ledger_id": "ledger_001",
        "canonicalization": "JCS_SHA256_V1",
        "entries": [],
    }


def _valid_decision():
    return {
        "schema_name": "SKILL_PROMOTION_DECISION_V1",
        "schema_version": "1.0.0",
        "decision_id": "dec_001",
        "skill_id": "skill.demo",
        "candidate_version": "1.0.0",
        "decision_type": "ADMITTED",
        "candidate_identity_hash": "sha256:" + "c" * 64,
        "reason_code": "OK_ADMITTED",
    }


def test_valid_decision_appends():
    """Valid decision appends to ledger."""
    ledger = _empty_ledger()
    decision = _valid_decision()

    result = append_decision_to_ledger(ledger, decision)

    assert len(result["entries"]) == 1
    assert result["entries"][0]["entry_index"] == 0
    assert result["entries"][0]["prev_entry_hash"] is None
    assert result["entries"][0]["decision"]["decision_id"] == "dec_001"
    assert result["entries"][0]["entry_hash"].startswith("sha256:")


def test_invalid_object_does_not_append():
    """Non-decision object does not append."""
    ledger = _empty_ledger()
    invalid = {"schema_name": "RANDOM_OBJECT_V1", "data": "test"}

    result = append_decision_to_ledger(ledger, invalid)

    # Ledger unchanged
    assert len(result["entries"]) == 0
    assert result == ledger


def test_appending_preserves_previous_entries():
    """Multiple appends preserve all prior entries."""
    ledger = _empty_ledger()

    # First append
    decision1 = {
        **_valid_decision(),
        "decision_id": "dec_001",
    }
    ledger = append_decision_to_ledger(ledger, decision1)
    assert len(ledger["entries"]) == 1
    first_hash = ledger["entries"][0]["entry_hash"]

    # Second append
    decision2 = {
        **_valid_decision(),
        "decision_id": "dec_002",
    }
    ledger = append_decision_to_ledger(ledger, decision2)

    # Both entries present
    assert len(ledger["entries"]) == 2
    assert ledger["entries"][0]["entry_hash"] == first_hash  # Unchanged
    assert ledger["entries"][0]["decision"]["decision_id"] == "dec_001"
    assert ledger["entries"][1]["decision"]["decision_id"] == "dec_002"
    assert ledger["entries"][1]["prev_entry_hash"] == first_hash  # Chained


def test_same_decision_on_same_ledger_yields_same_entry_hash():
    """Determinism: appending same decision to same ledger produces same hash."""
    ledger = _empty_ledger()
    decision = _valid_decision()

    # First append
    result1 = append_decision_to_ledger(ledger, decision)
    hash1 = result1["entries"][0]["entry_hash"]

    # Second append of same decision to same ledger
    result2 = append_decision_to_ledger(ledger, decision)
    hash2 = result2["entries"][0]["entry_hash"]

    # Hashes must be identical
    assert hash1 == hash2
    assert hash1.startswith("sha256:")
