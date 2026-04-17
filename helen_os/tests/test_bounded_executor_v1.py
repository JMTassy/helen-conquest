import json
from pathlib import Path

import pytest

from helen_os.executor.bounded_executor_v1 import (
    BoundedExecutor,
    FAILURE_CODES,
    EMPTY_STATE_HASH,
    compute_execution_identity,
    compute_file_hash,
    normalize_target,
    ExecutionDecisionReceipt,
    ExecutionResultReceipt,
    ArtifactWriteReceipt,
)
from helen_os.governance.canonical import sha256_prefixed, is_prefixed_sha256
from helen_os.governance.validators import validate_schema


@pytest.fixture()
def executor(tmp_path: Path) -> BoundedExecutor:
    return BoundedExecutor(base_dir=tmp_path, policy_version="v1")


def make_request(tool_type: str, target: str, payload: dict, pre_state_hash: str | None = None) -> dict:
    req = {"tool_type": tool_type, "target": target, "payload": payload}
    if pre_state_hash is not None:
        req["pre_state_hash"] = pre_state_hash
    return req


def test_failure_registry_contains_required_codes():
    required = {
        "invalid_target",
        "bounds_violation",
        "precondition_failed",
        "conflicting_pre_state",
        "duplicate_execution",
        "unsupported_handler",
        "artifact_write_failed",
        "receipt_emission_failed",
    }
    assert required.issubset(FAILURE_CODES)


def test_execution_identity_deterministic():
    ident1 = compute_execution_identity(
        tool_type="WRITE",
        normalized_target="a.txt",
        normalized_payload={"content": "hi"},
        pre_state_hash=EMPTY_STATE_HASH,
        policy_version="v1",
    )
    ident2 = compute_execution_identity(
        tool_type="WRITE",
        normalized_target="a.txt",
        normalized_payload={"content": "hi"},
        pre_state_hash=EMPTY_STATE_HASH,
        policy_version="v1",
    )
    assert ident1 == ident2


def test_execution_identity_changes_on_tool():
    base = dict(
        normalized_target="a.txt",
        normalized_payload={"content": "hi"},
        pre_state_hash=EMPTY_STATE_HASH,
        policy_version="v1",
    )
    ident1 = compute_execution_identity(tool_type="WRITE", **base)
    ident2 = compute_execution_identity(tool_type="EDIT", **base)
    assert ident1 != ident2


def test_execution_identity_changes_on_target():
    base = dict(
        tool_type="WRITE",
        normalized_payload={"content": "hi"},
        pre_state_hash=EMPTY_STATE_HASH,
        policy_version="v1",
    )
    ident1 = compute_execution_identity(normalized_target="a.txt", **base)
    ident2 = compute_execution_identity(normalized_target="b.txt", **base)
    assert ident1 != ident2


def test_execution_identity_changes_on_payload():
    base = dict(
        tool_type="WRITE",
        normalized_target="a.txt",
        pre_state_hash=EMPTY_STATE_HASH,
        policy_version="v1",
    )
    ident1 = compute_execution_identity(normalized_payload={"content": "hi"}, **base)
    ident2 = compute_execution_identity(normalized_payload={"content": "bye"}, **base)
    assert ident1 != ident2


def test_execution_identity_changes_on_pre_state():
    base = dict(
        tool_type="WRITE",
        normalized_target="a.txt",
        normalized_payload={"content": "hi"},
        policy_version="v1",
    )
    ident1 = compute_execution_identity(pre_state_hash=EMPTY_STATE_HASH, **base)
    ident2 = compute_execution_identity(pre_state_hash=sha256_prefixed({"x": 1}), **base)
    assert ident1 != ident2


def test_execution_identity_changes_on_policy_version():
    base = dict(
        tool_type="WRITE",
        normalized_target="a.txt",
        normalized_payload={"content": "hi"},
        pre_state_hash=EMPTY_STATE_HASH,
    )
    ident1 = compute_execution_identity(policy_version="v1", **base)
    ident2 = compute_execution_identity(policy_version="v2", **base)
    assert ident1 != ident2


def test_target_normalization_rejects_empty(tmp_path: Path):
    normalized, err = normalize_target(tmp_path, "")
    assert normalized is None
    assert err == "invalid_target"


def test_target_normalization_rejects_absolute(tmp_path: Path):
    normalized, err = normalize_target(tmp_path, "/abs/path.txt")
    assert normalized is None
    assert err == "bounds_violation"


def test_target_normalization_rejects_traversal(tmp_path: Path):
    normalized, err = normalize_target(tmp_path, "../secrets.txt")
    assert normalized is None
    assert err == "bounds_violation"


def test_target_normalization_normalizes(tmp_path: Path):
    normalized, err = normalize_target(tmp_path, "folder/file.txt")
    assert err is None
    assert normalized == "folder/file.txt"


def test_write_handler_rejects_existing_file(executor: BoundedExecutor, tmp_path: Path):
    path = tmp_path / "exists.txt"
    path.write_text("hi", encoding="utf-8")
    decision, result, artifact = executor.execute(make_request("WRITE", "exists.txt", {"content": "new"}))
    assert decision.decision == "REJECT"
    assert decision.failure_code == "bounds_violation"
    assert result.status == "FAILURE"
    assert artifact is None


def test_write_handler_writes_file(executor: BoundedExecutor, tmp_path: Path):
    decision, result, artifact = executor.execute(make_request("WRITE", "file.txt", {"content": "hello"}))
    assert decision.decision == "ALLOW"
    assert (tmp_path / "file.txt").read_text(encoding="utf-8") == "hello"
    assert result.status == "SUCCESS"
    assert artifact is not None


def test_write_handler_artifact_receipt(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("WRITE", "artifact.txt", {"content": "data"}))
    assert isinstance(artifact, ArtifactWriteReceipt)
    assert artifact.execution_id_ref == result.execution_id


def test_write_handler_post_state_hash_matches_file(executor: BoundedExecutor, tmp_path: Path):
    decision, result, artifact = executor.execute(make_request("WRITE", "hash.txt", {"content": "hashme"}))
    file_hash = compute_file_hash(tmp_path / "hash.txt")
    assert result.post_state_hash == file_hash


def test_edit_handler_rejects_missing_file(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("EDIT", "missing.txt", {"content": "x"}, pre_state_hash=EMPTY_STATE_HASH))
    assert decision.decision == "REJECT"
    assert decision.failure_code == "invalid_target"


def test_edit_handler_rejects_pre_state_mismatch(executor: BoundedExecutor, tmp_path: Path):
    path = tmp_path / "edit.txt"
    path.write_text("old", encoding="utf-8")
    bad_hash = sha256_prefixed({"bad": True})
    decision, result, artifact = executor.execute(make_request("EDIT", "edit.txt", {"content": "new"}, pre_state_hash=bad_hash))
    assert decision.decision == "REJECT"
    assert decision.failure_code == "conflicting_pre_state"


def test_edit_handler_updates_file(executor: BoundedExecutor, tmp_path: Path):
    path = tmp_path / "edit2.txt"
    path.write_text("old", encoding="utf-8")
    pre_hash = compute_file_hash(path)
    decision, result, artifact = executor.execute(make_request("EDIT", "edit2.txt", {"content": "new"}, pre_state_hash=pre_hash))
    assert decision.decision == "ALLOW"
    assert (tmp_path / "edit2.txt").read_text(encoding="utf-8") == "new"
    assert result.status == "SUCCESS"


def test_edit_handler_post_state_hash_matches_file(executor: BoundedExecutor, tmp_path: Path):
    path = tmp_path / "edit3.txt"
    path.write_text("old", encoding="utf-8")
    pre_hash = compute_file_hash(path)
    decision, result, artifact = executor.execute(make_request("EDIT", "edit3.txt", {"content": "new"}, pre_state_hash=pre_hash))
    file_hash = compute_file_hash(tmp_path / "edit3.txt")
    assert result.post_state_hash == file_hash


def test_analyze_handler_no_file_write(executor: BoundedExecutor, tmp_path: Path):
    decision, result, artifact = executor.execute(make_request("ANALYZE", "analysis.txt", {"query": "x"}))
    assert decision.decision == "ALLOW"
    assert result.status == "SUCCESS"
    assert not (tmp_path / "analysis.txt").exists()
    assert artifact is None


def test_route_handler_no_file_write(executor: BoundedExecutor, tmp_path: Path):
    decision, result, artifact = executor.execute(make_request("ROUTE", "route.txt", {"route": "KERNEL"}))
    assert decision.decision == "ALLOW"
    assert result.status == "SUCCESS"
    assert not (tmp_path / "route.txt").exists()
    assert artifact is None


def test_executor_rejects_unknown_handler(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("UNKNOWN", "x.txt", {"content": "x"}))
    assert decision.decision == "REJECT"
    assert decision.failure_code == "unsupported_handler"
    assert result.status == "FAILURE"


def test_executor_duplicate_execution_identity(executor: BoundedExecutor):
    req = make_request("ANALYZE", "dup.txt", {"query": "hi"})
    executor.execute(req)
    second = executor.execute(req)
    assert second[0].failure_code == "duplicate_execution"


def test_decision_receipt_schema_valid(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("WRITE", "schema.txt", {"content": "hi"}))
    ok, err = validate_schema("EXECUTION_DECISION_V1", "1.0.0", decision.__dict__)
    assert ok, err


def test_result_receipt_schema_valid(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("WRITE", "schema2.txt", {"content": "hi"}))
    ok, err = validate_schema("EXECUTION_RESULT_V1", "1.0.0", result.__dict__)
    assert ok, err


def test_artifact_receipt_schema_valid(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("WRITE", "schema3.txt", {"content": "hi"}))
    ok, err = validate_schema("ARTIFACT_WRITE_V1", "1.0.0", artifact.__dict__)
    assert ok, err


def test_decision_receipt_includes_execution_identity(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("WRITE", "id.txt", {"content": "hi"}))
    assert is_prefixed_sha256(decision.execution_identity)


def test_result_receipt_includes_execution_identity(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("WRITE", "id2.txt", {"content": "hi"}))
    assert result.execution_identity == decision.execution_identity


def test_result_receipt_references_decision(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("WRITE", "ref.txt", {"content": "hi"}))
    assert result.decision_id_ref == decision.decision_id


def test_artifact_receipt_references_execution(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("WRITE", "ref2.txt", {"content": "hi"}))
    assert artifact.execution_id_ref == result.execution_id


def test_write_decision_allow(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("WRITE", "allow.txt", {"content": "hi"}))
    assert decision.decision == "ALLOW"


def test_edit_decision_allow(executor: BoundedExecutor, tmp_path: Path):
    path = tmp_path / "allow_edit.txt"
    path.write_text("old", encoding="utf-8")
    pre_hash = compute_file_hash(path)
    decision, result, artifact = executor.execute(make_request("EDIT", "allow_edit.txt", {"content": "new"}, pre_state_hash=pre_hash))
    assert decision.decision == "ALLOW"


def test_analyze_decision_allow(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("ANALYZE", "noop.txt", {"query": "x"}))
    assert decision.decision == "ALLOW"


def test_route_decision_allow(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("ROUTE", "noop2.txt", {"route": "KERNEL"}))
    assert decision.decision == "ALLOW"


def test_edit_requires_pre_state_hash(executor: BoundedExecutor, tmp_path: Path):
    path = tmp_path / "needs_hash.txt"
    path.write_text("old", encoding="utf-8")
    decision, result, artifact = executor.execute(make_request("EDIT", "needs_hash.txt", {"content": "new"}))
    assert decision.decision == "REJECT"
    assert decision.failure_code == "precondition_failed"


def test_write_uses_empty_pre_state_hash(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("WRITE", "pre.txt", {"content": "x"}))
    assert decision.pre_state_hash == EMPTY_STATE_HASH


def test_reject_returns_failure_code(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("UNKNOWN", "x.txt", {"content": "x"}))
    assert decision.failure_code in FAILURE_CODES


def test_execution_result_failure_when_handler_fails(executor: BoundedExecutor, tmp_path: Path):
    path = tmp_path / "fail.txt"
    path.write_text("old", encoding="utf-8")
    bad_hash = sha256_prefixed({"bad": True})
    decision, result, artifact = executor.execute(make_request("EDIT", "fail.txt", {"content": "new"}, pre_state_hash=bad_hash))
    assert result.status == "FAILURE"
    assert result.failure_code == "conflicting_pre_state"


def test_artifact_write_receipt_sha256_prefixed(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("WRITE", "hashpref.txt", {"content": "x"}))
    assert artifact.sha256.startswith("sha256:")


def test_payload_hash_matches_expected(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("WRITE", "payload.txt", {"content": "x"}))
    expected = sha256_prefixed({"content": "x"})
    assert decision.normalized_payload_sha256 == expected


def test_output_hash_is_prefixed(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("ANALYZE", "out.txt", {"query": "x"}))
    assert result.output_sha256.startswith("sha256:")


def test_artifact_bytes_match_content(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("WRITE", "bytes.txt", {"content": "hello"}))
    assert artifact.bytes == len("hello".encode("utf-8"))


def test_result_artifact_refs_for_write(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("WRITE", "refs.txt", {"content": "x"}))
    assert result.artifact_refs == [artifact.artifact_id]


def test_result_artifact_refs_empty_for_analyze(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("ANALYZE", "refs2.txt", {"query": "x"}))
    assert result.artifact_refs == []


def test_result_post_state_hash_none_for_analyze(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("ANALYZE", "refs3.txt", {"query": "x"}))
    assert result.post_state_hash is None


def test_result_post_state_hash_none_for_route(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("ROUTE", "refs4.txt", {"route": "KERNEL"}))
    assert result.post_state_hash is None


def test_schema_validation_for_reject_receipt(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("UNKNOWN", "x.txt", {"content": "x"}))
    ok, err = validate_schema("EXECUTION_DECISION_V1", "1.0.0", decision.__dict__)
    assert ok, err


def test_execution_identity_is_prefixed(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("WRITE", "idpref.txt", {"content": "x"}))
    assert decision.execution_identity.startswith("sha256:")


def test_pre_state_hash_prefixed_for_edit(executor: BoundedExecutor, tmp_path: Path):
    path = tmp_path / "pref_edit.txt"
    path.write_text("old", encoding="utf-8")
    pre_hash = compute_file_hash(path)
    decision, result, artifact = executor.execute(make_request("EDIT", "pref_edit.txt", {"content": "new"}, pre_state_hash=pre_hash))
    assert decision.pre_state_hash.startswith("sha256:")


def test_normalized_target_in_receipts(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("WRITE", "folder/norm.txt", {"content": "x"}))
    assert decision.normalized_target == "folder/norm.txt"


def test_decision_and_result_separation(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("WRITE", "sep.txt", {"content": "x"}))
    assert isinstance(decision, ExecutionDecisionReceipt)
    assert isinstance(result, ExecutionResultReceipt)


def test_artifact_receipt_separation(executor: BoundedExecutor):
    decision, result, artifact = executor.execute(make_request("WRITE", "sep2.txt", {"content": "x"}))
    assert isinstance(artifact, ArtifactWriteReceipt)
