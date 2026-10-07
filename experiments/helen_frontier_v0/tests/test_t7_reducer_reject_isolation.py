"""T7 (local form): on the real reducer, REJECT ⇒ X_after == X_before.

Target: helen_os.governance.skill_promotion_reducer.reduce_promotion_packet, the
pure decision function used by the kernel daemon. Called read-only on temporary
fixtures. The reducer is not modified. The active ledger is not used; its file
is only hashed before/after as a read-only tripwire.

Proves, within this perimeter: a REJECTED decision leaves packet, state, the
working directory and the sovereign ledger file byte-identical, and grants
nothing (active_skills unchanged). The reducer emits no receipt itself, so the
"rejection receipt may be appended" clause of the wider contract does not apply
here; the daemon path that applies decisions is outside this test.

Does not prove: collective intelligence, contribution independence, or the
behaviour of the daemon's write path.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import pytest

from conftest import REPO_ROOT
from helen_os.governance.canonical import sha256_prefixed
from helen_os.governance.reason_codes import ReasonCode
from helen_os.governance.skill_promotion_reducer import reduce_promotion_packet

LEDGER = REPO_ROOT / "town" / "ledger_v1.ndjson"
ZERO = "sha256:" + "0" * 64


def _receipt() -> dict:
    payload = {"receipt_id": "R1", "payload": {"data": "valid"}}
    return {**payload, "sha256": sha256_prefixed(payload)}


def _packet() -> dict:
    return {
        "schema_name": "SKILL_PROMOTION_PACKET_V1",
        "schema_version": "1.0.0",
        "packet_id": "P-T7",
        "skill_id": "S1",
        "candidate_version": "1.0.0",
        "lineage": {"parent_skill_id": "S0", "parent_version": "0.9.0", "proposal_sha256": ZERO},
        "capability_manifest_sha256": ZERO,
        "doctrine_surface": {"law_surface_version": "v1", "transfer_required": False},
        "evaluation": {"threshold_name": "accuracy", "threshold_value": 0.9, "observed_value": 0.95, "passed": True},
        "receipts": [_receipt()],
    }


def _state() -> dict:
    return {
        "schema_name": "SKILL_LIBRARY_STATE_V1",
        "schema_version": "1.0.0",
        "law_surface_version": "v1",
        "active_skills": {"S0": {"active_version": "0.9.0", "status": "ACTIVE", "last_decision_id": "DEC0"}},
    }


def _file_hash(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree(path: Path) -> set[str]:
    return {str(p.relative_to(path)) for p in path.rglob("*")}


REJECT_CASES = {
    "schema_gate": (lambda p: p.__setitem__("schema_name", "WRONG_SCHEMA"), ReasonCode.ERR_SCHEMA_INVALID),
    # Empty receipts list is caught by the schema gate before the receipt gate,
    # so no reason code is pinned here; only the REJECTED decision is.
    "receipt_missing": (lambda p: p.__setitem__("receipts", []), None),
    "receipt_hash_mismatch": (
        lambda p: p.__setitem__("receipts", [{**_receipt(), "payload": {"data": "tampered"}}]),
        ReasonCode.ERR_RECEIPT_HASH_MISMATCH,
    ),
    "unknown_parent": (lambda p: p["lineage"].__setitem__("parent_skill_id", "S_NONE"), None),
    "threshold_not_met": (lambda p: p["evaluation"].__setitem__("passed", False), None),
}


@pytest.mark.parametrize("case", sorted(REJECT_CASES))
def test_reject_leaves_everything_unchanged(case, tmp_path, monkeypatch):
    mutate, expected_code = REJECT_CASES[case]
    monkeypatch.chdir(tmp_path)

    packet, state = _packet(), _state()
    mutate(packet)
    packet_before, state_before = copy.deepcopy(packet), copy.deepcopy(state)
    tree_before, ledger_before = _tree(tmp_path), _file_hash(LEDGER)

    result = reduce_promotion_packet(packet, state)

    assert result.decision == "REJECTED", (case, result)
    if expected_code is not None:
        assert result.reason_code == expected_code.value
    assert state == state_before, "governed state mutated under REJECT"
    assert packet == packet_before, "input packet mutated under REJECT"
    assert set(state["active_skills"]) == {"S0"}, "a grant appeared under REJECT"
    assert state["active_skills"]["S0"]["active_version"] == "0.9.0"
    assert _tree(tmp_path) == tree_before, "files written to cwd under REJECT"
    assert _file_hash(LEDGER) == ledger_before, "sovereign ledger file changed"


def test_reducer_decides_but_never_applies_even_on_admitted(tmp_path, monkeypatch):
    """Observation (not T7): the pure reducer mutates nothing on ADMITTED either.

    Application of decisions lives in the daemon write path, outside this test.
    """
    monkeypatch.chdir(tmp_path)
    packet, state = _packet(), _state()
    state_before, ledger_before = copy.deepcopy(state), _file_hash(LEDGER)
    result = reduce_promotion_packet(packet, state)
    assert result.decision == "ADMITTED"
    assert state == state_before
    assert _file_hash(LEDGER) == ledger_before
    assert _tree(tmp_path) == set()


def test_result_object_is_immutable():
    result = reduce_promotion_packet({**_packet(), "schema_name": "X"}, _state())
    with pytest.raises(Exception):
        result.decision = "ADMITTED"  # type: ignore[misc]
