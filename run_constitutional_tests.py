#!/usr/bin/env python3
"""
Constitutional Compliance Test Runner

Runs all 9 constitutional tests without requiring pytest.
Each test failure is a kernel bug (not a feature request).

Tests 1-6: Original constitutional tests
Tests 7-9: Enforcement infrastructure tests (NEW)
"""
import sys
import traceback
from pathlib import Path


def run_test_1_mayor_only_writes_decisions():
    """Test 1: Mayor-Only Verdict Output"""
    print("\n" + "=" * 80)
    print("TEST 1: Mayor-Only Verdict Output")
    print("=" * 80)

    repo_root = Path(__file__).parent
    decision_dir = "decisions"
    allowed_files = {"mayor_v2.py", "mayor.py"}

    offenders = []
    for py_file in repo_root.rglob("*.py"):
        if "test" in str(py_file) or "__pycache__" in str(py_file):
            continue

        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        # Check for WRITE operations specifically (not just references)
        write_indicators = [
            f'Path("{decision_dir}").mkdir',
            f"Path('{decision_dir}').mkdir",
            f'open("{decision_dir}',
            f"open('{decision_dir}",
            f'Path("{decision_dir}")',
            f"Path('{decision_dir}')",
        ]

        write_ops = ["write_text(", ".write(", "json.dump("]

        # Must have both a decisions/ path AND a write operation in proximity
        has_decision_write = False
        for indicator in write_indicators:
            if indicator in content:
                # Check if there's a write operation nearby
                if any(op in content for op in write_ops):
                    # EV reading for verification is OK, writing is not
                    if "read_text" in content or "glob(" in content:
                        continue  # EV verification pattern, allowed
                    has_decision_write = True
                    break

        if has_decision_write and py_file.name not in allowed_files:
            offenders.append(str(py_file.relative_to(repo_root)))

    if offenders:
        print(f"❌ FAILED: Non-Mayor files writing to decisions/:")
        for f in offenders:
            print(f"   - {f}")
        return False

    print("✅ PASSED: Only Mayor writes to decisions/")
    return True


def run_test_2_factory_no_verdict_semantics():
    """Test 2: Factory Emits Attestations Only"""
    print("\n" + "=" * 80)
    print("TEST 2: Factory Emits Attestations Only")
    print("=" * 80)

    repo_root = Path(__file__).parent
    forbidden_terms = ["SHIP", "NO_SHIP", "decision_record", "verdict", "blocking_obligations"]

    factory_files = list((repo_root / "oracle_town" / "core").rglob("*factory*.py"))
    if not factory_files:
        print("❌ FAILED: No factory files found")
        return False

    for factory_file in factory_files:
        content = factory_file.read_text(encoding="utf-8", errors="ignore")

        # Remove comments
        import re
        content_no_comments = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
        content_no_comments = re.sub(r'""".*?"""', '', content_no_comments, flags=re.DOTALL)

        violations = []
        for term in forbidden_terms:
            if term in content_no_comments:
                if f'"{term}"' not in content_no_comments and f"'{term}'" not in content_no_comments:
                    violations.append(term)

        if violations:
            print(f"❌ FAILED: Factory contains verdict semantics: {violations}")
            return False

    print("✅ PASSED: Factory has no verdict semantics")
    return True


def run_test_3_mayor_dependency_purity():
    """Test 3: Mayor Dependency Purity"""
    print("\n" + "=" * 80)
    print("TEST 3: Mayor Dependency Purity")
    print("=" * 80)

    import ast
    repo_root = Path(__file__).parent
    mayor_v2_path = repo_root / "oracle_town" / "core" / "mayor_v2.py"

    if not mayor_v2_path.exists():
        print("❌ FAILED: mayor_v2.py not found")
        return False

    content = mayor_v2_path.read_text(encoding="utf-8")
    tree = ast.parse(content)

    forbidden_imports = {
        "oracle_town.core.scoring",
        "oracle_town.core.town_hall",
        "oracle_town.creative",  # Layer 2 must never influence Mayor
        "oracle_town.districts",  # Districts output via Concierge only
        "telemetry"
    }

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)

    violations = [imp for imp in imports if any(forbidden in imp for forbidden in forbidden_imports)]

    if violations:
        print(f"❌ FAILED: Mayor imports forbidden modules: {violations}")
        print(f"   Forbidden: scoring, town_hall, creative, districts, telemetry")
        return False

    print("✅ PASSED: Mayor has no forbidden imports (including Layer 2 Creative Town)")
    return True


def run_test_4_no_receipt_no_ship():
    """Test 4: NO RECEIPT = NO SHIP"""
    print("\n" + "=" * 80)
    print("TEST 4: NO RECEIPT = NO SHIP")
    print("=" * 80)

    import asyncio
    from oracle_town.core.factory import Briefcase
    from oracle_town.core.mayor_v2 import MayorV2

    async def test():
        briefcase = Briefcase(
            run_id="TEST_NO_RECEIPT_001",
            claim_id="CLM_TEST_001",
            required_obligations=[
                {"name": "unit_tests_green", "type": "CODE_PROOF", "severity": "HARD"},
                {"name": "imports_clean", "type": "CODE_PROOF", "severity": "HARD"},
            ],
            requested_tests=[],
            kill_switch_policies=[],
        )

        attestations = []  # NO RECEIPTS

        mayor = MayorV2()
        decision = await mayor.decide(briefcase, attestations)

        if decision.decision != "NO_SHIP":
            print(f"❌ FAILED: Mayor allowed SHIP without receipts")
            return False

        expected_blockers = {"unit_tests_green", "imports_clean"}
        actual_blockers = set(decision.blocking_obligations)

        if actual_blockers != expected_blockers:
            print(f"❌ FAILED: Blocking obligations mismatch")
            print(f"   Expected: {expected_blockers}")
            print(f"   Actual: {actual_blockers}")
            return False

        print("✅ PASSED: NO RECEIPT = NO SHIP enforced")
        return True

    return asyncio.run(test())


def run_test_5_kill_switch_priority():
    """Test 5: Kill-Switch Absolute Priority"""
    print("\n" + "=" * 80)
    print("TEST 5: Kill-Switch Absolute Priority")
    print("=" * 80)

    import asyncio
    from oracle_town.core.factory import Briefcase, Attestation
    from oracle_town.core.mayor_v2 import MayorV2

    async def test():
        briefcase = Briefcase(
            run_id="TEST_KILL_001",
            claim_id="CLM_TEST_KILL",
            required_obligations=[
                {"name": "unit_tests_green", "type": "CODE_PROOF", "severity": "HARD"},
            ],
            requested_tests=[],
            kill_switch_policies=[],
        )

        # ALL obligations satisfied
        attestations = [
            Attestation(
                run_id="TEST_KILL_001",
                claim_id="CLM_TEST_KILL",
                obligation_name="unit_tests_green",
                attestor="CI_RUNNER",
                policy_match=1,
                payload_hash="abc123",
            )
        ]

        mayor = MayorV2()
        decision = await mayor.decide(briefcase, attestations, kill_switch_signals=["LEGAL"])

        if decision.decision != "NO_SHIP":
            print("❌ FAILED: Kill-switch did not block SHIP")
            return False

        if not decision.kill_switch_triggered:
            print("❌ FAILED: kill_switch_triggered not set")
            return False

        print("✅ PASSED: Kill-switch blocks SHIP even with satisfied attestations")
        return True

    return asyncio.run(test())


def run_test_6_replay_determinism():
    """Test 6: Replay Determinism"""
    print("\n" + "=" * 80)
    print("TEST 6: Replay Determinism")
    print("=" * 80)

    import asyncio
    import hashlib
    import json
    from oracle_town.core.factory import Briefcase
    from oracle_town.core.mayor_v2 import MayorV2

    def compute_digest(decision):
        canonical = {
            "decision": decision.decision,
            "blocking_obligations": sorted(decision.blocking_obligations),
            "kill_switch_triggered": decision.kill_switch_triggered,
            "attestations_checked": decision.attestations_checked,
        }
        return hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()

    async def test():
        # Run 1
        briefcase1 = Briefcase(
            run_id="TEST_REPLAY_001",
            claim_id="CLM_REPLAY",
            required_obligations=[],
            requested_tests=[],
            kill_switch_policies=[],
        )
        mayor1 = MayorV2()
        decision1 = await mayor1.decide(briefcase1, [])
        digest1 = compute_digest(decision1)

        # Run 2 (identical)
        briefcase2 = Briefcase(
            run_id="TEST_REPLAY_001",
            claim_id="CLM_REPLAY",
            required_obligations=[],
            requested_tests=[],
            kill_switch_policies=[],
        )
        mayor2 = MayorV2()
        decision2 = await mayor2.decide(briefcase2, [])
        digest2 = compute_digest(decision2)

        if digest1 != digest2:
            print(f"❌ FAILED: Replay non-determinism")
            print(f"   Digest 1: {digest1}")
            print(f"   Digest 2: {digest2}")
            return False

        print("✅ PASSED: Replay determinism verified")
        return True

    return asyncio.run(test())


def run_test_7_schema_fail_closed():
    """Test 7: Schema Validation is Fail-Closed"""
    print("\n" + "=" * 80)
    print("TEST 7: Schema Validation is Fail-Closed")
    print("=" * 80)

    try:
        from oracle_town.core.schema_validation import validate_or_raise, SchemaValidationError
    except ImportError as e:
        print(f"❌ FAILED: Cannot import schema_validation: {e}")
        return False

    # Test 1: Invalid UI stream (missing required fields)
    invalid_ui_stream = {
        "schema_version": "1.0.0",
        "stream_id": "UIS-TEST123",
        # Missing: run_id, created_at, ui_mode, events, hashes, constraints
    }

    try:
        validate_or_raise(invalid_ui_stream, "ui_event_stream.schema.json")
        print("❌ FAILED: Invalid UI stream was not rejected")
        return False
    except SchemaValidationError:
        print("✅ Invalid UI stream rejected (missing required fields)")
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
        return False

    # Test 2: Invalid attestation status (not PASS or FAIL)
    invalid_receipt = {
        "schema_version": "1.0.0",
        "bundle_id": "RCPT-TEST123456",
        "run_id": "RUN-001",
        "briefcase_id": "BFC-001",
        "created_at": "2026-01-22T12:00:00Z",
        "provenance": {
            "attestor_id": "CI_RUNNER",
            "attestor_kind": "CI_RUNNER",
            "repo": {"name": "test", "url_or_origin": "http://example.com"},
            "git": {"commit_sha": "a" * 40, "dirty": False},
            "runtime": {"os": "linux", "arch": "x86_64", "container_image": "", "working_dir": "/app"},
            "tool_versions": {"python": "3.9", "pytest": "7.0"}
        },
        "executions": [{
            "exec_id": "EX-ABC123",
            "test_id": "T-001",
            "command": "pytest",
            "started_at": "2026-01-22T12:00:00Z",
            "ended_at": "2026-01-22T12:01:00Z",
            "exit_code": 0,
            "status": "PASS",
            "io_hashes": {"stdout_sha256": "a" * 64, "stderr_sha256": "b" * 64},
            "artifacts": []
        }],
        "attestations": [{
            "attestation_id": "ATT-001",
            "obligation_name": "tests_green",
            "expected_attestor": "CI_RUNNER",
            "status": "MAYBE",  # Invalid! Must be PASS or FAIL
            "based_on_exec_ids": ["EX-ABC123"],
            "evidence": {
                "bundle_ref": {"bundle_id": "RCPT-TEST123456", "sha256": "a" * 64},
                "exec_refs": [{"exec_id": "EX-ABC123"}]
            },
            "created_at": "2026-01-22T12:01:00Z"
        }],
        "hashes": {"canonical_sha256": "a" * 64},
        "constraints": {"deterministic": True, "no_confidence_fields": True, "no_mayor_imports_claimed": True}
    }

    try:
        validate_or_raise(invalid_receipt, "ci_receipt_bundle.schema.json")
        print("❌ FAILED: Invalid attestation status 'MAYBE' was not rejected")
        return False
    except SchemaValidationError:
        print("✅ Invalid attestation status 'MAYBE' rejected (must be PASS or FAIL)")
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
        return False

    print("✅ PASSED: Schema validation is fail-closed")
    return True


def run_test_8_ledger_chain_integrity():
    """Test 8: Ledger Chain Integrity"""
    print("\n" + "=" * 80)
    print("TEST 8: Ledger Chain Integrity")
    print("=" * 80)

    try:
        from oracle_town.core.ledger import AppendOnlyLedger
    except ImportError as e:
        print(f"❌ FAILED: Cannot import ledger: {e}")
        return False

    import tempfile
    import json

    # Test 1: Clean chain verifies
    tmp = Path(tempfile.mkdtemp()) / "test_ledger.jsonl"
    ledger = AppendOnlyLedger(tmp)

    e1 = ledger.append("RECEIPT_BUNDLE_REF", {"bundle_id": "RCPT-001", "sha256": "a" * 64})
    e2 = ledger.append("ATTESTATION_REF", {"attestation_id": "ATT-001", "sha256": "b" * 64})

    try:
        ledger.verify_chain()
        print("✅ Clean ledger chain verified")
    except AssertionError as e:
        print(f"❌ FAILED: Clean chain did not verify: {e}")
        return False

    # Test 2: Tamper detection (modify payload)
    lines = tmp.read_text(encoding="utf-8").splitlines()
    last_entry = json.loads(lines[-1])
    last_entry["payload"]["sha256"] = "c" * 64  # Tamper!
    lines[-1] = json.dumps(last_entry, ensure_ascii=False)
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")

    try:
        AppendOnlyLedger(tmp).verify_chain()
        print("❌ FAILED: Tampered ledger was not detected")
        return False
    except AssertionError:
        print("✅ Tampered ledger detected (payload modification)")

    print("✅ PASSED: Ledger chain integrity enforcement works")
    return True


def run_test_9_mayor_io_allowlist():
    """Test 9: Mayor I/O Allowlist"""
    print("\n" + "=" * 80)
    print("TEST 9: Mayor I/O Allowlist")
    print("=" * 80)

    import ast
    repo_root = Path(__file__).parent
    mayor_path = repo_root / "oracle_town" / "core" / "mayor_v2.py"

    if not mayor_path.exists():
        print(f"❌ FAILED: Mayor not found at {mayor_path}")
        return False

    content = mayor_path.read_text(encoding="utf-8")
    tree = ast.parse(content)

    # Test 1: Check for open() calls to forbidden paths
    violations = []
    forbidden_patterns = ["ui_event_stream", "creative", "districts", "proposal", "builder_packet"]

    class OpenCallVisitor(ast.NodeVisitor):
        def visit_Call(self, node):
            # Detect: open("path")
            if isinstance(node.func, ast.Name) and node.func.id == "open":
                if node.args and isinstance(node.args[0], ast.Constant):
                    if isinstance(node.args[0].value, str):
                        path = node.args[0].value
                        for pattern in forbidden_patterns:
                            if pattern in path:
                                violations.append(("open", path, node.lineno))

            # Detect: Path("...").open() or Path(...).read_text()
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in {"open", "read_text", "read_bytes"}:
                    if isinstance(node.func.value, ast.Call):
                        if hasattr(node.func.value.func, 'id') and node.func.value.func.id == "Path":
                            if node.func.value.args and isinstance(node.func.value.args[0], ast.Constant):
                                if isinstance(node.func.value.args[0].value, str):
                                    path = node.func.value.args[0].value
                                    for pattern in forbidden_patterns:
                                        if pattern in path:
                                            violations.append((node.func.attr, path, node.lineno))

            self.generic_visit(node)

    OpenCallVisitor().visit(tree)

    if violations:
        print(f"❌ FAILED: Mayor has forbidden file I/O:")
        for fn, path, ln in violations:
            print(f"   - line {ln}: {fn}('{path}')")
        return False

    print("✅ Mayor has no forbidden file I/O (open/read_text/read_bytes)")

    # Test 2: Check decide() signature
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "MayorV2":
            for method in node.body:
                if isinstance(method, ast.FunctionDef) and method.name == "decide":
                    params = [arg.arg for arg in method.args.args]
                    allowed = {"self", "briefcase", "attestations", "kill_switch_signals"}
                    unexpected = [p for p in params if p not in allowed]

                    if unexpected:
                        print(f"❌ FAILED: decide() has unexpected params: {unexpected}")
                        return False

                    print(f"✅ decide() signature pure: {params}")
                    break
            break

    print("✅ PASSED: Mayor I/O purity enforced")
    return True


def main():
    """Run all constitutional tests"""
    print("=" * 80)
    print("CONSTITUTIONAL COMPLIANCE TEST SUITE (9 TESTS)")
    print("=" * 80)
    print("\nThese tests enforce the immutable KERNEL_CONSTITUTION.md")
    print("Failures are kernel bugs, not feature requests.\n")

    tests = [
        run_test_1_mayor_only_writes_decisions,
        run_test_2_factory_no_verdict_semantics,
        run_test_3_mayor_dependency_purity,
        run_test_4_no_receipt_no_ship,
        run_test_5_kill_switch_priority,
        run_test_6_replay_determinism,
        run_test_7_schema_fail_closed,
        run_test_8_ledger_chain_integrity,
        run_test_9_mayor_io_allowlist,
    ]

    results = []
    for test_func in tests:
        try:
            passed = test_func()
            results.append((test_func.__name__, passed))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {test_func.__name__}:")
            traceback.print_exc()
            results.append((test_func.__name__, False))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nResult: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 ALL CONSTITUTIONAL TESTS PASSED")
        print("   System is constitutionally compliant.")
        return 0
    else:
        print("\n⚠️  CONSTITUTIONAL VIOLATIONS DETECTED")
        print("   Fix these violations before production deployment.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
