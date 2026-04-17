"""
CI Replay Test — LEGORACLE Gate

Deterministic replay enforcement for the LEGORACLE obligation-checking validator.

Contract:
  - Same fixture → same verdict, same decision_hash, every run
  - SHIP fixture stays SHIP on replay
  - NO_SHIP fixture stays NO_SHIP on replay
  - Any mismatch → non-zero exit (CI fails)
  - No kernel files mutated

Fixtures:
  fixtures/legoracle/proposal_ship.json        — valid packet, all obligations met
  fixtures/legoracle/proposal_no_ship.json      — empty receipts, NO_RECEIPT = NO_SHIP
  fixtures/legoracle/expected_decisions.json     — frozen expected outputs (verdict + hashes)
  fixtures/legoracle/environment_pin.json        — Python version, platform, fixture hashes

This test is the replay gate that upgrades legoracle_gate_poc from demo to infrastructure.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest

from helen_os.governance.legoracle_gate_poc import evaluate_proposal


FIXTURES = Path(__file__).parent / "fixtures" / "legoracle"


def _canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _load_expected() -> dict:
    return json.loads((FIXTURES / "expected_decisions.json").read_text(encoding="utf-8"))


# ─── Fixture integrity ────────────────────────────────────────────────────────

class TestFixtureIntegrity:
    """Fixtures must not have been tampered with since freeze."""

    def test_ship_fixture_hash_matches_pin(self):
        env = _load_fixture("environment_pin.json")
        ship = _load_fixture("proposal_ship.json")
        assert _sha256(_canon(ship)) == env["fixture_ship_hash"], \
            "proposal_ship.json has been modified since freeze"

    def test_no_ship_fixture_hash_matches_pin(self):
        env = _load_fixture("environment_pin.json")
        no_ship = _load_fixture("proposal_no_ship.json")
        assert _sha256(_canon(no_ship)) == env["fixture_no_ship_hash"], \
            "proposal_no_ship.json has been modified since freeze"


# ─── Replay determinism ──────────────────────────────────────────────────────

class TestReplayDeterminism:
    """Same fixture, run twice in the same process → identical output."""

    def test_ship_replay_identical_hash(self):
        ship = _load_fixture("proposal_ship.json")
        d1 = evaluate_proposal(ship)
        d2 = evaluate_proposal(ship)
        assert d1.decision_hash == d2.decision_hash
        assert d1.verdict == d2.verdict == "SHIP"
        assert d1.input_hash == d2.input_hash

    def test_no_ship_replay_identical_hash(self):
        no_ship = _load_fixture("proposal_no_ship.json")
        d1 = evaluate_proposal(no_ship)
        d2 = evaluate_proposal(no_ship)
        assert d1.decision_hash == d2.decision_hash
        assert d1.verdict == d2.verdict == "NO_SHIP"
        assert d1.input_hash == d2.input_hash


# ─── Frozen expected output comparison ────────────────────────────────────────

class TestFrozenExpectedOutputs:
    """Decision hashes must match the frozen expected_decisions.json."""

    def test_ship_verdict_matches_expected(self):
        expected = _load_expected()["proposal_ship.json"]
        ship = _load_fixture("proposal_ship.json")
        decision = evaluate_proposal(ship)
        assert decision.verdict == expected["verdict"], \
            f"verdict drift: got {decision.verdict}, expected {expected['verdict']}"

    def test_ship_decision_hash_matches_expected(self):
        expected = _load_expected()["proposal_ship.json"]
        ship = _load_fixture("proposal_ship.json")
        decision = evaluate_proposal(ship)
        assert decision.decision_hash == expected["decision_hash"], \
            f"decision_hash drift: got {decision.decision_hash}, expected {expected['decision_hash']}"

    def test_ship_input_hash_matches_expected(self):
        expected = _load_expected()["proposal_ship.json"]
        ship = _load_fixture("proposal_ship.json")
        decision = evaluate_proposal(ship)
        assert decision.input_hash == expected["input_hash"], \
            f"input_hash drift: got {decision.input_hash}, expected {expected['input_hash']}"

    def test_no_ship_verdict_matches_expected(self):
        expected = _load_expected()["proposal_no_ship.json"]
        no_ship = _load_fixture("proposal_no_ship.json")
        decision = evaluate_proposal(no_ship)
        assert decision.verdict == expected["verdict"]

    def test_no_ship_decision_hash_matches_expected(self):
        expected = _load_expected()["proposal_no_ship.json"]
        no_ship = _load_fixture("proposal_no_ship.json")
        decision = evaluate_proposal(no_ship)
        assert decision.decision_hash == expected["decision_hash"]

    def test_no_ship_obligations_missing_matches_expected(self):
        expected = _load_expected()["proposal_no_ship.json"]
        no_ship = _load_fixture("proposal_no_ship.json")
        decision = evaluate_proposal(no_ship)
        assert decision.obligations_missing == expected["obligations_missing"]


# ─── Negative harness: mutation detection ─────────────────────────────────────

class TestMutationDetection:
    """Mutating any input field must produce a different decision hash."""

    def test_mutated_packet_id_changes_hash(self):
        ship = _load_fixture("proposal_ship.json")
        expected = _load_expected()["proposal_ship.json"]
        ship["packet_id"] = "PROMO-MUTATED"
        decision = evaluate_proposal(ship)
        assert decision.decision_hash != expected["decision_hash"], \
            "mutation did not change decision_hash — replay gate is broken"
        assert decision.verdict == "SHIP"  # still valid, just different

    def test_removing_receipts_changes_verdict(self):
        ship = _load_fixture("proposal_ship.json")
        ship["receipts"] = []
        decision = evaluate_proposal(ship)
        assert decision.verdict == "NO_SHIP"
        assert decision.decision_hash != _load_expected()["proposal_ship.json"]["decision_hash"]
