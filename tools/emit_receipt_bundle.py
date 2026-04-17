#!/usr/bin/env python3
"""
CI Receipt Bundle Emitter

This script runs after tests complete and produces a CIReceiptBundle artifact.

Workflow:
1. Run test commands (pytest, dependency checks)
2. Capture exit codes + stdout/stderr hashes
3. Derive attestations from executions (PASS/FAIL only, no opinions)
4. Build receipt bundle with full provenance
5. Validate against ci_receipt_bundle.schema.json (fail-closed)
6. Write to artifacts/receipt_bundle.json
7. Append reference to ledger (artifacts/ledger.jsonl)
8. Verify ledger chain integrity
9. Fail CI run if any execution failed (fail-closed)

Usage:
    python tools/emit_receipt_bundle.py

Environment Variables (optional):
    RUN_ID: Run identifier (default: RUN-local)
    BRIEFCASE_ID: Briefcase identifier (default: BFC-UNKNOWN)
    REPO_ORIGIN: Repository origin URL (default: unknown)
    REPO_NAME: Repository name (default: oracle-town)
    GIT_BRANCH: Git branch name (default: empty)
    CONTAINER_IMAGE: Container image name (default: empty)
    PYTEST_VERSION: Pytest version (default: empty)
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from oracle_town.core.ledger import AppendOnlyLedger, canonical_json_bytes, sha256_hex
from oracle_town.core.schema_validation import validate_or_raise


ARTIFACTS = Path("artifacts")
ARTIFACTS.mkdir(exist_ok=True)


def _utc_now() -> str:
    """ISO 8601 timestamp (UTC)"""
    return datetime.now(timezone.utc).isoformat()


def _git_commit() -> str:
    """Get current git commit SHA (40-char hex)"""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "0" * 40  # Fallback for non-git environments


def _run(cmd: str) -> tuple[int, str, str]:
    """
    Run command, capture exit code + stdout + stderr.

    Returns:
        (exit_code, stdout, stderr)
    """
    p = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    out, err = p.communicate()
    return p.returncode, out, err


def main() -> None:
    """Main execution"""
    print("=" * 80)
    print("CI Receipt Bundle Emitter")
    print("=" * 80)

    # Environment variables
    run_id = os.environ.get("RUN_ID", "RUN-local")
    briefcase_id = os.environ.get("BRIEFCASE_ID", "BFC-UNKNOWN")
    repo_origin = os.environ.get("REPO_ORIGIN", "unknown")
    repo_name = os.environ.get("REPO_NAME", "oracle-town")
    git_branch = os.environ.get("GIT_BRANCH", "")
    container_image = os.environ.get("CONTAINER_IMAGE", "")
    pytest_version = os.environ.get("PYTEST_VERSION", "")

    print(f"\nRun ID: {run_id}")
    print(f"Briefcase ID: {briefcase_id}")
    print(f"Repository: {repo_name} ({repo_origin})")
    print(f"Git commit: {_git_commit()}")
    print(f"Git branch: {git_branch or '(none)'}")
    print()

    # Define test executions
    test_commands = [
        ("T-PYTEST", "pytest -q tests/ --tb=short"),
        ("T-MAYOR-IMPORT-PURITY", "pytest -q tests/test_3_mayor_dependency_purity.py"),
        ("T-SCHEMA-FAIL-CLOSED", "pytest -q tests/test_7_schema_fail_closed.py"),
        ("T-LEDGER-INTEGRITY", "pytest -q tests/test_8_ledger_chain_integrity.py"),
        ("T-MAYOR-IO-ALLOWLIST", "pytest -q tests/test_9_mayor_io_allowlist.py"),
    ]

    executions = []

    print("Executing tests...")
    print("-" * 80)

    for test_id, cmd in test_commands:
        print(f"\n[{test_id}] Running: {cmd}")
        started = _utc_now()
        code, out, err = _run(cmd)
        ended = _utc_now()

        # Generate execution ID (deterministic from run_id + test_id + started)
        exec_id_seed = canonical_json_bytes({
            'run_id': run_id,
            'test_id': test_id,
            'started': started
        })
        exec_id = f"EX-{sha256_hex(exec_id_seed)[:10].upper()}"

        # Hash outputs
        stdout_sha = sha256_hex(out.encode("utf-8"))
        stderr_sha = sha256_hex(err.encode("utf-8"))

        # Status
        status = "PASS" if code == 0 else "FAIL"

        # Artifacts (e.g., JUnit XML)
        artifacts = []
        if "junitxml" in cmd:
            junit_path = ARTIFACTS / "junit.xml"
            if junit_path.exists():
                junit_bytes = junit_path.read_bytes()
                artifacts.append({
                    "path": str(junit_path),
                    "sha256": sha256_hex(junit_bytes)
                })

        executions.append({
            "exec_id": exec_id,
            "test_id": test_id,
            "command": cmd,
            "started_at": started,
            "ended_at": ended,
            "exit_code": code,
            "status": status,
            "io_hashes": {
                "stdout_sha256": stdout_sha,
                "stderr_sha256": stderr_sha
            },
            "artifacts": artifacts,
        })

        # Print result
        emoji = "✅" if status == "PASS" else "❌"
        print(f"{emoji} {status} (exit_code={code})")
        if status == "FAIL":
            print(f"   stdout hash: {stdout_sha}")
            print(f"   stderr hash: {stderr_sha}")

    print("\n" + "-" * 80)
    print("Test execution complete.\n")

    # Derive attestations from executions
    print("Deriving attestations...")
    attestations = []

    def attestation(
        attestation_id: str,
        obligation_name: str,
        expected_attestor: str,
        status: str,
        based_on_exec_ids: list[str]
    ) -> dict:
        """Create attestation dict"""
        return {
            "attestation_id": attestation_id,
            "obligation_name": obligation_name,
            "expected_attestor": expected_attestor,
            "status": status,
            "based_on_exec_ids": based_on_exec_ids,
            "evidence": {
                "bundle_ref": {"bundle_id": "PENDING", "sha256": "PENDING"},
                "exec_refs": [{"exec_id": eid} for eid in based_on_exec_ids],
            },
            "created_at": _utc_now(),
        }

    # Map executions to attestations
    exec_map = {e["test_id"]: e for e in executions}

    if "T-PYTEST" in exec_map:
        attestations.append(attestation(
            "ATT-UNITGREEN",
            "unit_tests_green",
            "CI_RUNNER",
            "PASS" if exec_map["T-PYTEST"]["status"] == "PASS" else "FAIL",
            [exec_map["T-PYTEST"]["exec_id"]]
        ))

    if "T-MAYOR-IMPORT-PURITY" in exec_map:
        attestations.append(attestation(
            "ATT-MAYOR-PURITY",
            "mayor_dependency_purity",
            "CI_RUNNER",
            "PASS" if exec_map["T-MAYOR-IMPORT-PURITY"]["status"] == "PASS" else "FAIL",
            [exec_map["T-MAYOR-IMPORT-PURITY"]["exec_id"]]
        ))

    if "T-SCHEMA-FAIL-CLOSED" in exec_map:
        attestations.append(attestation(
            "ATT-SCHEMA-FAILCLOSED",
            "schema_validation_fail_closed",
            "CI_RUNNER",
            "PASS" if exec_map["T-SCHEMA-FAIL-CLOSED"]["status"] == "PASS" else "FAIL",
            [exec_map["T-SCHEMA-FAIL-CLOSED"]["exec_id"]]
        ))

    if "T-LEDGER-INTEGRITY" in exec_map:
        attestations.append(attestation(
            "ATT-LEDGER-INTEGRITY",
            "ledger_chain_integrity",
            "CI_RUNNER",
            "PASS" if exec_map["T-LEDGER-INTEGRITY"]["status"] == "PASS" else "FAIL",
            [exec_map["T-LEDGER-INTEGRITY"]["exec_id"]]
        ))

    if "T-MAYOR-IO-ALLOWLIST" in exec_map:
        attestations.append(attestation(
            "ATT-MAYOR-IO-PURE",
            "mayor_io_purity",
            "CI_RUNNER",
            "PASS" if exec_map["T-MAYOR-IO-ALLOWLIST"]["status"] == "PASS" else "FAIL",
            [exec_map["T-MAYOR-IO-ALLOWLIST"]["exec_id"]]
        ))

    print(f"Derived {len(attestations)} attestations.\n")

    # Build receipt bundle
    print("Building receipt bundle...")
    bundle_id_seed = canonical_json_bytes({'run_id': run_id, 't': _utc_now()})
    bundle_id = f"RCPT-{sha256_hex(bundle_id_seed)[:10].upper()}"

    bundle = {
        "schema_version": "1.0.0",
        "bundle_id": bundle_id,
        "run_id": run_id,
        "briefcase_id": briefcase_id,
        "created_at": _utc_now(),
        "provenance": {
            "attestor_id": "CI_RUNNER",
            "attestor_kind": "CI_RUNNER",
            "repo": {
                "name": repo_name,
                "url_or_origin": repo_origin
            },
            "git": {
                "commit_sha": _git_commit(),
                "branch": git_branch,
                "dirty": False  # CI runs should always be on clean commits
            },
            "runtime": {
                "os": platform.system().lower(),
                "arch": platform.machine(),
                "container_image": container_image,
                "working_dir": str(Path.cwd()),
            },
            "tool_versions": {
                "python": platform.python_version(),
                "pytest": pytest_version or "unknown",
            },
        },
        "executions": executions,
        "attestations": attestations,
        "hashes": {"canonical_sha256": "PENDING"},
        "constraints": {
            "deterministic": True,
            "no_confidence_fields": True,
            "no_mayor_imports_claimed": True
        },
    }

    # Compute canonical hash (excludes hashes field itself)
    bundle_without_hashes = {k: v for k, v in bundle.items() if k != "hashes"}
    canonical_hash = sha256_hex(canonical_json_bytes(bundle_without_hashes))
    bundle["hashes"]["canonical_sha256"] = canonical_hash

    # Fill evidence bundle_ref now that we know bundle_id + hash
    for att in bundle["attestations"]:
        att["evidence"]["bundle_ref"]["bundle_id"] = bundle_id
        att["evidence"]["bundle_ref"]["sha256"] = canonical_hash

    print(f"Bundle ID: {bundle_id}")
    print(f"Canonical hash: {canonical_hash}\n")

    # Validate against schema (fail-closed)
    print("Validating receipt bundle against schema...")
    try:
        validate_or_raise(bundle, "ci_receipt_bundle.schema.json")
        print("✅ Schema validation passed.\n")
    except Exception as e:
        print(f"❌ Schema validation FAILED:")
        print(str(e))
        sys.exit(1)

    # Write to artifacts/
    out_path = ARTIFACTS / "receipt_bundle.json"
    out_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Receipt bundle written to: {out_path}\n")

    # Append to ledger (reference only, not full content)
    print("Appending to ledger...")
    ledger = AppendOnlyLedger(ARTIFACTS / "ledger.jsonl")
    entry = ledger.append("RECEIPT_BUNDLE_REF", {
        "bundle_id": bundle_id,
        "sha256": canonical_hash,
        "run_id": run_id,
        "briefcase_id": briefcase_id,
    })
    print(f"Ledger entry: seq={entry.seq}, hash={entry.canonical_sha256[:16]}...\n")

    # Verify ledger chain
    print("Verifying ledger chain integrity...")
    try:
        ledger.verify_chain()
        print("✅ Ledger chain verified.\n")
    except AssertionError as e:
        print(f"❌ Ledger chain verification FAILED:")
        print(str(e))
        sys.exit(1)

    # Summary
    print("=" * 80)
    print("Receipt Bundle Summary")
    print("=" * 80)
    passed = sum(1 for e in executions if e["status"] == "PASS")
    failed = sum(1 for e in executions if e["status"] == "FAIL")
    print(f"Executions: {len(executions)} total ({passed} PASS, {failed} FAIL)")
    print(f"Attestations: {len(attestations)}")
    print(f"Bundle ID: {bundle_id}")
    print(f"Canonical hash: {canonical_hash}")
    print(f"Ledger entries: {entry.seq}")
    print()

    # Fail CI if any execution failed (fail-closed)
    if failed > 0:
        print("❌ CI FAILED: One or more test executions failed.")
        print("   NO RECEIPT = NO SHIP")
        print("   Fix failing tests and re-run.")
        sys.exit(1)

    print("✅ CI PASSED: All tests passed, receipt bundle emitted.")
    print("   Receipt-grade evidence ready for Mayor.")
    sys.exit(0)


if __name__ == "__main__":
    main()
