"""
tests/test_research_loop_phase_b.py — Phase B Step 3+4 tests.

schema_validate.py + replay_checker.py
(MVP_SPEC_V0_1.md §3, §4.1)

Test groups:
    SV01  validate_mission()
    SV02  validate_proposal()
    SV03  validate_receipt()
    SV04  validate_evidence()
    SV05  validate_issue() / validate_issue_list()
    SV06  validate_gate_vector()
    SV07  validate_verdict()
    SV08  validate_manifest() — full manifest validation
    SV09  Cross-field checks (evidence refs, gate/issue mismatch)
    SV10  is_valid_manifest() / validate_or_raise()
    SV11  MVP constant enforcement

    RC01  ReplayTarget construction
    RC02  run_replay() — happy path (exact hash match)
    RC03  run_replay() — stdout hash mismatch → G_replay_ok=False
    RC04  run_replay() — stderr hash mismatch → G_replay_ok=False
    RC05  run_replay() — exit code mismatch → G_replay_ok=False
    RC06  run_replay() — metric mismatch → G_replay_ok=False
    RC07  run_replay() — eval_output_hash mismatch → G_replay_ok=False
    RC08  run_replay() — timeout → G_replay_ok=False
    RC09  run_replay() — eval_output_file absent (notes, non-blocking)
    RC10  check_replay() — derives target from RunManifestV1
    RC11  Frozen tribunal suite (6 hardened tests from spec §10)
    RC12  make_replay_target() convenience constructor
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

import pytest

_SCAFFOLD_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _SCAFFOLD_ROOT not in sys.path:
    sys.path.insert(0, os.path.abspath(_SCAFFOLD_ROOT))

from research_loop import (
    GENESIS_PARENT_HASH,
    MissionV1,
    ProposalV1,
    ExecutionReceiptV1,
    EvidenceBundleV1,
    IssueItemV1,
    IssueListV1,
    GateVectorV1,
    VerdictV1,
    RunManifestV1,
    build_run_manifest,
    verify_manifest,
    manifest_to_dict,
    sha256_hex,
    compute_verdict,
    # Schema validator
    SchemaViolation,
    SchemaValidationError,
    validate_manifest,
    validate_or_raise,
    is_valid_manifest,
    # Replay checker
    ReplayTarget,
    ReplayResult,
    run_replay,
    check_replay,
    make_replay_target,
    DEFAULT_TIMEOUT_SECONDS,
)
from research_loop.schema_validate import (
    validate_mission,
    validate_proposal,
    validate_receipt,
    validate_evidence,
    validate_issue,
    validate_issue_list,
    validate_gate_vector,
    validate_verdict,
)


# ── Shared fixtures ────────────────────────────────────────────────────────────

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
    summary="BM25 tuning.",
    hypothesis="BM25 with k1=1.5 improves accuracy.",
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
    G_receipts_present=True, G_replay_ok=True, G_metric_improved=True,
    G_no_blocking_issue=True, G_kernel_integrity_ok=True,
)
_PARENT              = GENESIS_PARENT_HASH
_CONFIG              = "d" * 64
_ENV                 = "e" * 64
_MODEL               = "f" * 64
_EVAL_OUT_HASH       = "9" * 64
_LAW_SURFACE_VERSION = "LAW_SURFACE_V1"
_LAW_SURFACE_HASH    = "0" * 64   # sentinel — real hash bound at runtime
_TS                  = "2026-03-10T12:00:00Z"


def _ship_manifest(**kwargs) -> RunManifestV1:
    defaults = dict(
        manifest_id="MAN_001", ts_utc=_TS, mission=_MISSION, proposal=_PROPOSAL,
        receipts=[_RECEIPT], evidence=_EVIDENCE, issues=_ISSUES_EMPTY,
        gates=_GATES_ALL_TRUE, parent_manifest_hash=_PARENT,
        config_hash=_CONFIG, environment_hash=_ENV, model_digest=_MODEL,
        eval_output_hash=_EVAL_OUT_HASH,
        law_surface_version=_LAW_SURFACE_VERSION,
        law_surface_hash=_LAW_SURFACE_HASH,
    )
    defaults.update(kwargs)
    return build_run_manifest(**defaults)


def _ship_dict(**kwargs) -> dict:
    m = _ship_manifest(**kwargs)
    return manifest_to_dict(m)


# ── SV01: validate_mission() ──────────────────────────────────────────────────

class TestValidateMission:
    def test_sv01_valid_mission(self):
        d = {"mission_id": "M1", "domain": "retrieval_ranking",
             "objective": "obj", "metric_name": "top1_accuracy", "maximize": True}
        assert validate_mission(d) == []

    def test_sv01_missing_mission_id(self):
        d = {"domain": "retrieval_ranking", "objective": "obj",
             "metric_name": "top1_accuracy", "maximize": True}
        v = validate_mission(d)
        assert any("mission_id" in x.message or x.path.endswith(".mission_id") for x in v)

    def test_sv01_invalid_domain(self):
        d = {"mission_id": "M1", "domain": "wrong_domain",
             "objective": "obj", "metric_name": "top1_accuracy", "maximize": True}
        v = validate_mission(d)
        codes = [x.code for x in v]
        assert "INVALID_DOMAIN" in codes

    def test_sv01_invalid_metric(self):
        d = {"mission_id": "M1", "domain": "retrieval_ranking",
             "objective": "obj", "metric_name": "wrong_metric", "maximize": True}
        v = validate_mission(d)
        assert any(x.code == "INVALID_METRIC" for x in v)

    def test_sv01_not_a_dict(self):
        v = validate_mission("not a dict")
        assert len(v) == 1
        assert v[0].code == "TYPE_ERROR"

    def test_sv01_maximize_wrong_type(self):
        d = {"mission_id": "M1", "domain": "retrieval_ranking",
             "objective": "obj", "metric_name": "top1_accuracy", "maximize": "yes"}
        v = validate_mission(d)
        assert any(x.code == "TYPE_ERROR" for x in v)


# ── SV02: validate_proposal() ─────────────────────────────────────────────────

class TestValidateProposal:
    def test_sv02_valid_proposal(self):
        d = {
            "proposal_id": "P1", "proposer": "HER",
            "summary": "short", "hypothesis": "hyp",
            "mutable_files": ["ranker.py"],
            "replay_command": "python eval.py",
        }
        assert validate_proposal(d) == []

    def test_sv02_wrong_proposer(self):
        d = {
            "proposal_id": "P1", "proposer": "ATTACKER",
            "summary": "short", "hypothesis": "hyp",
            "mutable_files": ["ranker.py"], "replay_command": "python eval.py",
        }
        v = validate_proposal(d)
        assert any(x.code == "INVALID_PROPOSER" for x in v)

    def test_sv02_wrong_mutable_file(self):
        d = {
            "proposal_id": "P1", "proposer": "HER",
            "summary": "short", "hypothesis": "hyp",
            "mutable_files": ["evil.py"], "replay_command": "python eval.py",
        }
        v = validate_proposal(d)
        assert any(x.code == "INVALID_MUTABLE_FILE" for x in v)

    def test_sv02_too_many_files(self):
        d = {
            "proposal_id": "P1", "proposer": "HER",
            "summary": "short", "hypothesis": "hyp",
            "mutable_files": ["ranker.py", "extra.py"],
            "replay_command": "python eval.py",
        }
        v = validate_proposal(d)
        assert any(x.code == "TOO_MANY_FILES" for x in v)

    def test_sv02_summary_too_long(self):
        d = {
            "proposal_id": "P1", "proposer": "HER",
            "summary": "x" * 201, "hypothesis": "hyp",
            "mutable_files": ["ranker.py"], "replay_command": "python eval.py",
        }
        v = validate_proposal(d)
        assert any(x.code == "SUMMARY_TOO_LONG" for x in v)

    def test_sv02_empty_mutable_files(self):
        d = {
            "proposal_id": "P1", "proposer": "HER",
            "summary": "short", "hypothesis": "hyp",
            "mutable_files": [], "replay_command": "python eval.py",
        }
        v = validate_proposal(d)
        assert any(x.code == "EMPTY_LIST" for x in v)


# ── SV03: validate_receipt() ──────────────────────────────────────────────────

class TestValidateReceipt:
    def test_sv03_valid_receipt(self):
        d = {"receipt_id": "R1", "kind": "metric", "command": "python eval.py",
             "stdout_sha256": "a" * 64, "stderr_sha256": "b" * 64,
             "artifact_refs": []}
        assert validate_receipt(d) == []

    def test_sv03_invalid_kind(self):
        d = {"receipt_id": "R1", "kind": "unknown", "command": "python eval.py",
             "artifact_refs": []}
        v = validate_receipt(d)
        assert any(x.code == "INVALID_KIND" for x in v)

    def test_sv03_bad_stdout_hash_length(self):
        d = {"receipt_id": "R1", "kind": "metric", "command": "cmd",
             "stdout_sha256": "abc", "artifact_refs": []}
        v = validate_receipt(d)
        assert any(x.code == "INVALID_HASH_LENGTH" for x in v)

    def test_sv03_no_sovereign_gate_fields(self):
        """Receipt must NOT carry kernel_integrity_ok, receipts_present, replay_ok."""
        d = {"receipt_id": "R1", "kind": "metric", "command": "cmd",
             "artifact_refs": []}
        v = validate_receipt(d)
        # Valid receipt — none of the sovereign gate fields trigger a violation
        assert v == []

    def test_sv03_optional_hashes_absent_is_ok(self):
        d = {"receipt_id": "R1", "kind": "command", "command": "ls",
             "artifact_refs": []}
        v = validate_receipt(d)
        assert v == []

    def test_sv03_bad_hash_chars(self):
        d = {"receipt_id": "R1", "kind": "metric", "command": "cmd",
             "stdout_sha256": "G" * 64, "artifact_refs": []}
        v = validate_receipt(d)
        assert any(x.code == "INVALID_HASH_CHARS" for x in v)


# ── SV04: validate_evidence() ─────────────────────────────────────────────────

class TestValidateEvidence:
    def test_sv04_valid_evidence(self):
        d = {"evidence_id": "E1", "dataset_hash": "c" * 64,
             "metric_name": "top1_accuracy", "metric_value": 0.847,
             "receipt_ids": ["R1"]}
        assert validate_evidence(d) == []

    def test_sv04_missing_metric_value(self):
        d = {"evidence_id": "E1", "dataset_hash": "c" * 64,
             "metric_name": "top1_accuracy", "receipt_ids": ["R1"]}
        v = validate_evidence(d)
        assert any(x.path.endswith("metric_value") for x in v)

    def test_sv04_empty_receipt_ids(self):
        d = {"evidence_id": "E1", "dataset_hash": "c" * 64,
             "metric_name": "top1_accuracy", "metric_value": 0.8,
             "receipt_ids": []}
        v = validate_evidence(d)
        assert any(x.code == "EMPTY_LIST" for x in v)


# ── SV05: validate_issue() / validate_issue_list() ────────────────────────────

class TestValidateIssue:
    def test_sv05_valid_issue(self):
        d = {"issue_id": "I1", "severity": "high", "code": "TIMEOUT_RISK",
             "message": "Took 295s."}
        assert validate_issue(d) == []

    def test_sv05_invalid_severity(self):
        d = {"issue_id": "I1", "severity": "critical", "code": "X", "message": "m"}
        v = validate_issue(d)
        assert any(x.code == "INVALID_SEVERITY" for x in v)

    def test_sv05_valid_blocker(self):
        d = {"issue_id": "I1", "severity": "blocker", "code": "TIMEOUT", "message": "m"}
        assert validate_issue(d) == []

    def test_sv05_issue_list_empty_is_valid(self):
        d = {"issue_list_id": "IL1", "issues": []}
        assert validate_issue_list(d) == []

    def test_sv05_issue_list_with_blocker_is_valid(self):
        d = {"issue_list_id": "IL1", "issues": [
            {"issue_id": "I1", "severity": "blocker", "code": "X", "message": "m"}
        ]}
        assert validate_issue_list(d) == []


# ── SV06: validate_gate_vector() ──────────────────────────────────────────────

class TestValidateGateVector:
    def test_sv06_all_true(self):
        d = {
            "G_receipts_present": True, "G_replay_ok": True,
            "G_metric_improved": True, "G_no_blocking_issue": True,
            "G_kernel_integrity_ok": True,
        }
        assert validate_gate_vector(d) == []

    def test_sv06_missing_gate(self):
        d = {"G_receipts_present": True, "G_replay_ok": True}
        v = validate_gate_vector(d)
        assert len(v) >= 3  # missing 3 gates

    def test_sv06_non_bool_gate(self):
        d = {
            "G_receipts_present": 1, "G_replay_ok": True,
            "G_metric_improved": True, "G_no_blocking_issue": True,
            "G_kernel_integrity_ok": True,
        }
        v = validate_gate_vector(d)
        assert any(x.code == "TYPE_ERROR" for x in v)


# ── SV07: validate_verdict() ──────────────────────────────────────────────────

class TestValidateVerdict:
    def test_sv07_ship_no_codes(self):
        d = {"verdict": "SHIP", "blocking_reason_codes": []}
        assert validate_verdict(d) == []

    def test_sv07_no_ship_with_codes(self):
        d = {"verdict": "NO_SHIP", "blocking_reason_codes": ["MISSING_RECEIPTS"]}
        assert validate_verdict(d) == []

    def test_sv07_ship_with_codes_is_violation(self):
        d = {"verdict": "SHIP", "blocking_reason_codes": ["MISSING_RECEIPTS"]}
        v = validate_verdict(d)
        assert any(x.code == "SHIP_WITH_BLOCKING_CODES" for x in v)

    def test_sv07_no_ship_without_codes_is_violation(self):
        d = {"verdict": "NO_SHIP", "blocking_reason_codes": []}
        v = validate_verdict(d)
        assert any(x.code == "NO_SHIP_WITHOUT_CODES" for x in v)

    def test_sv07_invalid_verdict_value(self):
        d = {"verdict": "APPROVE", "blocking_reason_codes": []}
        v = validate_verdict(d)
        assert any(x.code == "INVALID_VERDICT" for x in v)

    def test_sv07_unknown_reason_code(self):
        d = {"verdict": "NO_SHIP", "blocking_reason_codes": ["INVENTED_CODE"]}
        v = validate_verdict(d)
        assert any(x.code == "INVALID_REASON_CODE" for x in v)

    def test_sv07_quarantine_with_kernel_integrity_code(self):
        d = {"verdict": "QUARANTINE", "blocking_reason_codes": ["KERNEL_INTEGRITY_FAILED"]}
        assert validate_verdict(d) == []


# ── SV08: validate_manifest() ─────────────────────────────────────────────────

class TestValidateManifest:
    def test_sv08_valid_full_manifest(self):
        d = _ship_dict()
        v = validate_manifest(d)
        assert v == [], f"Unexpected violations: {v}"

    def test_sv08_missing_manifest_version(self):
        d = _ship_dict()
        del d["manifest_version"]
        v = validate_manifest(d)
        assert any(x.path.endswith("manifest_version") for x in v)

    def test_sv08_wrong_manifest_version(self):
        d = _ship_dict()
        d["manifest_version"] = "WRONG_VERSION"
        v = validate_manifest(d)
        assert any(x.code == "INVALID_VERSION" for x in v)

    def test_sv08_missing_eval_output_hash(self):
        """eval_output_hash is required for G_replay_ok (§4.1)."""
        d = _ship_dict()
        del d["eval_output_hash"]
        v = validate_manifest(d)
        assert any(x.path.endswith("eval_output_hash") for x in v)

    def test_sv08_missing_manifest_hash(self):
        d = _ship_dict()
        del d["manifest_hash"]
        v = validate_manifest(d)
        assert any(x.path.endswith("manifest_hash") for x in v)

    def test_sv08_missing_mission(self):
        d = _ship_dict()
        del d["mission"]
        v = validate_manifest(d)
        assert any(x.path.endswith("mission") for x in v)

    def test_sv08_empty_receipts(self):
        d = _ship_dict()
        d["receipts"] = []
        v = validate_manifest(d)
        assert any(x.code == "EMPTY_LIST" for x in v)

    def test_sv08_not_a_dict(self):
        v = validate_manifest("not a dict")
        assert len(v) == 1
        assert v[0].code == "TYPE_ERROR"

    def test_sv08_ts_utc_required(self):
        d = _ship_dict()
        del d["ts_utc"]
        v = validate_manifest(d)
        assert any(x.path.endswith("ts_utc") for x in v)

    def test_sv08_missing_law_surface_hash(self):
        """law_surface_hash is required — binds manifest to its legal regime."""
        d = _ship_dict()
        del d["law_surface_hash"]
        v = validate_manifest(d)
        assert any(x.path.endswith("law_surface_hash") for x in v)

    def test_sv08_missing_law_surface_version(self):
        """law_surface_version is required — identifies the legal regime."""
        d = _ship_dict()
        del d["law_surface_version"]
        v = validate_manifest(d)
        assert any(x.path.endswith("law_surface_version") for x in v)


# ── SV09: Cross-field checks ──────────────────────────────────────────────────

class TestCrossFieldChecks:
    def test_sv09_dangling_evidence_receipt_ref(self):
        d = _ship_dict()
        d["evidence"]["receipt_ids"] = ["RCP_NONEXISTENT"]
        v = validate_manifest(d)
        assert any(x.code == "DANGLING_EVIDENCE_REFERENCE" for x in v)

    def test_sv09_blocker_issue_with_gate_true(self):
        d = _ship_dict()
        d["issues"]["issues"] = [
            {"issue_id": "I1", "severity": "blocker",
             "code": "TIMEOUT", "message": "m"}
        ]
        d["gates"]["G_no_blocking_issue"] = True
        v = validate_manifest(d)
        assert any(x.code == "GATE_ISSUE_MISMATCH" for x in v)

    def test_sv09_blocker_issue_with_gate_false_is_ok(self):
        d = _ship_dict()
        d["issues"]["issues"] = [
            {"issue_id": "I1", "severity": "blocker",
             "code": "TIMEOUT", "message": "m"}
        ]
        d["gates"]["G_no_blocking_issue"] = False
        d["verdict"] = {"verdict": "NO_SHIP",
                        "blocking_reason_codes": ["BLOCKING_ISSUE"]}
        v = validate_manifest(d)
        # No gate mismatch since G_no_blocking_issue=False
        assert not any(x.code == "GATE_ISSUE_MISMATCH" for x in v)


# ── SV10: is_valid_manifest() / validate_or_raise() ──────────────────────────

class TestValidateOrRaise:
    def test_sv10_is_valid_true_for_good_manifest(self):
        d = _ship_dict()
        assert is_valid_manifest(d) is True

    def test_sv10_is_valid_false_for_bad(self):
        d = _ship_dict()
        del d["eval_output_hash"]
        assert is_valid_manifest(d) is False

    def test_sv10_validate_or_raise_passes_for_good(self):
        d = _ship_dict()
        validate_or_raise(d)  # must not raise

    def test_sv10_validate_or_raise_raises_for_bad(self):
        d = _ship_dict()
        del d["manifest_hash"]
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_or_raise(d)
        assert len(exc_info.value.violations) >= 1

    def test_sv10_schema_violation_has_path_code_message(self):
        d = _ship_dict()
        d["manifest_version"] = "WRONG"
        v = validate_manifest(d)
        assert len(v) >= 1
        assert isinstance(v[0], SchemaViolation)
        assert v[0].path
        assert v[0].code
        assert v[0].message


# ── SV11: MVP constant enforcement ───────────────────────────────────────────

class TestMVPConstantEnforcement:
    def test_sv11_wrong_domain_rejected(self):
        d = _ship_dict()
        d["mission"]["domain"] = "image_classification"
        v = validate_manifest(d)
        assert any(x.code == "INVALID_DOMAIN" for x in v)

    def test_sv11_wrong_metric_rejected(self):
        d = _ship_dict()
        d["mission"]["metric_name"] = "f1_score"
        d["evidence"]["metric_name"] = "f1_score"
        v = validate_manifest(d)
        assert any(x.code == "INVALID_METRIC" for x in v)

    def test_sv11_wrong_proposer_rejected(self):
        d = _ship_dict()
        d["proposal"]["proposer"] = "ADVERSARY"
        v = validate_manifest(d)
        assert any(x.code == "INVALID_PROPOSER" for x in v)

    def test_sv11_wrong_mutable_file_rejected(self):
        d = _ship_dict()
        d["proposal"]["mutable_files"] = ["kernel.py"]
        v = validate_manifest(d)
        assert any(x.code == "INVALID_MUTABLE_FILE" for x in v)


# ── RC01: ReplayTarget construction ───────────────────────────────────────────

class TestReplayTarget:
    def test_rc01_construction(self):
        t = make_replay_target(
            expected_exit_code=0,
            expected_metric_after=0.847,
            expected_stdout_sha256="a" * 64,
            expected_stderr_sha256="b" * 64,
            expected_eval_output_hash="c" * 64,
        )
        assert t.expected_exit_code == 0
        assert t.expected_metric_after == 0.847
        assert t.expected_stdout_sha256 == "a" * 64

    def test_rc01_defaults_are_none(self):
        t = make_replay_target()
        assert t.expected_stdout_sha256 is None
        assert t.expected_eval_output_hash is None

    def test_rc01_frozen(self):
        t = make_replay_target()
        with pytest.raises((AttributeError, TypeError)):
            t.expected_exit_code = 99  # type: ignore


# ── RC02: run_replay() — happy path ───────────────────────────────────────────

def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class TestRunReplayHappyPath:
    def test_rc02_echo_command_passes(self, tmp_path):
        """A simple echo command: both stdout/stderr hashes match."""
        import platform
        cmd = 'python3 -c "print(\'top1_accuracy: 0.847\')"'

        # Run once to get expected values
        import subprocess
        proc = subprocess.run(cmd, shell=True, capture_output=True)
        expected_stdout = _sha256_bytes(proc.stdout)
        expected_stderr = _sha256_bytes(proc.stderr)

        target = make_replay_target(
            expected_exit_code=0,
            expected_metric_after=0.847,
            expected_stdout_sha256=expected_stdout,
            expected_stderr_sha256=expected_stderr,
        )
        result = run_replay(cmd, target, timeout_seconds=30)
        assert result.G_replay_ok is True
        assert result.diff == []
        assert result.failure_reason is None

    def test_rc02_exit_code_zero(self, tmp_path):
        cmd = 'python3 -c "print(\'top1_accuracy: 0.500\')"'
        import subprocess
        proc = subprocess.run(cmd, shell=True, capture_output=True)
        target = make_replay_target(
            expected_exit_code=0,
            expected_metric_after=0.500,
            expected_stdout_sha256=_sha256_bytes(proc.stdout),
            expected_stderr_sha256=_sha256_bytes(proc.stderr),
        )
        result = run_replay(cmd, target, timeout_seconds=30)
        assert result.observed_exit_code == 0
        assert result.G_replay_ok is True


# ── RC03: stdout hash mismatch → NO_SHIP ─────────────────────────────────────

class TestStdoutMismatch:
    def test_rc03_stdout_mismatch_sets_no_ship(self):
        cmd = 'python3 -c "print(\'top1_accuracy: 0.847\')"'
        target = make_replay_target(
            expected_exit_code=0,
            expected_metric_after=0.847,
            expected_stdout_sha256="a" * 64,  # wrong hash
        )
        result = run_replay(cmd, target, timeout_seconds=30)
        assert result.G_replay_ok is False
        assert any("STDOUT_HASH_MISMATCH" in d for d in result.diff)
        assert result.failure_reason == "HASH_MISMATCH"


# ── RC04: stderr hash mismatch → NO_SHIP ─────────────────────────────────────

class TestStderrMismatch:
    def test_rc04_stderr_mismatch_sets_no_ship(self):
        cmd = 'python3 -c "import sys; print(\'top1_accuracy: 0.847\'); sys.stderr.write(\'warn\\n\')"'
        target = make_replay_target(
            expected_exit_code=0,
            expected_metric_after=0.847,
            expected_stderr_sha256="z" * 64,  # wrong hash
        )
        result = run_replay(cmd, target, timeout_seconds=30)
        assert result.G_replay_ok is False
        assert any("STDERR_HASH_MISMATCH" in d for d in result.diff)


# ── RC05: exit code mismatch → NO_SHIP ───────────────────────────────────────

class TestExitCodeMismatch:
    def test_rc05_nonzero_exit_code_fails(self):
        cmd = "python3 -c \"import sys; sys.exit(1)\""
        target = make_replay_target(
            expected_exit_code=0,  # expect success
            expected_metric_after=0.0,
        )
        result = run_replay(cmd, target, timeout_seconds=30)
        assert result.G_replay_ok is False
        assert any("EXIT_CODE_MISMATCH" in d for d in result.diff)

    def test_rc05_wrong_expected_exit_code(self):
        cmd = 'python3 -c "print(\'top1_accuracy: 0.8\')"'
        target = make_replay_target(
            expected_exit_code=99,  # wrong expectation
            expected_metric_after=0.8,
        )
        result = run_replay(cmd, target, timeout_seconds=30)
        assert result.G_replay_ok is False
        assert any("EXIT_CODE_MISMATCH" in d for d in result.diff)


# ── RC06: metric mismatch → NO_SHIP ──────────────────────────────────────────

class TestMetricMismatch:
    def test_rc06_metric_changed_fails(self):
        cmd = 'python3 -c "print(\'top1_accuracy: 0.600\')"'
        target = make_replay_target(
            expected_exit_code=0,
            expected_metric_after=0.847,  # different from what command outputs
        )
        result = run_replay(cmd, target, timeout_seconds=30)
        assert result.G_replay_ok is False
        assert any("METRIC_MISMATCH" in d for d in result.diff)

    def test_rc06_metric_not_in_stdout(self):
        cmd = 'python3 -c "print(\'no metric here\')"'
        target = make_replay_target(
            expected_exit_code=0,
            expected_metric_after=0.847,
        )
        result = run_replay(cmd, target, timeout_seconds=30)
        assert result.G_replay_ok is False
        assert any("METRIC_NOT_FOUND" in d for d in result.diff)


# ── RC07: eval_output_hash mismatch → NO_SHIP ────────────────────────────────

class TestEvalOutputHashMismatch:
    def test_rc07_eval_output_file_hash_wrong(self, tmp_path):
        """eval_output_hash mismatch must set G_replay_ok = False."""
        # Create an eval output file with known content
        eval_file = tmp_path / "eval_out.json"
        eval_file.write_bytes(b'{"score": 0.847}')
        actual_hash = _sha256_bytes(b'{"score": 0.847}')

        cmd = 'python3 -c "print(\'top1_accuracy: 0.847\')"'
        import subprocess
        proc = subprocess.run(cmd, shell=True, capture_output=True)

        # Provide a WRONG eval_output_hash
        target = make_replay_target(
            expected_exit_code=0,
            expected_metric_after=0.847,
            expected_stdout_sha256=_sha256_bytes(proc.stdout),
            expected_stderr_sha256=_sha256_bytes(proc.stderr),
            expected_eval_output_hash="dead" * 16,  # wrong
        )
        result = run_replay(cmd, target,
                            eval_output_file=eval_file,
                            timeout_seconds=30)
        assert result.G_replay_ok is False
        assert any("EVAL_OUTPUT_HASH_MISMATCH" in d for d in result.diff)

    def test_rc07_eval_output_file_hash_correct(self, tmp_path):
        """Matching eval_output_hash must pass."""
        eval_file = tmp_path / "eval_out.json"
        content = b'{"score": 0.847}'
        eval_file.write_bytes(content)
        actual_hash = _sha256_bytes(content)

        cmd = 'python3 -c "print(\'top1_accuracy: 0.847\')"'
        import subprocess
        proc = subprocess.run(cmd, shell=True, capture_output=True)

        target = make_replay_target(
            expected_exit_code=0,
            expected_metric_after=0.847,
            expected_stdout_sha256=_sha256_bytes(proc.stdout),
            expected_stderr_sha256=_sha256_bytes(proc.stderr),
            expected_eval_output_hash=actual_hash,
        )
        result = run_replay(cmd, target,
                            eval_output_file=eval_file,
                            timeout_seconds=30)
        assert result.G_replay_ok is True


# ── RC08: timeout → NO_SHIP ───────────────────────────────────────────────────

class TestTimeout:
    def test_rc08_timeout_sets_no_ship(self):
        # Command that sleeps for longer than timeout
        cmd = "python3 -c \"import time; time.sleep(10)\""
        target = make_replay_target(expected_exit_code=0, expected_metric_after=0.0)
        result = run_replay(cmd, target, timeout_seconds=1)
        assert result.G_replay_ok is False
        assert result.failure_reason == "TIMEOUT"
        assert any("timed out" in d.lower() for d in result.diff)


# ── RC09: eval_output_file absent (notes, non-blocking) ──────────────────────

class TestEvalOutputFileAbsent:
    def test_rc09_missing_file_records_note(self, tmp_path):
        cmd = 'python3 -c "print(\'top1_accuracy: 0.5\')"'
        import subprocess
        proc = subprocess.run(cmd, shell=True, capture_output=True)

        target = make_replay_target(
            expected_exit_code=0,
            expected_metric_after=0.5,
            expected_stdout_sha256=_sha256_bytes(proc.stdout),
            expected_stderr_sha256=_sha256_bytes(proc.stderr),
            expected_eval_output_hash="q" * 64,
        )
        nonexistent = tmp_path / "no_such_file.json"
        result = run_replay(cmd, target,
                            eval_output_file=nonexistent,
                            timeout_seconds=30)
        # File missing records a note but does NOT fail on eval_output_hash
        assert any("EVAL_OUTPUT_FILE_NOT_FOUND" in n for n in result.notes)

    def test_rc09_no_file_specified_records_note(self):
        cmd = 'python3 -c "print(\'top1_accuracy: 0.5\')"'
        import subprocess
        proc = subprocess.run(cmd, shell=True, capture_output=True)

        target = make_replay_target(
            expected_exit_code=0,
            expected_metric_after=0.5,
            expected_stdout_sha256=_sha256_bytes(proc.stdout),
            expected_stderr_sha256=_sha256_bytes(proc.stderr),
            expected_eval_output_hash="q" * 64,
        )
        result = run_replay(cmd, target, timeout_seconds=30)  # no eval_output_file
        assert any("EVAL_OUTPUT_FILE_NOT_SPECIFIED" in n for n in result.notes)


# ── RC10: check_replay() — derives target from RunManifestV1 ─────────────────

class TestCheckReplay:
    def test_rc10_derives_target_from_manifest(self, tmp_path):
        """check_replay should run proposal.replay_command and compare against manifest."""
        import subprocess
        cmd = 'python3 -c "print(\'top1_accuracy: 0.847\')"'
        proc = subprocess.run(cmd, shell=True, capture_output=True)
        stdout_hash = _sha256_bytes(proc.stdout)
        stderr_hash = _sha256_bytes(proc.stderr)

        receipt = ExecutionReceiptV1(
            receipt_id="RCP_001",
            kind="metric",
            command=cmd,
            stdout_sha256=stdout_hash,
            stderr_sha256=stderr_hash,
            artifact_refs=["metric:top1_accuracy=0.847"],
        )
        evidence = EvidenceBundleV1(
            evidence_id="EV_001",
            dataset_hash="c" * 64,
            metric_name="top1_accuracy",
            metric_value=0.847,
            receipt_ids=["RCP_001"],
        )
        m = build_run_manifest(
            manifest_id="MAN_001", ts_utc=_TS, mission=_MISSION,
            proposal=ProposalV1(
                proposal_id="PROP_001", proposer="HER",
                summary="test", hypothesis="test",
                mutable_files=["ranker.py"], replay_command=cmd,
            ),
            receipts=[receipt], evidence=evidence, issues=_ISSUES_EMPTY,
            gates=_GATES_ALL_TRUE, parent_manifest_hash=_PARENT,
            config_hash=_CONFIG, environment_hash=_ENV, model_digest=_MODEL,
            eval_output_hash=_EVAL_OUT_HASH,  # not verified — no eval_output_file
            law_surface_version=_LAW_SURFACE_VERSION,
            law_surface_hash=_LAW_SURFACE_HASH,
        )
        result = check_replay(m, timeout_seconds=30)
        # eval_output_hash comparison is skipped (no eval_output_file given)
        assert result.G_replay_ok is True
        assert any("EVAL_OUTPUT_FILE_NOT_SPECIFIED" in n for n in result.notes)


# ── RC11: Frozen tribunal suite (spec §10 hard tests) ─────────────────────────

class TestFrozenTribunalSuite:
    """
    Six cases frozen in MVP_SPEC_V0_1.md §10 + the eval_output_hash extension.
    These are the admissibility boundary tests.
    """

    def test_rc11_missing_required_artifact_ref_schema_reject(self):
        """Missing required field in manifest → schema validator rejects."""
        d = _ship_dict()
        del d["evidence"]  # remove required sub-object
        v = validate_manifest(d)
        assert not is_valid_manifest(d)
        assert any(x.path.endswith("evidence") for x in v)

    def test_rc11_replay_stdout_hash_change_no_ship(self):
        """If replay produces different stdout, G_replay_ok = False."""
        cmd = 'python3 -c "print(\'top1_accuracy: 0.847\')"'
        target = make_replay_target(
            expected_exit_code=0,
            expected_metric_after=0.847,
            expected_stdout_sha256="deadbeef" * 8,  # stale/wrong hash
        )
        result = run_replay(cmd, target, timeout_seconds=30)
        assert result.G_replay_ok is False
        assert any("STDOUT_HASH_MISMATCH" in d for d in result.diff)

    def test_rc11_blocker_in_issue_list_no_ship(self):
        """Blocker issue → G_no_blocking_issue=False → NO_SHIP."""
        gates = GateVectorV1(
            G_receipts_present=True, G_replay_ok=True, G_metric_improved=True,
            G_no_blocking_issue=False, G_kernel_integrity_ok=True,
        )
        verdict = compute_verdict(gates)
        assert verdict.verdict == "NO_SHIP"
        assert "BLOCKING_ISSUE" in verdict.blocking_reason_codes

    def test_rc11_gain_below_threshold_no_ship(self):
        """Improvement < +0.002 → G_metric_improved=False → NO_SHIP."""
        gates = GateVectorV1(
            G_receipts_present=True, G_replay_ok=True, G_metric_improved=False,
            G_no_blocking_issue=True, G_kernel_integrity_ok=True,
        )
        verdict = compute_verdict(gates)
        assert verdict.verdict == "NO_SHIP"
        assert "METRIC_NOT_IMPROVED" in verdict.blocking_reason_codes

    def test_rc11_valid_full_run_ships(self):
        """All gates True, valid manifest → SHIP."""
        m = _ship_manifest()
        assert m.verdict.verdict == "SHIP"
        assert verify_manifest(m) is True

    def test_rc11_no_ship_does_not_mutate_state(self):
        """NO_SHIP verdict does not alter admitted optimization state."""
        from research_loop import reduce_run
        m = _ship_manifest()
        state = {"best_metric": 0.847, "shipped_run_lineage": []}
        gates_fail = GateVectorV1(
            G_receipts_present=False, G_replay_ok=True, G_metric_improved=True,
            G_no_blocking_issue=True, G_kernel_integrity_ok=True,
        )
        verdict_str, new_state = reduce_run(state, m, gates_fail)
        assert verdict_str == "NO_SHIP"
        assert new_state is state

    def test_rc11_quarantine_does_not_mutate_state(self):
        """QUARANTINE verdict does not alter admitted optimization state."""
        from research_loop import reduce_run
        m = _ship_manifest()
        state = {"best_metric": 0.847, "shipped_run_lineage": []}
        gates_q = GateVectorV1(
            G_receipts_present=True, G_replay_ok=True, G_metric_improved=True,
            G_no_blocking_issue=True, G_kernel_integrity_ok=False,
        )
        verdict_str, new_state = reduce_run(state, m, gates_q)
        assert verdict_str == "QUARANTINE"
        assert new_state is state

    def test_rc11_eval_output_hash_change_no_ship(self, tmp_path):
        """eval_output_hash change → G_replay_ok=False (elevated to tribunal test)."""
        eval_file = tmp_path / "eval.json"
        content = b'{"result": "correct"}'
        eval_file.write_bytes(content)
        real_hash = _sha256_bytes(content)

        cmd = 'python3 -c "print(\'top1_accuracy: 0.9\')"'
        import subprocess
        proc = subprocess.run(cmd, shell=True, capture_output=True)

        target = make_replay_target(
            expected_exit_code=0,
            expected_metric_after=0.9,
            expected_stdout_sha256=_sha256_bytes(proc.stdout),
            expected_stderr_sha256=_sha256_bytes(proc.stderr),
            expected_eval_output_hash="aaaa" * 16,  # stale — differs from real
        )
        result = run_replay(cmd, target,
                            eval_output_file=eval_file,
                            timeout_seconds=30)
        assert result.G_replay_ok is False
        assert any("EVAL_OUTPUT_HASH_MISMATCH" in d for d in result.diff)


# ── RC12: make_replay_target() ────────────────────────────────────────────────

class TestMakeReplayTarget:
    def test_rc12_all_fields(self):
        t = make_replay_target(
            expected_exit_code=0,
            expected_metric_after=0.9,
            expected_stdout_sha256="a" * 64,
            expected_stderr_sha256="b" * 64,
            expected_eval_output_hash="c" * 64,
        )
        assert t.expected_exit_code == 0
        assert t.expected_metric_after == 0.9

    def test_rc12_default_timeout(self):
        assert DEFAULT_TIMEOUT_SECONDS == 300
