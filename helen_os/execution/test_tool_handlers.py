"""Tests for Stage B.1 tool handlers.

Covers:
  - WriteFileHandler  (12 tests)
  - EditFileHandler   (10 tests)
  - AnalyzeHandler    (8 tests)
  - RouteHandler      (8 tests)
  - 3-receipt spine enforcement (4 cross-handler tests)
  - Idempotence (5 tests)
  - Interrupt / replay (3 tests)

Total target: 50 tests
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import pytest

from helen_os.execution.types import (
    ArtifactWrite,
    ExecutionDecision,
    ExecutionResult,
    HandlerFailure,
    IdempotenceStatus,
    ReceiptRole,
    ROUTE_NON_SOVEREIGNTY_ASSERTION,
    TransitionStatus,
    _jcs,
    compute_exec_key,
    compute_state_hash,
)
from helen_os.execution.tool_handlers import (
    AnalyzeHandler,
    EditFileHandler,
    HandlerResult,
    IdempotenceRegistry,
    RouteHandler,
    WriteFileHandler,
    _HandlerExecutionError,
)


# ─── Fixtures ──────────────────────────────────────────────────────────────────

SESSION = {"user": "helen", "run_id": "test-run-001"}
ACTION_ID = "act-001"
SESSION_ID = "sess-001"


def _run_write(tmp_path: Path, content: str, filename: str = "out.txt", registry=None) -> HandlerResult:
    target = str(tmp_path / filename)
    h = WriteFileHandler(registry=registry)
    return h.run(
        action_id=ACTION_ID,
        session_id=SESSION_ID,
        target=target,
        payload={"content": content},
        session_state=SESSION,
    )


def _run_edit(tmp_path: Path, filename: str, payload: dict, registry=None) -> HandlerResult:
    target = str(tmp_path / filename)
    h = EditFileHandler(registry=registry)
    return h.run(
        action_id=ACTION_ID,
        session_id=SESSION_ID,
        target=target,
        payload=payload,
        session_state=SESSION,
    )


def _run_analyze(tmp_path: Path, filename: str, metric: str = "all", registry=None) -> HandlerResult:
    target = str(tmp_path / filename)
    h = AnalyzeHandler(registry=registry)
    return h.run(
        action_id=ACTION_ID,
        session_id=SESSION_ID,
        target=target,
        payload={"metric": metric},
        session_state=SESSION,
    )


def _run_route(destination: str, message: dict, registry=None) -> HandlerResult:
    h = RouteHandler(registry=registry)
    return h.run(
        action_id=ACTION_ID,
        session_id=SESSION_ID,
        target=f"/queues/{destination}",
        payload={"destination": destination, "message": message},
        session_state=SESSION,
    )


# ─── Spine law helper ──────────────────────────────────────────────────────────

def assert_spine(result: HandlerResult) -> None:
    """Assert the 3-receipt spine is structurally intact."""
    d, e, a = result.spine
    assert isinstance(d, ExecutionDecision), "spine[0] must be ExecutionDecision"
    assert isinstance(e, ExecutionResult), "spine[1] must be ExecutionResult"
    assert isinstance(a, ArtifactWrite), "spine[2] must be ArtifactWrite"
    # Sovereignty invariant
    assert not d.is_sovereign
    assert not e.is_sovereign
    assert not a.is_sovereign
    # Roles
    assert d.receipt_role == ReceiptRole.AUTHORIZATION
    assert e.receipt_role in (ReceiptRole.WITNESS_ATTEMPT, ReceiptRole.WITNESS_NOOP)
    assert a.receipt_role in (ReceiptRole.WITNESS_ARTIFACT, ReceiptRole.WITNESS_NOOP)
    # Confidence invariant
    assert d.confidence is None


# ─── WriteFileHandler ──────────────────────────────────────────────────────────

class TestWriteFileHandler:

    def test_WF_01_creates_new_file(self, tmp_path):
        result = _run_write(tmp_path, "hello helen")
        assert result.success
        assert (tmp_path / "out.txt").read_text() == "hello helen"

    def test_WF_02_spine_intact_on_success(self, tmp_path):
        result = _run_write(tmp_path, "spine test")
        assert_spine(result)

    def test_WF_03_artifact_hash_matches_content(self, tmp_path):
        content = "canonical content"
        result = _run_write(tmp_path, content)
        expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        assert result.artifact_receipt.artifact_hash == expected_hash

    def test_WF_04_pre_post_state_differ_on_write(self, tmp_path):
        result = _run_write(tmp_path, "state change test")
        assert result.state_transition.pre_state_hash != result.state_transition.post_state_hash

    def test_WF_05_transition_status_verified(self, tmp_path):
        result = _run_write(tmp_path, "verified")
        assert result.state_transition.transition_status == TransitionStatus.VERIFIED

    def test_WF_06_overwrites_existing_file(self, tmp_path):
        (tmp_path / "out.txt").write_text("old content")
        result = _run_write(tmp_path, "new content")
        assert result.success
        assert (tmp_path / "out.txt").read_text() == "new content"

    def test_WF_07_decision_phase_fail_missing_content_key(self, tmp_path):
        target = str(tmp_path / "out.txt")
        h = WriteFileHandler()
        result = h.run(
            action_id=ACTION_ID, session_id=SESSION_ID,
            target=target, payload={}, session_state=SESSION,
        )
        assert result.execution_receipt.status == "FAILED"
        assert result.execution_receipt.error_code == HandlerFailure.INVALID_PAYLOAD.value
        assert_spine(result)

    def test_WF_08_decision_phase_fail_content_not_string(self, tmp_path):
        target = str(tmp_path / "out.txt")
        h = WriteFileHandler()
        result = h.run(
            action_id=ACTION_ID, session_id=SESSION_ID,
            target=target, payload={"content": 42}, session_state=SESSION,
        )
        assert result.execution_receipt.status == "FAILED"
        assert_spine(result)

    def test_WF_09_decision_phase_fail_nonexistent_parent(self, tmp_path):
        target = str(tmp_path / "nonexistent_dir" / "out.txt")
        h = WriteFileHandler()
        result = h.run(
            action_id=ACTION_ID, session_id=SESSION_ID,
            target=target, payload={"content": "x"}, session_state=SESSION,
        )
        assert result.execution_receipt.status == "FAILED"
        assert_spine(result)

    def test_WF_10_exec_key_is_deterministic(self, tmp_path):
        target = str(tmp_path / "det.txt")
        payload = {"content": "determinism"}
        pre = compute_state_hash(session_state=SESSION)
        k1 = compute_exec_key(tool_type="WRITE_FILE", normalized_target=target, payload=payload, pre_state_hash=pre)
        k2 = compute_exec_key(tool_type="WRITE_FILE", normalized_target=target, payload=payload, pre_state_hash=pre)
        assert k1 == k2

    def test_WF_11_different_pre_state_different_exec_key(self, tmp_path):
        target = str(tmp_path / "det.txt")
        payload = {"content": "same content"}
        k1 = compute_exec_key(tool_type="WRITE_FILE", normalized_target=target, payload=payload, pre_state_hash="aaa")
        k2 = compute_exec_key(tool_type="WRITE_FILE", normalized_target=target, payload=payload, pre_state_hash="bbb")
        assert k1 != k2

    def test_WF_12_artifact_uri_correct(self, tmp_path):
        result = _run_write(tmp_path, "uri test")
        expected = f"file://{tmp_path / 'out.txt'}"
        assert result.artifact_receipt.artifact_uri == expected


# ─── EditFileHandler ───────────────────────────────────────────────────────────

class TestEditFileHandler:

    def test_EF_01_append_mode(self, tmp_path):
        (tmp_path / "file.txt").write_text("line1\n")
        result = _run_edit(tmp_path, "file.txt", {"mode": "append", "content": "line2\n"})
        assert result.success
        assert (tmp_path / "file.txt").read_text() == "line1\nline2\n"

    def test_EF_02_replace_mode(self, tmp_path):
        (tmp_path / "file.txt").write_text("hello world")
        result = _run_edit(tmp_path, "file.txt", {"mode": "replace", "content": "goodbye", "old_string": "hello"})
        assert result.success
        assert (tmp_path / "file.txt").read_text() == "goodbye world"

    def test_EF_03_spine_intact(self, tmp_path):
        (tmp_path / "file.txt").write_text("data")
        result = _run_edit(tmp_path, "file.txt", {"mode": "append", "content": " more"})
        assert_spine(result)

    def test_EF_04_missing_file_fails_execution_phase(self, tmp_path):
        result = _run_edit(tmp_path, "missing.txt", {"mode": "append", "content": "x"})
        assert result.execution_receipt.status == "FAILED"
        assert result.execution_receipt.error_code == HandlerFailure.TARGET_NOT_FOUND.value
        assert_spine(result)

    def test_EF_05_invalid_mode_fails_decision(self, tmp_path):
        (tmp_path / "file.txt").write_text("x")
        result = _run_edit(tmp_path, "file.txt", {"mode": "delete", "content": "x"})
        assert result.execution_receipt.status == "FAILED"
        assert result.execution_receipt.error_code == HandlerFailure.INVALID_PAYLOAD.value

    def test_EF_06_replace_old_string_not_found_fails(self, tmp_path):
        (tmp_path / "file.txt").write_text("hello world")
        result = _run_edit(tmp_path, "file.txt", {"mode": "replace", "content": "x", "old_string": "nothere"})
        assert result.execution_receipt.status == "FAILED"
        # old_string not in file = pre-state conflict (EXECUTION phase)
        assert result.execution_receipt.error_code == HandlerFailure.CONFLICTING_PRE_STATE.value

    def test_EF_07_replace_missing_old_string_key_fails(self, tmp_path):
        (tmp_path / "file.txt").write_text("x")
        result = _run_edit(tmp_path, "file.txt", {"mode": "replace", "content": "y"})
        assert result.execution_receipt.status == "FAILED"
        assert result.execution_receipt.error_code == HandlerFailure.INVALID_PAYLOAD.value

    def test_EF_08_post_state_differs_from_pre(self, tmp_path):
        (tmp_path / "file.txt").write_text("original")
        result = _run_edit(tmp_path, "file.txt", {"mode": "append", "content": " appended"})
        assert result.state_transition.pre_state_hash != result.state_transition.post_state_hash

    def test_EF_09_artifact_hash_matches_new_content(self, tmp_path):
        (tmp_path / "file.txt").write_text("base")
        result = _run_edit(tmp_path, "file.txt", {"mode": "append", "content": "_ext"})
        expected = hashlib.sha256("base_ext".encode("utf-8")).hexdigest()
        assert result.artifact_receipt.artifact_hash == expected

    def test_EF_10_spine_intact_on_failure(self, tmp_path):
        result = _run_edit(tmp_path, "ghost.txt", {"mode": "append", "content": "x"})
        assert_spine(result)


# ─── AnalyzeHandler ────────────────────────────────────────────────────────────

class TestAnalyzeHandler:

    def test_AN_01_line_count(self, tmp_path):
        (tmp_path / "data.txt").write_text("a\nb\nc\n")
        result = _run_analyze(tmp_path, "data.txt", metric="line_count")
        assert result.success
        assert result.output_data["line_count"] == 3

    def test_AN_02_char_count(self, tmp_path):
        (tmp_path / "data.txt").write_text("hello")
        result = _run_analyze(tmp_path, "data.txt", metric="char_count")
        assert result.output_data["char_count"] == 5

    def test_AN_03_word_count(self, tmp_path):
        (tmp_path / "data.txt").write_text("one two three")
        result = _run_analyze(tmp_path, "data.txt", metric="word_count")
        assert result.output_data["word_count"] == 3

    def test_AN_04_hash_metric(self, tmp_path):
        content = "hash me"
        (tmp_path / "data.txt").write_text(content)
        result = _run_analyze(tmp_path, "data.txt", metric="hash")
        expected = hashlib.sha256(content.encode()).hexdigest()
        assert result.output_data["sha256"] == expected

    def test_AN_05_post_state_equals_pre_state(self, tmp_path):
        """Non-mutating: state must not change."""
        (tmp_path / "data.txt").write_text("read only")
        result = _run_analyze(tmp_path, "data.txt")
        assert result.state_transition.pre_state_hash == result.state_transition.post_state_hash

    def test_AN_06_file_not_modified_after_analyze(self, tmp_path):
        content = "unchanged"
        (tmp_path / "data.txt").write_text(content)
        _run_analyze(tmp_path, "data.txt")
        assert (tmp_path / "data.txt").read_text() == content

    def test_AN_07_missing_target_fails_execution(self, tmp_path):
        result = _run_analyze(tmp_path, "ghost.txt")
        assert result.execution_receipt.status == "FAILED"
        assert result.execution_receipt.error_code == HandlerFailure.TARGET_NOT_FOUND.value

    def test_AN_08_spine_intact(self, tmp_path):
        (tmp_path / "data.txt").write_text("x")
        result = _run_analyze(tmp_path, "data.txt")
        assert_spine(result)


# ─── RouteHandler ──────────────────────────────────────────────────────────────

class TestRouteHandler:

    def test_RT_01_emits_queue_receipt(self):
        result = _run_route("task_queue", {"task": "build"})
        assert result.success
        assert result.artifact_receipt.artifact_type == "queue_receipt"

    def test_RT_02_non_sovereignty_assertion_present(self):
        result = _run_route("task_queue", {"task": "build"})
        assert result.artifact_receipt.non_sovereignty_assertion == ROUTE_NON_SOVEREIGNTY_ASSERTION

    def test_RT_03_post_state_equals_pre_state(self):
        """ROUTE does not mutate local state."""
        result = _run_route("task_queue", {"task": "noop"})
        assert result.state_transition.pre_state_hash == result.state_transition.post_state_hash

    def test_RT_04_missing_destination_fails_decision(self):
        h = RouteHandler()
        result = h.run(
            action_id=ACTION_ID, session_id=SESSION_ID,
            target="/queues/test", payload={"message": {"x": 1}}, session_state=SESSION,
        )
        assert result.execution_receipt.status == "FAILED"
        assert result.execution_receipt.error_code == HandlerFailure.INVALID_PAYLOAD.value

    def test_RT_05_missing_message_fails_decision(self):
        h = RouteHandler()
        result = h.run(
            action_id=ACTION_ID, session_id=SESSION_ID,
            target="/queues/test", payload={"destination": "q"}, session_state=SESSION,
        )
        assert result.execution_receipt.status == "FAILED"

    def test_RT_06_non_string_message_fails_decision(self):
        h = RouteHandler()
        result = h.run(
            action_id=ACTION_ID, session_id=SESSION_ID,
            target="/queues/test", payload={"destination": "q", "message": "not a dict"}, session_state=SESSION,
        )
        assert result.execution_receipt.status == "FAILED"

    def test_RT_07_spine_intact(self):
        result = _run_route("q", {"data": "x"})
        assert_spine(result)

    def test_RT_08_advisory_only_status_in_output(self):
        result = _run_route("q", {"data": "x"})
        assert result.output_data.get("status") == "advisory_only"


# ─── 3-receipt spine law ───────────────────────────────────────────────────────

class TestSpineLaw:

    def test_SP_01_write_spine_order_is_decision_result_artifact(self, tmp_path):
        result = _run_write(tmp_path, "x")
        d, e, a = result.spine
        assert d.receipt_type == "EXECUTION_DECISION"
        assert e.receipt_type == "EXECUTION_RESULT"
        assert a.receipt_type == "ARTIFACT_WRITE"

    def test_SP_02_analyze_spine_complete_on_success(self, tmp_path):
        (tmp_path / "f.txt").write_text("data")
        result = _run_analyze(tmp_path, "f.txt")
        assert len(result.spine) == 3

    def test_SP_03_route_spine_complete(self):
        result = _run_route("q", {"k": "v"})
        assert len(result.spine) == 3

    def test_SP_04_all_spine_receipts_non_sovereign(self, tmp_path):
        (tmp_path / "f.txt").write_text("x")
        for result in [
            _run_write(tmp_path, "data", "w.txt"),
            _run_edit(tmp_path, "f.txt", {"mode": "append", "content": "y"}),
            _run_analyze(tmp_path, "f.txt"),
            _run_route("q", {"k": "v"}),
        ]:
            for receipt in result.spine:
                assert not receipt.is_sovereign, f"{type(receipt).__name__} must never be sovereign"


# ─── Idempotence ───────────────────────────────────────────────────────────────

class TestIdempotence:
    """Idempotence tests use AnalyzeHandler (non-mutating).

    WriteFileHandler correctly generates a NEW ExecKey after a successful write
    because the file's pre-state changes (file now exists with mtime/size).
    AnalyzeHandler is non-mutating: pre_state_hash stays identical between
    calls so the ExecKey matches and DUPLICATE is correctly detected.
    """

    def test_ID_01_second_analyze_returns_duplicate(self, tmp_path):
        (tmp_path / "data.txt").write_text("stable content")
        reg = IdempotenceRegistry()
        _run_analyze(tmp_path, "data.txt", registry=reg)
        result2 = _run_analyze(tmp_path, "data.txt", registry=reg)
        assert result2.idempotence_status == IdempotenceStatus.DUPLICATE

    def test_ID_02_duplicate_emits_noop_artifact(self, tmp_path):
        (tmp_path / "data.txt").write_text("stable")
        reg = IdempotenceRegistry()
        _run_analyze(tmp_path, "data.txt", registry=reg)
        result2 = _run_analyze(tmp_path, "data.txt", registry=reg)
        assert result2.artifact_receipt.receipt_type == "ARTIFACT_NOOP"

    def test_ID_03_duplicate_spine_has_witness_noop_role(self, tmp_path):
        (tmp_path / "data.txt").write_text("stable")
        reg = IdempotenceRegistry()
        _run_analyze(tmp_path, "data.txt", registry=reg)
        result2 = _run_analyze(tmp_path, "data.txt", registry=reg)
        assert result2.artifact_receipt.receipt_role == ReceiptRole.WITNESS_NOOP

    def test_ID_04_different_targets_are_each_new(self, tmp_path):
        (tmp_path / "a.txt").write_text("alpha")
        (tmp_path / "b.txt").write_text("beta")
        reg = IdempotenceRegistry()
        _run_analyze(tmp_path, "a.txt", registry=reg)
        result_b = _run_analyze(tmp_path, "b.txt", registry=reg)
        assert result_b.idempotence_status == IdempotenceStatus.NEW

    def test_ID_05_registry_clear_allows_rerun(self, tmp_path):
        (tmp_path / "data.txt").write_text("stable")
        reg = IdempotenceRegistry()
        _run_analyze(tmp_path, "data.txt", registry=reg)
        reg.clear()
        result = _run_analyze(tmp_path, "data.txt", registry=reg)
        assert result.idempotence_status == IdempotenceStatus.NEW


# ─── Interrupt / replay ────────────────────────────────────────────────────────

class TestInterruptReplay:

    def test_IR_01_exec_key_stable_across_restarts(self, tmp_path):
        """Same inputs → same ExecKey regardless of when computed."""
        target = str(tmp_path / "stable.txt")
        payload = {"content": "replay me"}
        pre = compute_state_hash(session_state=SESSION)
        keys = [
            compute_exec_key(tool_type="WRITE_FILE", normalized_target=target, payload=payload, pre_state_hash=pre)
            for _ in range(5)
        ]
        assert len(set(keys)) == 1

    def test_IR_02_replay_with_prior_registry_skips(self, tmp_path):
        """If registry survives restart, duplicate is detected correctly.

        Uses AnalyzeHandler: non-mutating, so pre_state_hash is identical
        on retry (file unchanged) → ExecKey matches → DUPLICATE detected.
        """
        (tmp_path / "file.txt").write_text("stable")
        reg = IdempotenceRegistry()
        first = _run_analyze(tmp_path, "file.txt", registry=reg)
        assert first.idempotence_status == IdempotenceStatus.NEW
        # Simulated restart: same registry object passed again
        second = _run_analyze(tmp_path, "file.txt", registry=reg)
        assert second.idempotence_status == IdempotenceStatus.DUPLICATE

    def test_IR_03_spine_intact_on_duplicate(self, tmp_path):
        (tmp_path / "file.txt").write_text("x")
        reg = IdempotenceRegistry()
        _run_analyze(tmp_path, "file.txt", registry=reg)
        result = _run_analyze(tmp_path, "file.txt", registry=reg)
        assert_spine(result)
