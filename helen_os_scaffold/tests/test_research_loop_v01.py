"""
tests/test_research_loop_v01.py — HELEN Research Loop v0.1 tests.

Verifies the frozen MVP spec (research_loop/MVP_SPEC_V0_1.md).

Test groups:
    RL01  Artifact construction (MissionV1, ProposalV1, etc.)
    RL02  Manifest hash determinism (same inputs → same hash)
    RL03  verify_manifest() integrity gate
    RL04  Verdict reducer — gate semantics
    RL05  Verdict reducer — state evolution
    RL06  Manifest validation errors
    RL07  Ledger append_ship — happy path
    RL08  Ledger append_ship — chain enforcement
    RL09  Ledger append_ship — integrity enforcement
    RL10  Ledger append_ship — verdict enforcement
    RL11  Ledger append_audit — NO_SHIP and QUARANTINE
    RL12  Ledger replay — verify_chain()
    RL13  Ledger load_admitted_state()
    RL14  Genesis manifest via make_genesis_manifest()
    RL15  Metric gate — improvement threshold
    RL16  Memory law — only SHIP feeds optimization state
    RL17  Canonical JSON determinism
"""
from __future__ import annotations

import os
import sys
import tempfile
import json
from pathlib import Path

import pytest

_SCAFFOLD_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _SCAFFOLD_ROOT not in sys.path:
    sys.path.insert(0, os.path.abspath(_SCAFFOLD_ROOT))

from research_loop import (
    MANIFEST_VERSION,
    GENESIS_PARENT_HASH,
    IMPROVEMENT_THRESHOLD,
    MissionV1,
    ProposalV1,
    ExecutionReceiptV1,
    EvidenceBundleV1,
    IssueItemV1,
    IssueListV1,
    GateVectorV1,
    VerdictV1,
    RunManifestV1,
    ManifestValidationError,
    build_run_manifest,
    verify_manifest,
    manifest_to_dict,
    canonical_json,
    sha256_hex,
    compute_verdict,
    compute_metric_gate,
    reduce_run,
    ManifestLedger,
    make_genesis_manifest,
    LedgerError,
    LedgerIntegrityError,
    LedgerChainError,
    LedgerVerdictError,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

_MISSION = MissionV1(
    mission_id="MIS_001",
    domain="retrieval_ranking",
    objective="Maximize top-1 accuracy on frozen benchmark.",
    metric_name="top1_accuracy",
    maximize=True,
)
_PROPOSAL = ProposalV1(
    proposal_id="PROP_001",
    proposer="HER",
    summary="Use BM25 with tuned k1 and b parameters.",
    hypothesis="Tuning BM25 parameters improves top-1 accuracy.",
    mutable_files=["ranker.py"],
    replay_command="python eval.py --seed 42 --dataset frozen_eval.jsonl",
)
_RECEIPT = ExecutionReceiptV1(
    receipt_id="RCP_001",
    kind="metric",
    command="python eval.py --seed 42 --dataset frozen_eval.jsonl",
    stdout_sha256="a" * 64,
    stderr_sha256="b" * 64,
    artifact_refs=["metric:top1_accuracy=0.847"],
)
_EVIDENCE = EvidenceBundleV1(
    evidence_id="EV_001",
    dataset_hash="c" * 64,
    metric_name="top1_accuracy",
    metric_value=0.847,
    receipt_ids=["RCP_001"],
)
_ISSUES_EMPTY = IssueListV1(issue_list_id="ISSUES_001", issues=[])
_GATES_ALL_TRUE = GateVectorV1(
    G_receipts_present=True,
    G_replay_ok=True,
    G_metric_improved=True,
    G_no_blocking_issue=True,
    G_kernel_integrity_ok=True,
)
_PARENT              = GENESIS_PARENT_HASH
_CONFIG              = "d" * 64
_ENV                 = "e" * 64
_MODEL               = "f" * 64
_EVAL_OUT_HASH       = "9" * 64
_LAW_SURFACE_VERSION = "LAW_SURFACE_V1"
_LAW_SURFACE_HASH    = "0" * 64   # sentinel — real hash bound at runtime
_TS                  = "2026-03-10T12:00:00Z"


def _build_ship_manifest(**kwargs) -> RunManifestV1:
    defaults = dict(
        manifest_id="MAN_001",
        ts_utc=_TS,
        mission=_MISSION,
        proposal=_PROPOSAL,
        receipts=[_RECEIPT],
        evidence=_EVIDENCE,
        issues=_ISSUES_EMPTY,
        gates=_GATES_ALL_TRUE,
        parent_manifest_hash=_PARENT,
        config_hash=_CONFIG,
        environment_hash=_ENV,
        model_digest=_MODEL,
        eval_output_hash=_EVAL_OUT_HASH,
        law_surface_version=_LAW_SURFACE_VERSION,
        law_surface_hash=_LAW_SURFACE_HASH,
    )
    defaults.update(kwargs)
    return build_run_manifest(**defaults)


@pytest.fixture
def tmp_ledger(tmp_path):
    return ManifestLedger(
        ledger_path=tmp_path / "ledger.ndjson",
        audit_path=tmp_path / "audit.ndjson",
    )


# ── RL01: Artifact construction ────────────────────────────────────────────────

class TestArtifactConstruction:
    def test_rl01_mission_creation(self):
        assert _MISSION.mission_id == "MIS_001"
        assert _MISSION.domain == "retrieval_ranking"
        assert _MISSION.metric_name == "top1_accuracy"
        assert _MISSION.maximize is True

    def test_rl01_proposal_creation(self):
        assert _PROPOSAL.proposer == "HER"
        assert _PROPOSAL.mutable_files == ["ranker.py"]
        assert _PROPOSAL.replay_command

    def test_rl01_receipt_creation(self):
        assert _RECEIPT.kind == "metric"
        assert _RECEIPT.stdout_sha256 == "a" * 64

    def test_rl01_issue_list_no_blocker(self):
        assert not _ISSUES_EMPTY.has_blocker()

    def test_rl01_issue_list_with_blocker(self):
        blocker_list = IssueListV1(
            issue_list_id="ISS",
            issues=[IssueItemV1("I1", "blocker", "TIMEOUT", "Timed out")],
        )
        assert blocker_list.has_blocker()

    def test_rl01_gate_vector_all_true(self):
        assert all([
            _GATES_ALL_TRUE.G_receipts_present,
            _GATES_ALL_TRUE.G_replay_ok,
            _GATES_ALL_TRUE.G_metric_improved,
            _GATES_ALL_TRUE.G_no_blocking_issue,
            _GATES_ALL_TRUE.G_kernel_integrity_ok,
        ])

    def test_rl01_manifest_version_constant(self):
        assert MANIFEST_VERSION == "RUN_MANIFEST_V1"

    def test_rl01_genesis_parent_hash_is_zeros(self):
        assert GENESIS_PARENT_HASH == "0" * 64

    def test_rl01_improvement_threshold(self):
        assert IMPROVEMENT_THRESHOLD == 0.002


# ── RL02: Manifest hash determinism ───────────────────────────────────────────

class TestManifestHashDeterminism:
    def test_rl02_same_inputs_same_hash(self):
        m1 = _build_ship_manifest()
        m2 = _build_ship_manifest()
        assert m1.manifest_hash == m2.manifest_hash

    def test_rl02_same_inputs_same_manifest_id(self):
        m1 = _build_ship_manifest()
        m2 = _build_ship_manifest()
        assert m1.manifest_id == m2.manifest_id

    def test_rl02_different_proposal_different_hash(self):
        prop2 = ProposalV1(
            proposal_id="PROP_002",
            proposer="HER",
            summary="Different approach.",
            hypothesis="Different hypothesis.",
            mutable_files=["ranker.py"],
            replay_command="python eval.py --seed 99",
        )
        m1 = _build_ship_manifest()
        m2 = _build_ship_manifest(proposal=prop2)
        assert m1.manifest_hash != m2.manifest_hash

    def test_rl02_different_metric_different_hash(self):
        ev2 = EvidenceBundleV1(
            evidence_id="EV_001",
            dataset_hash="c" * 64,
            metric_name="top1_accuracy",
            metric_value=0.900,
            receipt_ids=["RCP_001"],
        )
        m1 = _build_ship_manifest()
        m2 = _build_ship_manifest(evidence=ev2)
        assert m1.manifest_hash != m2.manifest_hash

    def test_rl02_different_parent_different_hash(self):
        m1 = _build_ship_manifest(parent_manifest_hash="0" * 64)
        m2 = _build_ship_manifest(parent_manifest_hash="a" * 64)
        assert m1.manifest_hash != m2.manifest_hash

    def test_rl02_manifest_version_is_pinned(self):
        m = _build_ship_manifest()
        assert m.manifest_version == MANIFEST_VERSION


# ── RL03: verify_manifest() ───────────────────────────────────────────────────

class TestVerifyManifest:
    def test_rl03_valid_manifest_verifies(self):
        m = _build_ship_manifest()
        assert verify_manifest(m) is True

    def test_rl03_tampered_metric_fails(self):
        m = _build_ship_manifest()
        # Manually tamper with evidence (frozen dataclass, so rebuild)
        ev_tampered = EvidenceBundleV1(
            evidence_id=m.evidence.evidence_id,
            dataset_hash=m.evidence.dataset_hash,
            metric_name=m.evidence.metric_name,
            metric_value=99.0,     # tampered
            receipt_ids=list(m.evidence.receipt_ids),
        )
        tampered = RunManifestV1(
            manifest_version=m.manifest_version,
            manifest_id=m.manifest_id,
            ts_utc=m.ts_utc,
            mission=m.mission,
            proposal=m.proposal,
            receipts=m.receipts,
            evidence=ev_tampered,   # tampered
            issues=m.issues,
            gates=m.gates,
            verdict=m.verdict,
            parent_manifest_hash=m.parent_manifest_hash,
            config_hash=m.config_hash,
            environment_hash=m.environment_hash,
            model_digest=m.model_digest,
            eval_output_hash=m.eval_output_hash,
            law_surface_version=m.law_surface_version,
            law_surface_hash=m.law_surface_hash,
            manifest_hash=m.manifest_hash,   # old hash (now stale)
        )
        assert verify_manifest(tampered) is False

    def test_rl03_tampered_hash_fails(self):
        m = _build_ship_manifest()
        # Manually set a wrong manifest_hash
        wrong = RunManifestV1(
            manifest_version=m.manifest_version,
            manifest_id=m.manifest_id,
            ts_utc=m.ts_utc,
            mission=m.mission,
            proposal=m.proposal,
            receipts=m.receipts,
            evidence=m.evidence,
            issues=m.issues,
            gates=m.gates,
            verdict=m.verdict,
            parent_manifest_hash=m.parent_manifest_hash,
            config_hash=m.config_hash,
            environment_hash=m.environment_hash,
            model_digest=m.model_digest,
            eval_output_hash=m.eval_output_hash,
            law_surface_version=m.law_surface_version,
            law_surface_hash=m.law_surface_hash,
            manifest_hash="deadbeef" * 8,
        )
        assert verify_manifest(wrong) is False


# ── RL04: Verdict reducer — gate semantics ─────────────────────────────────────

class TestVerdictReducerGates:
    def _gates(self, **overrides) -> GateVectorV1:
        d = dict(
            G_receipts_present=True, G_replay_ok=True, G_metric_improved=True,
            G_no_blocking_issue=True, G_kernel_integrity_ok=True,
        )
        d.update(overrides)
        return GateVectorV1(**d)

    def test_rl04_all_true_is_ship(self):
        v = compute_verdict(self._gates())
        assert v.verdict == "SHIP"
        assert v.blocking_reason_codes == []

    def test_rl04_integrity_fail_is_quarantine(self):
        v = compute_verdict(self._gates(G_kernel_integrity_ok=False))
        assert v.verdict == "QUARANTINE"
        assert "KERNEL_INTEGRITY_FAILED" in v.blocking_reason_codes

    def test_rl04_integrity_fail_overrides_everything(self):
        # Even if all other gates are True, integrity failure → QUARANTINE
        v = compute_verdict(self._gates(
            G_kernel_integrity_ok=False,
            G_receipts_present=True,
            G_replay_ok=True,
        ))
        assert v.verdict == "QUARANTINE"

    def test_rl04_missing_receipts_is_no_ship(self):
        v = compute_verdict(self._gates(G_receipts_present=False))
        assert v.verdict == "NO_SHIP"
        assert "MISSING_RECEIPTS" in v.blocking_reason_codes

    def test_rl04_replay_fail_is_no_ship(self):
        v = compute_verdict(self._gates(G_replay_ok=False))
        assert v.verdict == "NO_SHIP"
        assert "REPLAY_FAILED" in v.blocking_reason_codes

    def test_rl04_blocking_issue_is_no_ship(self):
        v = compute_verdict(self._gates(G_no_blocking_issue=False))
        assert v.verdict == "NO_SHIP"
        assert "BLOCKING_ISSUE" in v.blocking_reason_codes

    def test_rl04_metric_not_improved_is_no_ship(self):
        v = compute_verdict(self._gates(G_metric_improved=False))
        assert v.verdict == "NO_SHIP"
        assert "METRIC_NOT_IMPROVED" in v.blocking_reason_codes

    def test_rl04_multiple_failures_accumulate(self):
        v = compute_verdict(self._gates(
            G_receipts_present=False, G_replay_ok=False,
        ))
        assert v.verdict == "NO_SHIP"
        assert "MISSING_RECEIPTS" in v.blocking_reason_codes
        assert "REPLAY_FAILED" in v.blocking_reason_codes

    def test_rl04_ship_has_no_blocking_codes(self):
        v = compute_verdict(self._gates())
        assert v.blocking_reason_codes == []


# ── RL05: Reducer state evolution ─────────────────────────────────────────────

class TestReducerStateEvolution:
    def test_rl05_ship_updates_state(self):
        m = _build_ship_manifest()
        state = {"best_metric": 0.8, "shipped_run_lineage": []}
        verdict, new_state = reduce_run(state, m, _GATES_ALL_TRUE)
        assert verdict == "SHIP"
        assert new_state["best_metric"] == 0.847
        assert m.manifest_hash in new_state["shipped_run_lineage"]

    def test_rl05_no_ship_does_not_update_state(self):
        m = _build_ship_manifest()
        gates_fail = GateVectorV1(
            G_receipts_present=False, G_replay_ok=True,
            G_metric_improved=True, G_no_blocking_issue=True,
            G_kernel_integrity_ok=True,
        )
        state = {"best_metric": 0.8, "shipped_run_lineage": []}
        verdict, new_state = reduce_run(state, m, gates_fail)
        assert verdict == "NO_SHIP"
        assert new_state["best_metric"] == 0.8   # unchanged

    def test_rl05_quarantine_does_not_update_state(self):
        m = _build_ship_manifest()
        gates_fail = GateVectorV1(
            G_receipts_present=True, G_replay_ok=True,
            G_metric_improved=True, G_no_blocking_issue=True,
            G_kernel_integrity_ok=False,
        )
        state = {"best_metric": 0.8, "shipped_run_lineage": []}
        verdict, new_state = reduce_run(state, m, gates_fail)
        assert verdict == "QUARANTINE"
        assert new_state is state   # same object


# ── RL06: Manifest validation errors ──────────────────────────────────────────

class TestManifestValidationErrors:
    def test_rl06_ship_with_blocking_codes_raises(self):
        with pytest.raises(ManifestValidationError, match="zero blocking"):
            build_run_manifest(
                manifest_id="MAN_ERR",
                ts_utc=_TS,
                mission=_MISSION,
                proposal=_PROPOSAL,
                receipts=[_RECEIPT],
                evidence=_EVIDENCE,
                issues=_ISSUES_EMPTY,
                gates=_GATES_ALL_TRUE,
                parent_manifest_hash=_PARENT,
                config_hash=_CONFIG,
                environment_hash=_ENV,
                model_digest=_MODEL,
                eval_output_hash=_EVAL_OUT_HASH,
                law_surface_version=_LAW_SURFACE_VERSION,
                law_surface_hash=_LAW_SURFACE_HASH,
                verdict=VerdictV1("SHIP", ["MISSING_RECEIPTS"]),
            )

    def test_rl06_no_ship_without_codes_raises(self):
        with pytest.raises(ManifestValidationError, match="at least one"):
            build_run_manifest(
                manifest_id="MAN_ERR",
                ts_utc=_TS,
                mission=_MISSION,
                proposal=_PROPOSAL,
                receipts=[_RECEIPT],
                evidence=_EVIDENCE,
                issues=_ISSUES_EMPTY,
                gates=GateVectorV1(False, True, True, True, True),
                parent_manifest_hash=_PARENT,
                config_hash=_CONFIG,
                environment_hash=_ENV,
                model_digest=_MODEL,
                eval_output_hash=_EVAL_OUT_HASH,
                law_surface_version=_LAW_SURFACE_VERSION,
                law_surface_hash=_LAW_SURFACE_HASH,
                verdict=VerdictV1("NO_SHIP", []),   # empty codes
            )

    def test_rl06_evidence_references_missing_receipt(self):
        ev_bad = EvidenceBundleV1(
            evidence_id="EV_BAD",
            dataset_hash="c" * 64,
            metric_name="top1_accuracy",
            metric_value=0.847,
            receipt_ids=["RCP_MISSING"],  # not in receipts
        )
        with pytest.raises(ManifestValidationError, match="missing receipt"):
            build_run_manifest(
                manifest_id="MAN_ERR",
                ts_utc=_TS,
                mission=_MISSION,
                proposal=_PROPOSAL,
                receipts=[_RECEIPT],
                evidence=ev_bad,
                issues=_ISSUES_EMPTY,
                gates=_GATES_ALL_TRUE,
                parent_manifest_hash=_PARENT,
                config_hash=_CONFIG,
                environment_hash=_ENV,
                model_digest=_MODEL,
                eval_output_hash=_EVAL_OUT_HASH,
                law_surface_version=_LAW_SURFACE_VERSION,
                law_surface_hash=_LAW_SURFACE_HASH,
            )

    def test_rl06_blocker_issue_gate_mismatch_raises(self):
        issues_with_blocker = IssueListV1(
            issue_list_id="ISS_B",
            issues=[IssueItemV1("I1", "blocker", "TIMEOUT", "Timed out")]
        )
        with pytest.raises(ManifestValidationError, match="Gate mismatch"):
            build_run_manifest(
                manifest_id="MAN_ERR",
                ts_utc=_TS,
                mission=_MISSION,
                proposal=_PROPOSAL,
                receipts=[_RECEIPT],
                evidence=_EVIDENCE,
                issues=issues_with_blocker,
                gates=_GATES_ALL_TRUE,  # G_no_blocking_issue=True, but there's a blocker
                parent_manifest_hash=_PARENT,
                config_hash=_CONFIG,
                environment_hash=_ENV,
                model_digest=_MODEL,
                eval_output_hash=_EVAL_OUT_HASH,
                law_surface_version=_LAW_SURFACE_VERSION,
                law_surface_hash=_LAW_SURFACE_HASH,
            )

    def test_rl06_empty_receipts_raises(self):
        with pytest.raises(ManifestValidationError, match="At least one"):
            build_run_manifest(
                manifest_id="MAN_ERR",
                ts_utc=_TS,
                mission=_MISSION,
                proposal=_PROPOSAL,
                receipts=[],
                evidence=_EVIDENCE,
                issues=_ISSUES_EMPTY,
                gates=_GATES_ALL_TRUE,
                parent_manifest_hash=_PARENT,
                config_hash=_CONFIG,
                environment_hash=_ENV,
                model_digest=_MODEL,
                eval_output_hash=_EVAL_OUT_HASH,
                law_surface_version=_LAW_SURFACE_VERSION,
                law_surface_hash=_LAW_SURFACE_HASH,
            )


# ── RL07: Ledger append_ship — happy path ─────────────────────────────────────

class TestLedgerAppendShip:
    def test_rl07_empty_ledger_ship_count_zero(self, tmp_ledger):
        assert tmp_ledger.ship_count() == 0

    def test_rl07_after_append_ship_count_one(self, tmp_ledger):
        m = _build_ship_manifest()
        tmp_ledger.append_ship(m)
        assert tmp_ledger.ship_count() == 1

    def test_rl07_tail_hash_after_append(self, tmp_ledger):
        m = _build_ship_manifest()
        tmp_ledger.append_ship(m)
        assert tmp_ledger.tail_hash() == m.manifest_hash

    def test_rl07_empty_ledger_tail_is_genesis(self, tmp_ledger):
        assert tmp_ledger.tail_hash() == GENESIS_PARENT_HASH

    def test_rl07_best_metric_after_append(self, tmp_ledger):
        m = _build_ship_manifest()
        tmp_ledger.append_ship(m)
        assert tmp_ledger.best_metric() == pytest.approx(0.847)

    def test_rl07_empty_ledger_best_metric_is_none(self, tmp_ledger):
        assert tmp_ledger.best_metric() is None

    def test_rl07_chained_append(self, tmp_ledger):
        m1 = _build_ship_manifest(manifest_id="MAN_001")
        tmp_ledger.append_ship(m1)

        ev2 = EvidenceBundleV1(
            evidence_id="EV_002",
            dataset_hash="c" * 64,
            metric_name="top1_accuracy",
            metric_value=0.870,
            receipt_ids=["RCP_001"],
        )
        m2 = _build_ship_manifest(
            manifest_id="MAN_002",
            evidence=ev2,
            parent_manifest_hash=m1.manifest_hash,
        )
        tmp_ledger.append_ship(m2)
        assert tmp_ledger.ship_count() == 2
        assert tmp_ledger.tail_hash() == m2.manifest_hash
        assert tmp_ledger.best_metric() == pytest.approx(0.870)

    def test_rl07_iter_ship_order(self, tmp_ledger):
        m1 = _build_ship_manifest(manifest_id="MAN_001")
        tmp_ledger.append_ship(m1)
        ev2 = EvidenceBundleV1("EV_002", "c" * 64, "top1_accuracy", 0.870, ["RCP_001"])
        m2 = _build_ship_manifest(manifest_id="MAN_002", evidence=ev2,
                                  parent_manifest_hash=m1.manifest_hash)
        tmp_ledger.append_ship(m2)
        ids = [r["manifest_id"] for r in tmp_ledger.iter_ship()]
        assert ids == ["MAN_001", "MAN_002"]


# ── RL08: Ledger chain enforcement ────────────────────────────────────────────

class TestLedgerChainEnforcement:
    def test_rl08_wrong_parent_raises(self, tmp_ledger):
        m1 = _build_ship_manifest(manifest_id="MAN_001")
        tmp_ledger.append_ship(m1)

        ev2 = EvidenceBundleV1("EV_002", "c" * 64, "top1_accuracy", 0.870, ["RCP_001"])
        m2 = _build_ship_manifest(
            manifest_id="MAN_002",
            evidence=ev2,
            parent_manifest_hash="wrong_parent_hash" + "0" * 46,
        )
        with pytest.raises(LedgerChainError):
            tmp_ledger.append_ship(m2)

    def test_rl08_first_manifest_must_have_genesis_parent(self, tmp_ledger):
        m = _build_ship_manifest(parent_manifest_hash="wrong_parent" + "0" * 52)
        with pytest.raises(LedgerChainError):
            tmp_ledger.append_ship(m)

    def test_rl08_genesis_parent_accepted_on_empty_ledger(self, tmp_ledger):
        m = _build_ship_manifest(parent_manifest_hash=GENESIS_PARENT_HASH)
        tmp_ledger.append_ship(m)  # must not raise
        assert tmp_ledger.ship_count() == 1


# ── RL09: Integrity enforcement ───────────────────────────────────────────────

class TestLedgerIntegrityEnforcement:
    def test_rl09_tampered_manifest_rejected(self, tmp_ledger):
        m = _build_ship_manifest()
        # Build a manifest with a wrong hash
        wrong = RunManifestV1(
            manifest_version=m.manifest_version,
            manifest_id=m.manifest_id,
            ts_utc=m.ts_utc,
            mission=m.mission,
            proposal=m.proposal,
            receipts=m.receipts,
            evidence=m.evidence,
            issues=m.issues,
            gates=m.gates,
            verdict=m.verdict,
            parent_manifest_hash=m.parent_manifest_hash,
            config_hash=m.config_hash,
            environment_hash=m.environment_hash,
            model_digest=m.model_digest,
            eval_output_hash=m.eval_output_hash,
            law_surface_version=m.law_surface_version,
            law_surface_hash=m.law_surface_hash,
            manifest_hash="deadbeef" * 8,
        )
        with pytest.raises(LedgerIntegrityError):
            tmp_ledger.append_ship(wrong)


# ── RL10: Verdict enforcement ─────────────────────────────────────────────────

class TestLedgerVerdictEnforcement:
    def test_rl10_no_ship_manifest_rejected_from_main_ledger(self, tmp_ledger):
        gates_fail = GateVectorV1(False, True, True, True, True)
        m = build_run_manifest(
            manifest_id="MAN_ERR",
            ts_utc=_TS,
            mission=_MISSION,
            proposal=_PROPOSAL,
            receipts=[_RECEIPT],
            evidence=_EVIDENCE,
            issues=_ISSUES_EMPTY,
            gates=gates_fail,
            parent_manifest_hash=_PARENT,
            config_hash=_CONFIG,
            environment_hash=_ENV,
            model_digest=_MODEL,
            eval_output_hash=_EVAL_OUT_HASH,
            law_surface_version=_LAW_SURFACE_VERSION,
            law_surface_hash=_LAW_SURFACE_HASH,
        )
        assert m.verdict.verdict == "NO_SHIP"
        with pytest.raises(LedgerVerdictError):
            tmp_ledger.append_ship(m)

    def test_rl10_quarantine_manifest_rejected_from_main_ledger(self, tmp_ledger):
        gates_q = GateVectorV1(True, True, True, True, False)
        m = build_run_manifest(
            manifest_id="MAN_ERR",
            ts_utc=_TS,
            mission=_MISSION,
            proposal=_PROPOSAL,
            receipts=[_RECEIPT],
            evidence=_EVIDENCE,
            issues=_ISSUES_EMPTY,
            gates=gates_q,
            parent_manifest_hash=_PARENT,
            config_hash=_CONFIG,
            environment_hash=_ENV,
            model_digest=_MODEL,
            eval_output_hash=_EVAL_OUT_HASH,
            law_surface_version=_LAW_SURFACE_VERSION,
            law_surface_hash=_LAW_SURFACE_HASH,
        )
        assert m.verdict.verdict == "QUARANTINE"
        with pytest.raises(LedgerVerdictError):
            tmp_ledger.append_ship(m)


# ── RL11: Audit trail ─────────────────────────────────────────────────────────

class TestAuditTrail:
    def test_rl11_no_ship_appended_to_audit(self, tmp_ledger):
        gates_fail = GateVectorV1(False, True, True, True, True)
        m = build_run_manifest(
            manifest_id="MAN_NS",
            ts_utc=_TS, mission=_MISSION, proposal=_PROPOSAL,
            receipts=[_RECEIPT], evidence=_EVIDENCE, issues=_ISSUES_EMPTY,
            gates=gates_fail, parent_manifest_hash=_PARENT,
            config_hash=_CONFIG, environment_hash=_ENV, model_digest=_MODEL,
            eval_output_hash=_EVAL_OUT_HASH,
            law_surface_version=_LAW_SURFACE_VERSION, law_surface_hash=_LAW_SURFACE_HASH,
        )
        tmp_ledger.append_audit(m)
        audit_records = list(tmp_ledger.iter_audit())
        assert len(audit_records) == 1
        assert audit_records[0]["verdict"]["verdict"] == "NO_SHIP"

    def test_rl11_no_ship_does_not_appear_in_main_ledger(self, tmp_ledger):
        gates_fail = GateVectorV1(False, True, True, True, True)
        m = build_run_manifest(
            manifest_id="MAN_NS",
            ts_utc=_TS, mission=_MISSION, proposal=_PROPOSAL,
            receipts=[_RECEIPT], evidence=_EVIDENCE, issues=_ISSUES_EMPTY,
            gates=gates_fail, parent_manifest_hash=_PARENT,
            config_hash=_CONFIG, environment_hash=_ENV, model_digest=_MODEL,
            eval_output_hash=_EVAL_OUT_HASH,
            law_surface_version=_LAW_SURFACE_VERSION, law_surface_hash=_LAW_SURFACE_HASH,
        )
        tmp_ledger.append_audit(m)
        assert tmp_ledger.ship_count() == 0


# ── RL12: verify_chain() ──────────────────────────────────────────────────────

class TestVerifyChain:
    def test_rl12_empty_ledger_chain_verifies(self, tmp_ledger):
        tmp_ledger.verify_chain()  # must not raise

    def test_rl12_single_entry_chain_verifies(self, tmp_ledger):
        m = _build_ship_manifest()
        tmp_ledger.append_ship(m)
        tmp_ledger.verify_chain()

    def test_rl12_two_entry_chain_verifies(self, tmp_ledger):
        m1 = _build_ship_manifest(manifest_id="MAN_001")
        tmp_ledger.append_ship(m1)
        ev2 = EvidenceBundleV1("EV_002", "c" * 64, "top1_accuracy", 0.870, ["RCP_001"])
        m2 = _build_ship_manifest(manifest_id="MAN_002", evidence=ev2,
                                  parent_manifest_hash=m1.manifest_hash)
        tmp_ledger.append_ship(m2)
        tmp_ledger.verify_chain()  # must not raise


# ── RL13: load_admitted_state() ───────────────────────────────────────────────

class TestLoadAdmittedState:
    def test_rl13_empty_ledger_state(self, tmp_ledger):
        state = tmp_ledger.load_admitted_state()
        assert state["best_metric"] is None
        assert state["best_manifest_hash"] is None
        assert state["shipped_run_lineage"] == []

    def test_rl13_after_one_ship_state_updated(self, tmp_ledger):
        m = _build_ship_manifest()
        tmp_ledger.append_ship(m)
        state = tmp_ledger.load_admitted_state()
        assert state["best_metric"] == pytest.approx(0.847)
        assert state["best_manifest_hash"] == m.manifest_hash
        assert len(state["shipped_run_lineage"]) == 1

    def test_rl13_best_metric_is_maximum_not_latest(self, tmp_ledger):
        m1 = _build_ship_manifest(manifest_id="MAN_001")
        tmp_ledger.append_ship(m1)
        ev2 = EvidenceBundleV1("EV_002", "c" * 64, "top1_accuracy", 0.900, ["RCP_001"])
        m2 = _build_ship_manifest(manifest_id="MAN_002", evidence=ev2,
                                  parent_manifest_hash=m1.manifest_hash)
        tmp_ledger.append_ship(m2)
        state = tmp_ledger.load_admitted_state()
        assert state["best_metric"] == pytest.approx(0.900)


# ── RL14: Genesis manifest ────────────────────────────────────────────────────

class TestGenesisManifest:
    def test_rl14_genesis_is_ship(self, tmp_ledger):
        g = make_genesis_manifest(
            ledger=tmp_ledger,
            mission=_MISSION,
            config_hash=_CONFIG,
            environment_hash=_ENV,
            model_digest=_MODEL,
            ts_utc=_TS,
            baseline_metric=0.800,
            dataset_hash="c" * 64,
            baseline_run_command="python eval.py --seed 42",
            baseline_stdout_sha256="a" * 64,
        )
        assert g.verdict.verdict == "SHIP"
        assert g.manifest_id == "MAN_GENESIS"

    def test_rl14_genesis_parent_is_zeros(self, tmp_ledger):
        g = make_genesis_manifest(
            ledger=tmp_ledger, mission=_MISSION, config_hash=_CONFIG,
            environment_hash=_ENV, model_digest=_MODEL, ts_utc=_TS,
            baseline_metric=0.800, dataset_hash="c" * 64,
            baseline_run_command="python eval.py --seed 42",
            baseline_stdout_sha256="a" * 64,
        )
        assert g.parent_manifest_hash == GENESIS_PARENT_HASH

    def test_rl14_genesis_appended_to_ledger(self, tmp_ledger):
        make_genesis_manifest(
            ledger=tmp_ledger, mission=_MISSION, config_hash=_CONFIG,
            environment_hash=_ENV, model_digest=_MODEL, ts_utc=_TS,
            baseline_metric=0.800, dataset_hash="c" * 64,
            baseline_run_command="python eval.py --seed 42",
            baseline_stdout_sha256="a" * 64,
        )
        assert tmp_ledger.ship_count() == 1

    def test_rl14_genesis_baseline_metric_stored(self, tmp_ledger):
        make_genesis_manifest(
            ledger=tmp_ledger, mission=_MISSION, config_hash=_CONFIG,
            environment_hash=_ENV, model_digest=_MODEL, ts_utc=_TS,
            baseline_metric=0.800, dataset_hash="c" * 64,
            baseline_run_command="python eval.py --seed 42",
            baseline_stdout_sha256="a" * 64,
        )
        assert tmp_ledger.best_metric() == pytest.approx(0.800)


# ── RL15: Metric gate ─────────────────────────────────────────────────────────

class TestMetricGate:
    def test_rl15_improvement_above_threshold(self):
        assert compute_metric_gate(0.852, 0.847) is True   # 0.852 >= 0.847 + 0.002

    def test_rl15_improvement_exactly_threshold(self):
        assert compute_metric_gate(0.849, 0.847) is True   # 0.849 >= 0.847 + 0.002

    def test_rl15_below_threshold_is_false(self):
        assert compute_metric_gate(0.848, 0.847) is False  # 0.848 < 0.847 + 0.002

    def test_rl15_equal_is_false(self):
        assert compute_metric_gate(0.847, 0.847) is False  # 0.847 < 0.847 + 0.002

    def test_rl15_regression_is_false(self):
        assert compute_metric_gate(0.800, 0.847) is False

    def test_rl15_custom_threshold(self):
        assert compute_metric_gate(0.851, 0.847, threshold=0.003) is True
        assert compute_metric_gate(0.849, 0.847, threshold=0.003) is False


# ── RL16: Memory law ──────────────────────────────────────────────────────────

class TestMemoryLaw:
    def test_rl16_shipped_lineage_grows_only_on_ship(self, tmp_ledger):
        m1 = _build_ship_manifest(manifest_id="MAN_001")
        tmp_ledger.append_ship(m1)
        state = tmp_ledger.load_admitted_state()
        lineage_before = list(state["shipped_run_lineage"])

        # Append a NO_SHIP to audit (not to main ledger)
        gates_fail = GateVectorV1(False, True, True, True, True)
        m_ns = build_run_manifest(
            manifest_id="MAN_NS",
            ts_utc=_TS, mission=_MISSION, proposal=_PROPOSAL,
            receipts=[_RECEIPT], evidence=_EVIDENCE, issues=_ISSUES_EMPTY,
            gates=gates_fail, parent_manifest_hash=_PARENT,
            config_hash=_CONFIG, environment_hash=_ENV, model_digest=_MODEL,
            eval_output_hash=_EVAL_OUT_HASH,
            law_surface_version=_LAW_SURFACE_VERSION, law_surface_hash=_LAW_SURFACE_HASH,
        )
        tmp_ledger.append_audit(m_ns)

        state_after = tmp_ledger.load_admitted_state()
        # Lineage must not include the NO_SHIP manifest
        assert state_after["shipped_run_lineage"] == lineage_before


# ── RL17: Canonical JSON determinism ─────────────────────────────────────────

class TestCanonicalJSON:
    def test_rl17_deterministic(self):
        obj = {"z": 1, "a": 2, "m": [3, 4]}
        b1 = canonical_json(obj)
        b2 = canonical_json(obj)
        assert b1 == b2

    def test_rl17_sorted_keys(self):
        obj = {"z": 1, "a": 2}
        raw = canonical_json(obj).decode("utf-8")
        assert raw.index('"a"') < raw.index('"z"')

    def test_rl17_compact_separators(self):
        b = canonical_json({"k": "v"}).decode("utf-8")
        assert " " not in b

    def test_rl17_sha256_hex_length(self):
        h = sha256_hex(b"hello")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)
