"""E2E test: experiment → AUTORESEARCH_EVAL_RECEIPT_V1
           → AUTORESEARCH_PROMOTION_CASE_V1
           → SKILL_PROMOTION_PACKET_V1
           → reducer → SKILL_PROMOTION_DECISION_V1
           → state update → ledger append → replay verification.

This test closes the evaluation seam: proves the full pipeline from
a raw experimental outcome to governed ledger entry is mechanically
consistent, deterministic, and schema-correct.

Laws verified:
  L1 (Membrane):  Only reducer-emitted decisions may mutate governed state.
  L2 (Ledger):    Only reducer-emitted decisions extend governed history.
  L4 (Replay):    replay_ledger_to_state(ledger, initial) == final_state.

Eval pipeline invariants verified:
  EV1. evaluate_result() is pure: same inputs → same result.
  EV2. build_eval_receipt() result field == evaluate_result() output.
  EV3. validate_eval_receipt() rejects inconsistent result fields.
  EV4. assemble_promotion_packet() embeds receipt with correct sha256.
  EV5. Reducer admits packet iff eval_receipt.result == PASS.
  EV6. State unchanged before reducer ADMITTED.
  EV7. Full pipeline is deterministic across runs.
"""
from __future__ import annotations

import copy

import pytest

from helen_os.governance.canonical import sha256_prefixed
from helen_os.governance.skill_promotion_reducer import reduce_promotion_packet
from helen_os.state.decision_ledger_v1 import (
    append_decision_to_ledger,
    make_empty_ledger,
)
from helen_os.state.skill_library_state_updater import apply_skill_promotion_decision
from helen_os.state.ledger_replay_v1 import replay_ledger_to_state
from helen_os.eval.autoresearch_eval_receipt_v1 import (
    build_eval_receipt,
    evaluate_result,
    validate_eval_receipt,
    COMPARISON_RULES,
    RESULT_VALUES,
)
from helen_os.eval.autoresearch_promotion_case_v1 import (
    build_promotion_case,
    validate_promotion_case,
    assemble_promotion_packet,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _make_state() -> dict:
    def skill(v, d):
        return {"active_version": v, "status": "ACTIVE", "last_decision_id": d}

    return {
        "schema_name":         "SKILL_LIBRARY_STATE_V1",
        "schema_version":      "1.0.0",
        "law_surface_version": "TEMPLE_LAW_V1",
        "active_skills": {
            "skill.search":    skill("1.0.0", "dec_s_001"),
            "skill.discovery": skill("1.0.0", "dec_d_001"),
        },
    }


# Deterministic placeholder hashes (valid format, not real artifacts)
_RUN_LOG_HASH    = "sha256:" + "a" * 64
_ENV_HASH        = "sha256:" + "b" * 64
_DOCTRINE_HASH   = "sha256:" + "c" * 64


def _make_passing_receipt() -> dict:
    """Build a PASS eval receipt: candidate_value=0.88 > threshold=0.75 (gt)."""
    return build_eval_receipt(
        experiment_id="exp_search_recall_001",
        metric_name="recall@10",
        baseline_value=0.65,
        candidate_value=0.88,
        comparison_rule="gt",
        threshold=0.75,
        run_log_hash=_RUN_LOG_HASH,
        environment_manifest_hash=_ENV_HASH,
        doctrine_hash=_DOCTRINE_HASH,
    )


def _make_failing_receipt() -> dict:
    """Build a FAIL eval receipt: candidate_value=0.60 NOT > threshold=0.75 (gt)."""
    return build_eval_receipt(
        experiment_id="exp_search_recall_fail_001",
        metric_name="recall@10",
        baseline_value=0.65,
        candidate_value=0.60,
        comparison_rule="gt",
        threshold=0.75,
        run_log_hash=_RUN_LOG_HASH,
        environment_manifest_hash=_ENV_HASH,
        doctrine_hash=_DOCTRINE_HASH,
    )


def _make_case(receipt: dict) -> dict:
    return build_promotion_case(
        case_id="case_search_v2_001",
        skill_id="skill.search",
        candidate_version="2.0.0",
        parent_skill_id="skill.search",
        parent_version="1.0.0",
        eval_receipt=receipt,
        capability_description="Improved recall via semantic fallback.",
    )


def _build_decision(packet: dict, result: object) -> dict:
    return {
        "schema_name":    "SKILL_PROMOTION_DECISION_V1",
        "schema_version": "1.0.0",
        "decision_id":    f"dec_{packet['skill_id'].replace('.', '_')}_eval_001",
        "skill_id":       packet["skill_id"],
        "candidate_version": packet["candidate_version"],
        "decision_type":  result.decision,
        "reason_code":    result.reason_code,
    }


# ── EV1–EV3: Eval receipt unit properties ────────────────────────────────────

class TestEvalReceiptUnit:
    """EV1–EV3: evaluate_result() purity, build coherence, validate coherence."""

    def test_ev1_evaluate_result_pure(self):
        """EV1: same inputs → same result, no side effects."""
        assert evaluate_result(0.88, "gt", 0.75) == "PASS"
        assert evaluate_result(0.88, "gt", 0.75) == "PASS"  # idempotent

    def test_ev1_all_comparison_rules(self):
        """EV1: all 4 rules produce correct PASS/FAIL."""
        assert evaluate_result(1.0, "gt",  0.5) == "PASS"
        assert evaluate_result(0.5, "gt",  1.0) == "FAIL"
        assert evaluate_result(1.0, "gte", 1.0) == "PASS"
        assert evaluate_result(0.9, "gte", 1.0) == "FAIL"
        assert evaluate_result(0.3, "lt",  0.5) == "PASS"
        assert evaluate_result(0.6, "lt",  0.5) == "FAIL"
        assert evaluate_result(0.5, "lte", 0.5) == "PASS"
        assert evaluate_result(0.6, "lte", 0.5) == "FAIL"

    def test_ev1_unknown_rule_raises(self):
        """EV1: unknown comparison_rule raises ValueError."""
        with pytest.raises(ValueError, match="Unknown comparison_rule"):
            evaluate_result(0.88, "neq", 0.75)

    def test_ev2_build_receipt_result_coherent(self):
        """EV2: build_eval_receipt result matches evaluate_result."""
        receipt = _make_passing_receipt()
        expected = evaluate_result(
            receipt["candidate_value"],
            receipt["comparison_rule"],
            receipt["threshold"],
        )
        assert receipt["result"] == expected == "PASS"

    def test_ev2_fail_receipt_result_coherent(self):
        """EV2: FAIL receipt result matches evaluate_result."""
        receipt = _make_failing_receipt()
        expected = evaluate_result(
            receipt["candidate_value"],
            receipt["comparison_rule"],
            receipt["threshold"],
        )
        assert receipt["result"] == expected == "FAIL"

    def test_ev2_receipt_schema_valid(self):
        """EV2: built receipt passes schema validation."""
        receipt = _make_passing_receipt()
        valid, err = validate_eval_receipt(receipt)
        assert valid, f"validate_eval_receipt failed: {err}"

    def test_ev3_validate_rejects_inconsistent_result(self):
        """EV3: validator rejects receipt where result contradicts comparison."""
        receipt = _make_passing_receipt()
        tampered = dict(receipt, result="FAIL")  # PASS scenario but claims FAIL
        valid, err = validate_eval_receipt(tampered)
        assert not valid
        assert "inconsistent" in (err or "").lower()

    def test_ev3_inconclusive_exempt_from_coherence_check(self):
        """EV3: INCONCLUSIVE result skips coherence check (interrupted run)."""
        receipt = _make_passing_receipt()
        inconclusive = dict(receipt, result="INCONCLUSIVE")
        valid, err = validate_eval_receipt(inconclusive)
        assert valid, f"INCONCLUSIVE should be schema-valid: {err}"

    def test_ev3_frozen_enums(self):
        """EV3: comparison_rule and result are closed enums."""
        assert COMPARISON_RULES == frozenset({"gt", "gte", "lt", "lte"})
        assert RESULT_VALUES == frozenset({"PASS", "FAIL", "INCONCLUSIVE"})


# ── EV4: Promotion case and packet assembly ───────────────────────────────────

class TestPromotionCaseAssembly:
    """EV4: case validation, packet assembly, receipt sha256 integrity."""

    def test_ev4_case_authority_is_none(self):
        """EV4: promotion case carries authority=NONE."""
        case = _make_case(_make_passing_receipt())
        assert case["authority"] == "NONE"
        assert case["schema_name"] == "AUTORESEARCH_PROMOTION_CASE_V1"

    def test_ev4_case_schema_valid(self):
        """EV4: promotion case passes schema + invariant validation."""
        case = _make_case(_make_passing_receipt())
        valid, err = validate_promotion_case(case)
        assert valid, f"validate_promotion_case failed: {err}"

    def test_ev4_case_rejects_fail_receipt(self):
        """EV4: promotion case with FAIL receipt is schema-valid but FAIL flows through."""
        # Case itself is valid — it's the reducer that enforces PASS requirement
        case = _make_case(_make_failing_receipt())
        valid, err = validate_promotion_case(case)
        assert valid  # Case schema is valid; rejection happens at reducer Gate 6

    def test_ev4_packet_receipt_sha256_correct(self):
        """EV4: assembled packet receipt has correct sha256."""
        state = _make_state()
        case = _make_case(_make_passing_receipt())
        packet = assemble_promotion_packet(case, state)
        receipt = packet["receipts"][0]

        # Recompute sha256 the same way assemble_promotion_packet does
        hashable = {"receipt_id": receipt["receipt_id"], "payload": receipt["payload"]}
        expected_sha256 = sha256_prefixed(hashable)
        assert receipt["sha256"] == expected_sha256

    def test_ev4_packet_schema_name(self):
        """EV4: assembled packet has correct schema."""
        state = _make_state()
        case = _make_case(_make_passing_receipt())
        packet = assemble_promotion_packet(case, state)
        assert packet["schema_name"] == "SKILL_PROMOTION_PACKET_V1"
        assert packet["schema_version"] == "1.0.0"

    def test_ev4_packet_evaluation_passed_true_for_pass_receipt(self):
        """EV4: evaluation.passed=True when eval_receipt.result==PASS."""
        state = _make_state()
        case = _make_case(_make_passing_receipt())
        packet = assemble_promotion_packet(case, state)
        assert packet["evaluation"]["passed"] is True

    def test_ev4_packet_evaluation_passed_false_for_fail_receipt(self):
        """EV4: evaluation.passed=False when eval_receipt.result==FAIL."""
        state = _make_state()
        case = _make_case(_make_failing_receipt())
        packet = assemble_promotion_packet(case, state)
        assert packet["evaluation"]["passed"] is False


# ── EV5–EV6: Reducer gate ─────────────────────────────────────────────────────

class TestReducerGates:
    """EV5–EV6: Reducer admits PASS receipts, rejects FAIL receipts."""

    def test_ev5_reducer_admits_pass_receipt(self):
        """EV5: PASS eval receipt → reducer ADMITTED."""
        state = _make_state()
        case = _make_case(_make_passing_receipt())
        packet = assemble_promotion_packet(case, state)
        result = reduce_promotion_packet(packet, state)
        assert result.decision == "ADMITTED"
        assert result.reason_code == "OK_ADMITTED"

    def test_ev5_reducer_rejects_fail_receipt(self):
        """EV5: FAIL eval receipt → evaluation.passed=False → reducer REJECTED."""
        state = _make_state()
        case = _make_case(_make_failing_receipt())
        packet = assemble_promotion_packet(case, state)
        result = reduce_promotion_packet(packet, state)
        assert result.decision == "REJECTED"
        assert result.reason_code == "ERR_THRESHOLD_NOT_MET"

    def test_ev5_reducer_deterministic(self):
        """EV5: same case + state → same reducer decision across runs."""
        state = _make_state()
        case = _make_case(_make_passing_receipt())
        packet = assemble_promotion_packet(case, state)
        r1 = reduce_promotion_packet(packet, state)
        r2 = reduce_promotion_packet(packet, state)
        assert r1.decision == r2.decision
        assert r1.reason_code == r2.reason_code

    def test_ev6_state_unchanged_before_admitted(self):
        """EV6: state must NOT change until apply_skill_promotion_decision is called."""
        state = _make_state()
        state_hash_before = sha256_prefixed(state)
        case = _make_case(_make_passing_receipt())
        packet = assemble_promotion_packet(case, state)
        reduce_promotion_packet(packet, state)   # run reducer — must not mutate
        assert sha256_prefixed(state) == state_hash_before


# ── Full pipeline: state + ledger + replay ────────────────────────────────────

class TestFullPipeline:
    """EV7 + L1/L2/L4: Admitted → state update + ledger append + replay."""

    def test_admitted_adds_skill_to_state(self):
        """L1: ADMITTED decision → skill appears in active_skills."""
        state = _make_state()
        case = _make_case(_make_passing_receipt())
        packet = assemble_promotion_packet(case, state)
        result = reduce_promotion_packet(packet, state)
        assert result.decision == "ADMITTED"

        decision = _build_decision(packet, result)
        new_state = apply_skill_promotion_decision(state, decision)
        assert "skill.search" in new_state["active_skills"]
        assert new_state["active_skills"]["skill.search"]["active_version"] == "2.0.0"

    def test_original_state_immutable(self):
        """L1: original state dict unchanged after apply."""
        state = _make_state()
        state_before = copy.deepcopy(state)
        case = _make_case(_make_passing_receipt())
        packet = assemble_promotion_packet(case, state)
        result = reduce_promotion_packet(packet, state)
        decision = _build_decision(packet, result)
        apply_skill_promotion_decision(state, decision)
        assert state == state_before

    def test_fail_receipt_does_not_mutate_state(self):
        """L1: REJECTED decision must not alter state."""
        state = _make_state()
        state_hash_before = sha256_prefixed(state)
        case = _make_case(_make_failing_receipt())
        packet = assemble_promotion_packet(case, state)
        result = reduce_promotion_packet(packet, state)
        assert result.decision == "REJECTED"
        # REJECTED decisions must not be applied
        assert sha256_prefixed(state) == state_hash_before

    def test_ledger_receives_one_entry(self):
        """L2: ADMITTED decision appended; ledger grows by exactly 1."""
        state = _make_state()
        ledger = make_empty_ledger("eval_ledger_001")
        case = _make_case(_make_passing_receipt())
        packet = assemble_promotion_packet(case, state)
        result = reduce_promotion_packet(packet, state)
        decision = _build_decision(packet, result)
        new_ledger = append_decision_to_ledger(ledger, decision)
        assert len(new_ledger["entries"]) == 1
        assert new_ledger["entries"][0]["entry_index"] == 0
        assert new_ledger["entries"][0]["prev_entry_hash"] is None

    def test_replay_reconstructs_final_state(self):
        """L4: initial_state + ledger → replay → final_state (load-bearing)."""
        state = _make_state()
        ledger = make_empty_ledger("eval_ledger_001")
        case = _make_case(_make_passing_receipt())
        packet = assemble_promotion_packet(case, state)
        result = reduce_promotion_packet(packet, state)
        decision = _build_decision(packet, result)

        new_state  = apply_skill_promotion_decision(state, decision)
        new_ledger = append_decision_to_ledger(ledger, decision)

        replayed = replay_ledger_to_state(new_ledger, state)
        assert sha256_prefixed(replayed) == sha256_prefixed(new_state)

    def test_ev7_full_pipeline_deterministic(self):
        """EV7: same experiment inputs → same final state hash + ledger hash."""
        def _run() -> tuple[str, str]:
            st = _make_state()
            lg = make_empty_ledger("eval_ledger_001")
            receipt = _make_passing_receipt()
            case = _make_case(receipt)
            packet = assemble_promotion_packet(case, st)
            res = reduce_promotion_packet(packet, st)
            dec = _build_decision(packet, res)
            new_st = apply_skill_promotion_decision(st, dec)
            new_lg = append_decision_to_ledger(lg, dec)
            return sha256_prefixed(new_st), sha256_prefixed(new_lg)

        h1 = _run()
        h2 = _run()
        assert h1 == h2   # zero drift across two full pipeline runs
