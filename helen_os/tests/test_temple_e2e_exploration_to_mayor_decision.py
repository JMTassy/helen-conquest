"""E2E test: TEMPLE_EXPLORATION_V1 → TEMPLE_TRANSMUTATION_REQUEST_V1
           → SKILL_PROMOTION_PACKET_V1 → reducer → SKILL_PROMOTION_DECISION_V1
           → state update → ledger append → replay verification.

This test closes the live bridge seam: proves the full pipeline from
non-sovereign TEMPLE exploration to governed ledger entry is mechanically
consistent, deterministic, and schema-correct.

Laws verified:
  L1 (Membrane):  Only reducer-emitted decisions may mutate governed state.
  L2 (Ledger):    Only reducer-emitted decisions extend governed history.
  L4 (Replay):    replay_ledger_to_state(ledger, initial) == final_state.

TEMPLE law verified:
  authority=NONE throughout phases 1 and 2.
  No state mutation before reducer ADMITTED.
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
from helen_os.temple.temple_v1 import run_temple_exploration


# ── Fixtures ────────────────────────────────────────────────────────────────

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


def _receipt(rid: str, payload: dict) -> dict:
    hashable = {"receipt_id": rid, "payload": payload}
    return {"receipt_id": rid, "payload": payload, "sha256": sha256_prefixed(hashable)}


# ── Phase 1: TEMPLE exploration ──────────────────────────────────────────────

def _build_temple_exploration() -> dict:
    return run_temple_exploration(
        session_id="e2e_temple_001",
        theme="WEAVER capability gap — E2E bridge test",
        her_threads=[{
            "id": "HT-01",
            "voice": "HER",
            "content": "skill.weaver is missing: no typed skill bridges TEMPLE exports to governance.",
        }],
        hal_frictions=[{
            "id": "HF-01",
            "voice": "HAL",
            "friction": "PASS. Gap is real and bounded. Export candidate is bridge-eligible.",
        }],
        tension_map=[{
            "id": "T-01",
            "pole_a": "FREE_EXPRESSION",
            "pole_b": "INSTITUTIONAL_LEGIBILITY",
            "description": "Weaver sits at the intersection.",
        }],
        center_sketches=[{
            "id": "CS-01",
            "label": "THE_LOOM",
            "sketch": "What can be woven becomes cloth. The rest is retained.",
        }],
        export_candidates=[{
            "id": "EC-01",
            "label": "WEAVER_SKILL",
            "description": "skill.weaver v1.0.0 — TEMPLE→governance translation layer",
            "bridge_eligible": True,
            "hal_verdict": "PASS",
        }],
    )


# ── Phase 2: Transmutation request ──────────────────────────────────────────

def _build_transmutation_request(exploration: dict) -> dict:
    source_hash = sha256_prefixed(exploration)
    return {
        "schema_name":          "TEMPLE_TRANSMUTATION_REQUEST_V1",
        "schema_version":       "1.0.0",
        "request_id":           "transmute_e2e_001",
        "source_session_id":    exploration["session_id"],
        "source_artifact_hash": source_hash,
        "export_candidate_id":  "EC-01",
        "export_hal_verdict":   "PASS",
        "proposed_skill_id":    "skill.weaver",
        "proposed_version":     "1.0.0",
        "parent_skill_id":      "skill.discovery",
        "capability_description": "Translation layer from TEMPLE exports to governed proposals.",
        "transmutation_status": "PENDING",
        "authority":            "NONE",
    }


# ── Phase 3: Mayor promotion packet ─────────────────────────────────────────

def _build_promotion_packet(transmutation: dict, state: dict) -> dict:
    # Mayor receipt: TEMPLE provenance
    r1 = _receipt("receipt_temple_e2e_001", {
        "source_artifact_hash": transmutation["source_artifact_hash"],
        "export_candidate_id":  transmutation["export_candidate_id"],
        "hal_verdict":          transmutation["export_hal_verdict"],
    })
    # Mayor receipt: transmutation request itself
    r2 = _receipt("receipt_transmutation_e2e_001", {
        "request_id":   transmutation["request_id"],
        "request_hash": sha256_prefixed(transmutation),
        "status":       transmutation["transmutation_status"],
    })
    capability_manifest = {
        "skill_name":    "skill.weaver",
        "version":       "1.0.0",
        "source":        "TEMPLE_TRANSMUTATION_REQUEST_V1",
        "authority":     "NONE",
    }
    return {
        "schema_name":    "SKILL_PROMOTION_PACKET_V1",
        "schema_version": "1.0.0",
        "packet_id":      "promotion_e2e_001",
        "skill_id":       transmutation["proposed_skill_id"],
        "candidate_version": transmutation["proposed_version"],
        "lineage": {
            "parent_skill_id":  transmutation["parent_skill_id"],
            "parent_version":   "1.0.0",
            "proposal_sha256":  sha256_prefixed(transmutation),
        },
        "capability_manifest_sha256": sha256_prefixed(capability_manifest),
        "doctrine_surface": {
            "law_surface_version": state["law_surface_version"],
            "transfer_required":   False,
        },
        "evaluation": {
            "threshold_name":  "E2E_TEST_THRESHOLD",
            "threshold_value": 0.70,
            "observed_value":  0.85,
            "passed":          True,
        },
        "receipts": [r1, r2],
    }


# ── Decision builder ─────────────────────────────────────────────────────────

def _build_decision(packet: dict, result: object) -> dict:
    return {
        "schema_name":    "SKILL_PROMOTION_DECISION_V1",
        "schema_version": "1.0.0",
        "decision_id":    f"dec_{packet['skill_id'].replace('.', '_')}_e2e_001",
        "skill_id":       packet["skill_id"],
        "candidate_version": packet["candidate_version"],
        "decision_type":  result.decision,
        "reason_code":    result.reason_code,
    }


# ── Tests ────────────────────────────────────────────────────────────────────

class TestPhase1TempleNonSovereign:
    """Phase 1: TEMPLE exploration produces a non-sovereign artifact."""

    def test_temple_exploration_authority_is_none(self):
        exp = _build_temple_exploration()
        assert exp["authority"] == "NONE"

    def test_temple_exploration_no_state_field(self):
        exp = _build_temple_exploration()
        assert "state" not in exp
        assert "decision" not in exp
        assert "receipt" not in exp

    def test_temple_exploration_is_deterministic(self):
        e1 = _build_temple_exploration()
        e2 = _build_temple_exploration()
        assert sha256_prefixed(e1) == sha256_prefixed(e2)

    def test_temple_export_candidate_has_hal_pass(self):
        exp = _build_temple_exploration()
        ec = next(c for c in exp["export_candidates"] if c["id"] == "EC-01")
        assert ec["hal_verdict"] == "PASS"
        assert ec["bridge_eligible"] is True


class TestPhase2TransmutationRequest:
    """Phase 2: transmutation request carries provenance, authority=NONE."""

    def test_transmutation_authority_is_none(self):
        exp = _build_temple_exploration()
        req = _build_transmutation_request(exp)
        assert req["authority"] == "NONE"
        assert req["schema_name"] == "TEMPLE_TRANSMUTATION_REQUEST_V1"

    def test_transmutation_carries_source_hash(self):
        exp = _build_temple_exploration()
        req = _build_transmutation_request(exp)
        assert req["source_artifact_hash"] == sha256_prefixed(exp)
        assert req["source_artifact_hash"].startswith("sha256:")

    def test_transmutation_status_pending(self):
        exp = _build_temple_exploration()
        req = _build_transmutation_request(exp)
        assert req["transmutation_status"] == "PENDING"

    def test_transmutation_is_deterministic(self):
        exp = _build_temple_exploration()
        r1 = _build_transmutation_request(exp)
        r2 = _build_transmutation_request(exp)
        assert sha256_prefixed(r1) == sha256_prefixed(r2)


class TestPhase3ReducerDecision:
    """Phase 3: Mayor packet through 6 reducer gates → ADMITTED."""

    def test_reducer_admits_valid_packet(self):
        state = _make_state()
        exp = _build_temple_exploration()
        req = _build_transmutation_request(exp)
        pkt = _build_promotion_packet(req, state)
        result = reduce_promotion_packet(pkt, state)
        assert result.decision == "ADMITTED"
        assert result.reason_code == "OK_ADMITTED"

    def test_reducer_deterministic_across_runs(self):
        state = _make_state()
        exp = _build_temple_exploration()
        req = _build_transmutation_request(exp)
        pkt = _build_promotion_packet(req, state)
        r1 = reduce_promotion_packet(pkt, state)
        r2 = reduce_promotion_packet(pkt, state)
        assert r1.decision == r2.decision
        assert r1.reason_code == r2.reason_code

    def test_state_unchanged_before_admitted_decision(self):
        """State must NOT change until apply_skill_promotion_decision is called."""
        state = _make_state()
        exp = _build_temple_exploration()
        req = _build_transmutation_request(exp)
        pkt = _build_promotion_packet(req, state)
        state_hash_before = sha256_prefixed(state)
        reduce_promotion_packet(pkt, state)   # run reducer — must not mutate
        assert sha256_prefixed(state) == state_hash_before


class TestPhase4StateMutationAndLedger:
    """Phase 4: ADMITTED → state update + ledger append + replay."""

    def test_admitted_decision_adds_skill_to_state(self):
        state = _make_state()
        exp = _build_temple_exploration()
        req = _build_transmutation_request(exp)
        pkt = _build_promotion_packet(req, state)
        result = reduce_promotion_packet(pkt, state)
        assert result.decision == "ADMITTED"

        decision = _build_decision(pkt, result)
        new_state = apply_skill_promotion_decision(state, decision)
        assert "skill.weaver" in new_state["active_skills"]
        assert new_state["active_skills"]["skill.weaver"]["active_version"] == "1.0.0"

    def test_original_state_unchanged_after_apply(self):
        state = _make_state()
        state_before = copy.deepcopy(state)
        exp = _build_temple_exploration()
        req = _build_transmutation_request(exp)
        pkt = _build_promotion_packet(req, state)
        result = reduce_promotion_packet(pkt, state)
        decision = _build_decision(pkt, result)
        apply_skill_promotion_decision(state, decision)
        assert state == state_before   # original is immutable

    def test_ledger_receives_one_entry(self):
        state = _make_state()
        ledger = make_empty_ledger("e2e_ledger_001")
        exp = _build_temple_exploration()
        req = _build_transmutation_request(exp)
        pkt = _build_promotion_packet(req, state)
        result = reduce_promotion_packet(pkt, state)
        decision = _build_decision(pkt, result)
        new_ledger = append_decision_to_ledger(ledger, decision)
        assert len(new_ledger["entries"]) == 1
        assert new_ledger["entries"][0]["entry_index"] == 0
        assert new_ledger["entries"][0]["prev_entry_hash"] is None

    def test_replay_reconstructs_final_state(self):
        """Load-bearing property: initial_state + ledger → replay → final_state."""
        state = _make_state()
        ledger = make_empty_ledger("e2e_ledger_001")
        exp = _build_temple_exploration()
        req = _build_transmutation_request(exp)
        pkt = _build_promotion_packet(req, state)
        result = reduce_promotion_packet(pkt, state)
        decision = _build_decision(pkt, result)

        new_state  = apply_skill_promotion_decision(state, decision)
        new_ledger = append_decision_to_ledger(ledger, decision)

        replayed = replay_ledger_to_state(new_ledger, state)
        assert sha256_prefixed(replayed) == sha256_prefixed(new_state)

    def test_full_pipeline_deterministic(self):
        """Same TEMPLE session → same final state hash, same ledger hash."""
        def _run() -> tuple[str, str]:
            st = _make_state()
            lg = make_empty_ledger("e2e_ledger_001")
            exp = _build_temple_exploration()
            req = _build_transmutation_request(exp)
            pkt = _build_promotion_packet(req, st)
            res = reduce_promotion_packet(pkt, st)
            dec = _build_decision(pkt, res)
            new_st = apply_skill_promotion_decision(st, dec)
            new_lg = append_decision_to_ledger(lg, dec)
            return sha256_prefixed(new_st), sha256_prefixed(new_lg)

        h1 = _run()
        h2 = _run()
        assert h1 == h2   # zero drift across two full pipeline runs
