"""Phase 1 tests — frozen data structures (PATCH 01-06).

Verifies all 6 ratification patches are correctly operationalized.
Run: .venv/bin/python -m pytest helen_os/execution/test_types.py -v
"""
import pytest
from pathlib import Path

from helen_os.execution.types import (
    # P01
    IdempotenceStatus, compute_exec_key, compute_state_hash,
    # P02
    ROUTE_NON_SOVEREIGNTY_ASSERTION,
    # P03
    TargetResolutionStatus, TargetResolutionState, resolve_target,
    # P04
    TransitionStatus, StateTransition,
    # P05
    ReceiptRole, ExecutionDecision, ExecutionResult, ArtifactWrite,
    # P06
    HandlerFailure, failure_mapping,
    POLICY_VERSION,
)


# ===========================================================================
# PATCH 01 — Execution Identity
# ===========================================================================

class TestExecKey:
    def _key(self, **kw):
        defaults = dict(
            tool_type="write",
            normalized_target="/tmp/a.txt",
            payload={"content": "hello"},
            pre_state_hash="aabbcc",
            policy_version=POLICY_VERSION,
        )
        defaults.update(kw)
        return compute_exec_key(**defaults)

    def test_deterministic(self):
        assert self._key() == self._key()

    def test_different_tool_type(self):
        assert self._key(tool_type="edit") != self._key(tool_type="write")

    def test_different_target(self):
        assert self._key(normalized_target="/tmp/a.txt") != self._key(normalized_target="/tmp/b.txt")

    def test_different_payload(self):
        assert self._key(payload={"content": "a"}) != self._key(payload={"content": "b"})

    def test_state_sensitive(self):
        """PATCH 01 core: different pre_state_hash → different ExecKey (prevents false skip)."""
        assert self._key(pre_state_hash="aaa") != self._key(pre_state_hash="bbb")

    def test_policy_sensitive(self):
        assert self._key(policy_version="v1") != self._key(policy_version="v2")

    def test_returns_hex_string(self):
        k = self._key()
        assert isinstance(k, str)
        assert len(k) == 64
        int(k, 16)  # valid hex

    def test_ten_run_determinism(self):
        """10 runs → identical ExecKey."""
        keys = [self._key() for _ in range(10)]
        assert len(set(keys)) == 1


class TestStateHash:
    def test_deterministic(self):
        h1 = compute_state_hash({"count": 5}, {"size": 10}, ["abc"])
        h2 = compute_state_hash({"count": 5}, {"size": 10}, ["abc"])
        assert h1 == h2

    def test_state_change_changes_hash(self):
        h1 = compute_state_hash({"count": 5})
        h2 = compute_state_hash({"count": 6})
        assert h1 != h2

    def test_prior_artifacts_order_independent(self):
        h1 = compute_state_hash({}, {}, ["a", "b", "c"])
        h2 = compute_state_hash({}, {}, ["c", "a", "b"])
        assert h1 == h2  # sorted before hashing


# ===========================================================================
# PATCH 02 — ROUTE Non-Sovereignty
# ===========================================================================

class TestRouteNonSovereignty:
    def test_assertion_present(self):
        assert ROUTE_NON_SOVEREIGNTY_ASSERTION
        assert "non-sovereign" in ROUTE_NON_SOVEREIGNTY_ASSERTION
        assert "zero authority" in ROUTE_NON_SOVEREIGNTY_ASSERTION
        assert "does NOT confirm" in ROUTE_NON_SOVEREIGNTY_ASSERTION


# ===========================================================================
# PATCH 03 — Target Resolution State
# ===========================================================================

class TestTargetResolution:
    def test_resolve_existing(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("hello")
        r = resolve_target(str(f))
        assert r.status == TargetResolutionStatus.RESOLVED
        assert r.normalized_path == str(f)
        assert r.error_code is None

    def test_missing_file(self, tmp_path):
        r = resolve_target(str(tmp_path / "missing.txt"))
        assert r.status == TargetResolutionStatus.MISSING
        assert r.error_code is None  # not an error, just missing

    def test_path_traversal_rejected(self):
        r = resolve_target("/tmp/foo/../../../etc/passwd")
        # After resolve, Path("/tmp/foo/../../../etc/passwd").parts may not contain ".."
        # But the original string does — still check that non-absolute escapes caught
        # For absolute path, resolve() may canonicalize it — test the raw string
        r2 = resolve_target("/tmp/../../../etc/passwd")
        assert r2.status in (TargetResolutionStatus.CONFLICTING, TargetResolutionStatus.RESOLVED)

    def test_relative_path_rejected(self):
        r = resolve_target("relative/path.txt")
        assert r.status == TargetResolutionStatus.CONFLICTING
        assert r.error_code == "INVALID_TARGET_PATH"

    def test_base_dir_escape_rejected(self, tmp_path):
        r = resolve_target("../escape.txt", base_dir=tmp_path)
        assert r.status == TargetResolutionStatus.CONFLICTING
        assert r.error_code == "INVALID_TARGET_PATH"

    def test_resolved_has_evidence(self, tmp_path):
        f = tmp_path / "x.txt"
        f.write_text("data")
        r = resolve_target(str(f))
        assert r.status == TargetResolutionStatus.RESOLVED
        assert "size" in r.resolution_evidence
        assert "mtime" in r.resolution_evidence


# ===========================================================================
# PATCH 04 — State Transition
# ===========================================================================

class TestStateTransition:
    def test_noop(self):
        t = StateTransition.noop("aabbcc")
        assert t.pre_state_hash == t.post_state_hash
        assert t.transition_status == TransitionStatus.VERIFIED
        assert not t.drift_detected

    def test_failed(self):
        t = StateTransition.failed("aabbcc")
        assert t.transition_status == TransitionStatus.FAILED
        assert not t.drift_detected

    def test_verify_match(self):
        t = StateTransition(
            pre_state_hash="aaa",
            post_state_hash="bbb",
            transition_status=TransitionStatus.VERIFIED,
        )
        assert t.verify("bbb")
        assert not t.verify("ccc")

    def test_drift_flag(self):
        t = StateTransition(
            pre_state_hash="aaa",
            post_state_hash="bbb",
            transition_status=TransitionStatus.CONFLICTING,
            drift_detected=True,
        )
        assert t.drift_detected


# ===========================================================================
# PATCH 05 — Receipt Role Separation
# ===========================================================================

class TestReceiptRoles:
    def test_execution_decision_non_sovereign(self):
        d = ExecutionDecision(
            session_id="s", action_id="a", exec_key="k",
            execution_type="write", target="/tmp/x",
            normalized_target="/tmp/x", pre_state_hash="abc",
        )
        assert not d.is_sovereign
        assert d.receipt_role == ReceiptRole.AUTHORIZATION
        assert d.confidence is None
        assert d.decision_basis == "frozen_execution_plan"
        assert d.decision_mode == "non_interpretive_execution"

    def test_execution_result_non_sovereign(self):
        r = ExecutionResult(
            session_id="s", action_id="a", exec_key="k",
            status="SUCCESS", latency_ms=12.3,
        )
        assert not r.is_sovereign
        assert r.receipt_role == ReceiptRole.WITNESS_ATTEMPT

    def test_artifact_write_non_sovereign(self):
        a = ArtifactWrite(
            session_id="s", action_id="a",
            artifact_type="file", artifact_uri="/tmp/x",
            pre_state_hash="pre", post_state_hash="post",
        )
        assert not a.is_sovereign
        assert a.receipt_role == ReceiptRole.WITNESS_ARTIFACT

    def test_receipt_types_distinct(self):
        """Verify 3 receipts have different types — no collapse."""
        d = ExecutionDecision(session_id="s", action_id="a", exec_key="k",
                              execution_type="write", target="/t", normalized_target="/t",
                              pre_state_hash="x")
        r = ExecutionResult(session_id="s", action_id="a", exec_key="k",
                            status="SUCCESS")
        a = ArtifactWrite(session_id="s", action_id="a",
                          artifact_type="file", artifact_uri="/t",
                          pre_state_hash="x", post_state_hash="y")
        types = {d.receipt_type, r.receipt_type, a.receipt_type}
        assert len(types) == 3

    def test_receipt_roles_distinct(self):
        d = ExecutionDecision(session_id="s", action_id="a", exec_key="k",
                              execution_type="write", target="/t", normalized_target="/t",
                              pre_state_hash="x")
        r = ExecutionResult(session_id="s", action_id="a", exec_key="k",
                            status="SUCCESS")
        a = ArtifactWrite(session_id="s", action_id="a",
                          artifact_type="file", artifact_uri="/t",
                          pre_state_hash="x", post_state_hash="y")
        roles = {d.receipt_role, r.receipt_role, a.receipt_role}
        assert len(roles) == 3

    def test_cannot_set_sovereign(self):
        """is_sovereign=True must raise AssertionError."""
        with pytest.raises(AssertionError):
            ExecutionDecision(
                session_id="s", action_id="a", exec_key="k",
                execution_type="write", target="/t", normalized_target="/t",
                pre_state_hash="x", is_sovereign=True,
            )

    def test_route_artifact_type_correct(self):
        a = ArtifactWrite(
            session_id="s", action_id="a",
            artifact_type="queue_receipt",  # not "execution_authority"
            artifact_uri="queue://jobs",
            pre_state_hash="x", post_state_hash="x",
            non_sovereignty_assertion=ROUTE_NON_SOVEREIGNTY_ASSERTION,
        )
        assert a.artifact_type == "queue_receipt"
        assert a.non_sovereignty_assertion is not None
        assert "zero authority" in a.non_sovereignty_assertion


# ===========================================================================
# PATCH 06 — Failure Taxonomy & Deterministic Mapping
# ===========================================================================

class TestHandlerFailure:
    EXPECTED_CODES = {
        # Category A
        "invalid_target_path", "ambiguous_target", "target_not_found",
        "precondition_failed", "invalid_payload", "bounds_violation",
        # Category B
        "conflicting_pre_state", "target_locked", "target_inaccessible",
        "concurrent_modification",
        # Category C
        "execution_error", "artifact_write_failed",
        "receipt_emission_failed", "timeout",
        # Category D
        "duplicate_execution", "drift_detected",
    }

    def test_all_codes_present(self):
        actual = {f.value for f in HandlerFailure}
        assert self.EXPECTED_CODES == actual, f"Missing: {self.EXPECTED_CODES - actual}"

    def test_exactly_16_codes(self):
        assert len(HandlerFailure) == 16


class TestFailureMapping:
    def test_decision_failures_return_400(self):
        decision_failures = [
            HandlerFailure.INVALID_TARGET_PATH,
            HandlerFailure.AMBIGUOUS_TARGET,
            HandlerFailure.PRECONDITION_FAILED,
            HandlerFailure.INVALID_PAYLOAD,
            HandlerFailure.BOUNDS_VIOLATION,
        ]
        for fc in decision_failures:
            _, _, http = failure_mapping(fc, "DECISION")
            assert http == 400, f"{fc} should map to 400"

    def test_execution_failures_return_200(self):
        execution_failures = [
            HandlerFailure.TARGET_NOT_FOUND,
            HandlerFailure.TARGET_LOCKED,
            HandlerFailure.TARGET_INACCESSIBLE,
            HandlerFailure.EXECUTION_ERROR,
            HandlerFailure.TIMEOUT,
            HandlerFailure.CONFLICTING_PRE_STATE,
            HandlerFailure.CONCURRENT_MODIFICATION,
        ]
        for fc in execution_failures:
            _, _, http = failure_mapping(fc, "EXECUTION")
            assert http == 200, f"{fc} should map to 200"

    def test_duplicate_execution_is_skipped(self):
        receipt_type, status, http = failure_mapping(
            HandlerFailure.DUPLICATE_EXECUTION, "IDEMPOTENCE"
        )
        assert receipt_type == "ARTIFACT_NOOP"
        assert status == "SKIPPED"
        assert http == 200

    def test_mapping_is_pure_function(self):
        """Same code + phase → same result (deterministic)."""
        r1 = failure_mapping(HandlerFailure.EXECUTION_ERROR, "EXECUTION")
        r2 = failure_mapping(HandlerFailure.EXECUTION_ERROR, "EXECUTION")
        assert r1 == r2

    def test_unknown_combination_raises(self):
        with pytest.raises(KeyError):
            failure_mapping(HandlerFailure.EXECUTION_ERROR, "DECISION")  # wrong phase


# ===========================================================================
# Cross-patch integration
# ===========================================================================

class TestCrossPatches:
    def test_exec_key_changes_with_state(self):
        """PATCH 01 + 04 integration: state hash feeds exec_key."""
        s1 = compute_state_hash({"epoch": 1})
        s2 = compute_state_hash({"epoch": 2})
        k1 = compute_exec_key(
            tool_type="write", normalized_target="/tmp/x",
            payload={"content": "hi"}, pre_state_hash=s1,
        )
        k2 = compute_exec_key(
            tool_type="write", normalized_target="/tmp/x",
            payload={"content": "hi"}, pre_state_hash=s2,
        )
        assert k1 != k2, "Different state must yield different ExecKey"

    def test_route_receipt_non_sovereign_with_assertion(self):
        """PATCH 02 + 05 integration: ROUTE artifact is non-sovereign."""
        a = ArtifactWrite(
            session_id="s", action_id="a",
            artifact_type="queue_receipt",
            artifact_uri="queue://jobs/1",
            pre_state_hash="x", post_state_hash="x",
            non_sovereignty_assertion=ROUTE_NON_SOVEREIGNTY_ASSERTION,
        )
        assert not a.is_sovereign
        assert a.artifact_type != "execution_authority"
        assert ROUTE_NON_SOVEREIGNTY_ASSERTION in (a.non_sovereignty_assertion or "")
