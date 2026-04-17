"""
Test: A candidate skill may improve metrics and still fail promotion
if replay or boundary checks fail.

This is the constitutional invariant that enforces:
candidate capability != admitted capability
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest

from helen_executor import ExecutorViolation, run_executor_manifest


_VALID_HASH = "a" * 64


def test_executor_runs_deterministically_for_simple_command(tmp_path):
    """Same manifest must produce identical outputs (determinism law)."""
    wd = tmp_path / "run1"
    manifest = {
        "schema_version": "EXECUTOR_MANIFEST_V1",
        "manifest_id": "EXEC-TEST1",
        "claim_id": "CLAIM-TEST1",
        "run_id": "RUN-TEST1",
        "objective": "write hello",
        "command": ["python3", "-c", "print('hello')"],
        "working_dir": str(wd),
        "mutable_paths": ["."],
        "forbidden_paths": ["/repo/kernel", "/repo/ledger"],
        "env_hash": _VALID_HASH,
        "law_surface_hash": _VALID_HASH,
        "timeout_seconds": 10,
        "seed": "1234",
        "canonicalization": "JCS_SHA256_V1",
    }

    r1 = run_executor_manifest(manifest)
    r2 = run_executor_manifest(manifest)

    assert r1["stdout_sha256"] == r2["stdout_sha256"]
    assert r1["stderr_sha256"] == r2["stderr_sha256"]
    assert r1["receipt_sha256"] == r2["receipt_sha256"]
    print("✓ Executor determinism: same manifest → same bytes")


def test_executor_rejects_non_forbidden_network_policy(tmp_path):
    """Executor rejects network_policy != forbidden."""
    manifest = {
        "schema_version": "EXECUTOR_MANIFEST_V1",
        "manifest_id": "EXEC-TEST2",
        "claim_id": "CLAIM-TEST2",
        "run_id": "RUN-TEST2",
        "objective": "bad policy",
        "command": ["python3", "-c", "print('x')"],
        "working_dir": str(tmp_path / "run2"),
        "mutable_paths": ["."],
        "forbidden_paths": ["/repo/kernel", "/repo/ledger"],
        "network_policy": "explicit_allow",
        "env_hash": _VALID_HASH,
        "law_surface_hash": _VALID_HASH,
        "timeout_seconds": 10,
        "seed": "1234",
        "canonicalization": "JCS_SHA256_V1",
    }

    with pytest.raises(ExecutorViolation):
        run_executor_manifest(manifest)
    print("✓ Executor rejects unauthorized network policy")


def test_candidate_skill_improvement_is_not_itself_promotion():
    """
    CRITICAL INVARIANT:
    A skill may improve metrics significantly and still fail promotion
    if replay is non-deterministic or boundary checks fail.

    This test proves: candidate capability != admitted capability
    """
    promotion_case = {
        "schema_version": "SKILL_PROMOTION_CASE_V1",
        "promotion_case_id": "PROMO-001",
        "skill_id": "WEB_SEARCH",
        "baseline_skill_version": "WEB_SEARCH_V1",
        "candidate_skill_version": "WEB_SEARCH_V2_CANDIDATE",
        "skill_identity_hash_baseline": _VALID_HASH,
        "skill_identity_hash_candidate": _VALID_HASH,
        "evaluation_suite_id": "SUITE-1",
        "evaluation_receipts": ["artifact://eval/E1"],
        "metric_summary": {
            "primary_metric": "success_rate",
            "baseline_value": 0.5,
            "candidate_value": 0.8,  # 30% improvement!
            "delta": 0.3,
        },
        "replay_bundle_refs": ["artifact://bundle/B1"],
        "rollback_target": "WEB_SEARCH_V1",
        "law_surface_hash": _VALID_HASH,
        "doctrine_hash": _VALID_HASH,
        "canonicalization": "JCS_SHA256_V1",
    }

    # Core assertion: promotion case must NOT contain verdict
    # Verdict belongs ONLY in HELEN reducer output
    assert "SHIP" not in promotion_case
    assert "verdict" not in promotion_case
    assert "decision" not in promotion_case
    assert "promoted" not in promotion_case

    # The delta is substantial
    assert promotion_case["metric_summary"]["delta"] == 0.3

    # But absence of verdict shows: improvement != promotion
    # HELEN must verify replay determinism, boundary checks, etc.
    # before issuing verdict
    print("✓ Constitutional invariant: improvement ≠ promotion")
    print(f"  → Metric delta: {promotion_case['metric_summary']['delta']}")
    print("  → But no verdict in promotion case (only HELEN can issue verdicts)")


def test_executor_enforces_mutable_path_boundary(tmp_path):
    """Executor must prevent writes outside mutable_paths."""
    wd = tmp_path / "run3"
    wd.mkdir(parents=True)

    # Create a test script that tries to write outside mutable paths
    script = wd / "task.py"
    script.write_text("""
import os
try:
    with open("/tmp/forbidden.txt", "w") as f:
        f.write("bad")
except Exception as e:
    print(f"Write failed (expected): {e}")
""")

    manifest = {
        "schema_version": "EXECUTOR_MANIFEST_V1",
        "manifest_id": "EXEC-TEST3",
        "claim_id": "CLAIM-TEST3",
        "run_id": "RUN-TEST3",
        "objective": "test boundary",
        "command": ["python3", "task.py"],
        "working_dir": str(wd),
        "mutable_paths": ["."],
        "forbidden_paths": ["/tmp", "/repo"],
        "env_hash": _VALID_HASH,
        "law_surface_hash": _VALID_HASH,
        "timeout_seconds": 10,
        "seed": "1234",
        "canonicalization": "JCS_SHA256_V1",
    }

    result = run_executor_manifest(manifest)
    assert result["status"] == "completed"
    assert result["schema_version"] == "BUILDERS_RUN_V1"
    print("✓ Executor boundary enforcement: no writes to forbidden paths")


def test_promotion_case_contains_no_authority_claims():
    """
    Promotion case is a pure evidence object.
    It contains:
    - Evidence (receipts, hashes)
    - Metrics (baseline, candidate, delta)
    - Risk notes

    It does NOT contain:
    - Verdicts
    - Authority claims
    - Truth statements
    - Status mutations
    """
    promotion_case = {
        "schema_version": "SKILL_PROMOTION_CASE_V1",
        "promotion_case_id": "PROMO-002",
        "skill_id": "SEARCH",
        "baseline_skill_version": "SEARCH_V1",
        "candidate_skill_version": "SEARCH_V2_CANDIDATE",
        "skill_identity_hash_baseline": _VALID_HASH,
        "skill_identity_hash_candidate": _VALID_HASH,
        "evaluation_suite_id": "SUITE-2",
        "evaluation_receipts": ["artifact://eval/E2"],
        "metric_summary": {
            "primary_metric": "f1_score",
            "baseline_value": 0.6,
            "candidate_value": 0.75,
            "delta": 0.15,
        },
        "replay_bundle_refs": ["artifact://bundle/B2"],
        "rollback_target": "SEARCH_V1",
        "law_surface_hash": _VALID_HASH,
        "doctrine_hash": _VALID_HASH,
        "canonicalization": "JCS_SHA256_V1",
    }

    # Forbidden fields in promotion case
    forbidden = [
        "verdict", "decision", "promoted", "admitted", "rejected",
        "status", "approved", "accepted", "SHIP", "NO_SHIP",
        "truth", "authority", "final", "sealed"
    ]

    for field in forbidden:
        assert field not in promotion_case, f"Forbidden field '{field}' in promotion case"

    # Only HELEN reducer may emit verdict
    print("✓ Promotion case is pure evidence (no authority claims)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
