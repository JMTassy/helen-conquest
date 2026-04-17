"""
Tests for LEGORACLE Gate POC.

Three tests, three properties:
  1. Valid receipt path → SHIP
  2. Missing obligation → NO_SHIP
  3. Same input twice → identical hash/verdict (replay determinism)
"""
import pytest

from helen_os.governance.legoracle_gate_poc import evaluate_proposal, _canon, _sha256


def _valid_promotion_packet():
    """A fully valid SKILL_PROMOTION_PACKET_V1 with all obligations satisfied."""
    return {
        "schema_name": "SKILL_PROMOTION_PACKET_V1",
        "schema_version": "1.0.0",
        "packet_id": "PROMO-REPLAY-001",
        "skill_id": "WEB_SEARCH",
        "candidate_version": "WEB_SEARCH_V4",
        "lineage": {
            "parent_skill_id": "WEB_SEARCH",
            "parent_version": "WEB_SEARCH_V3",
            "proposal_sha256": "sha256:" + "a" * 64,
        },
        "capability_manifest_sha256": "sha256:" + "b" * 64,
        "doctrine_surface": {
            "law_surface_version": "KERNEL_V2_1.0",
            "transfer_required": True,
        },
        "evaluation": {
            "threshold_name": "pass_rate",
            "threshold_value": 0.95,
            "observed_value": 0.98,
            "passed": True,
        },
        "receipts": [
            {"receipt_id": "R1", "payload": {"type": "eval"}, "sha256": "sha256:" + "c" * 64},
        ],
    }


# ─── Test 1: Valid receipt path → SHIP ────────────────────────────────────────

def test_valid_proposal_ships():
    """A proposal with all obligations satisfied gets SHIP."""
    proposal = _valid_promotion_packet()
    decision = evaluate_proposal(proposal)

    assert decision.verdict == "SHIP"
    assert decision.obligations_total == 12
    assert decision.obligations_satisfied == 12
    assert decision.obligations_missing == []
    assert decision.schema_name == "SKILL_PROMOTION_PACKET_V1"
    assert len(decision.input_hash) == 64
    assert len(decision.decision_hash) == 64

    # Decision record is well-formed
    record = decision.to_dict()
    assert record["schema_name"] == "LEGORACLE_DECISION_V1"
    assert record["verdict"] == "SHIP"


# ─── Test 2: Missing obligation → NO_SHIP ────────────────────────────────────

def test_missing_receipts_blocks():
    """A proposal with empty receipts gets NO_SHIP (NO_RECEIPT = NO_SHIP)."""
    proposal = _valid_promotion_packet()
    proposal["receipts"] = []
    decision = evaluate_proposal(proposal)

    assert decision.verdict == "NO_SHIP"
    assert "receipts" in decision.obligations_missing
    assert decision.obligations_satisfied < decision.obligations_total


def test_missing_schema_name_blocks():
    """A proposal without schema_name gets NO_SHIP."""
    proposal = {"some_field": "value"}
    decision = evaluate_proposal(proposal)

    assert decision.verdict == "NO_SHIP"
    assert "schema_name" in decision.obligations_missing


def test_failed_evaluation_blocks():
    """A proposal where evaluation.passed is False gets NO_SHIP."""
    proposal = _valid_promotion_packet()
    proposal["evaluation"]["passed"] = False
    decision = evaluate_proposal(proposal)

    assert decision.verdict == "NO_SHIP"
    assert "evaluation.passed" in decision.obligations_missing


def test_missing_nested_field_blocks():
    """A proposal missing a nested obligation (lineage.proposal_sha256) gets NO_SHIP."""
    proposal = _valid_promotion_packet()
    del proposal["lineage"]["proposal_sha256"]
    decision = evaluate_proposal(proposal)

    assert decision.verdict == "NO_SHIP"
    assert "lineage.proposal_sha256" in decision.obligations_missing


# ─── Test 3: Same input twice → identical hash/verdict (replay) ───────────────

def test_replay_determinism():
    """Same proposal evaluated twice produces identical decision_hash and verdict."""
    proposal = _valid_promotion_packet()

    decision_a = evaluate_proposal(proposal)
    decision_b = evaluate_proposal(proposal)

    assert decision_a.verdict == decision_b.verdict
    assert decision_a.input_hash == decision_b.input_hash
    assert decision_a.decision_hash == decision_b.decision_hash
    assert decision_a.obligations_missing == decision_b.obligations_missing


def test_replay_determinism_no_ship():
    """Replay determinism holds for NO_SHIP paths too."""
    proposal = _valid_promotion_packet()
    proposal["receipts"] = []

    decision_a = evaluate_proposal(proposal)
    decision_b = evaluate_proposal(proposal)

    assert decision_a.verdict == "NO_SHIP"
    assert decision_a.verdict == decision_b.verdict
    assert decision_a.decision_hash == decision_b.decision_hash


def test_different_input_different_hash():
    """Different proposals produce different decision hashes."""
    proposal_a = _valid_promotion_packet()
    proposal_b = _valid_promotion_packet()
    proposal_b["packet_id"] = "PROMO-DIFFERENT"

    decision_a = evaluate_proposal(proposal_a)
    decision_b = evaluate_proposal(proposal_b)

    assert decision_a.input_hash != decision_b.input_hash
    # Decision hashes differ because input_hash is part of the decision record
    assert decision_a.decision_hash != decision_b.decision_hash
    # But both SHIP
    assert decision_a.verdict == decision_b.verdict == "SHIP"
