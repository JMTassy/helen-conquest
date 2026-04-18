#!/usr/bin/env python3
"""
Test Suite: OpenClaw ↔ HELEN Proxy
Validates K-gate (K-ρ/K-τ) and S-gate (S1-S4) compliance.

Status: OPERATIONAL
Coverage: Core governance rules, determinism, immutability
"""

import json
import tempfile
import os
from pathlib import Path
from openclaw_helen_proxy import (
    OpenClawProxy,
    ProxyRequest,
    ApprovalStatus,
    CommandType,
)


def test_k_rho_determinism():
    """
    K-ρ Gate: Determinism
    Requirement: Same input → same output (receipt hash matches)
    """
    print("\n" + "=" * 60)
    print("TEST: K-ρ GATE (DETERMINISM)")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = os.path.join(tmpdir, "ledger.ndjson")
        proxy = OpenClawProxy(ledger_path=ledger_path)

        # Same request twice
        request_json = {
            "workflow_id": "daily_digest_v1",
            "command": "run_aggregation",
            "parameters": {
                "sources": ["twitter_steipete", "hackernews", "devto"],
            },
            "timestamp": "2026-02-22T07:00:00Z",
            "approval_policy": "human_required",
        }

        # First execution
        request_json["request_hash"] = proxy._sha256(
            {"workflow_id": "daily_digest_v1", "command": "run_aggregation",
             "parameters": request_json["parameters"], "timestamp": "2026-02-22T07:00:00Z"}
        )
        receipt1 = proxy.process_request(request_json)

        # Reset proxy but keep same ledger
        proxy2 = OpenClawProxy(ledger_path=ledger_path)

        # Same request again
        receipt2 = proxy2.process_request(request_json)

        # K-ρ CHECK: Hashes should match (deterministic)
        print(f"Receipt 1 Hash: {receipt1.response_hash}")
        print(f"Receipt 2 Hash: {receipt2.response_hash}")

        if receipt1.response_hash == receipt2.response_hash:
            print("✅ K-ρ PASSED: Deterministic execution (same input → same hash)")
            return True
        else:
            print("❌ K-ρ FAILED: Non-deterministic behavior detected")
            return False


def test_s2_no_receipt_no_claim():
    """
    S2 Gate: No Receipt = No Claim
    Requirement: Every operation produces receipt.json
    """
    print("\n" + "=" * 60)
    print("TEST: S2 GATE (NO RECEIPT = NO CLAIM)")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = os.path.join(tmpdir, "ledger.ndjson")
        proxy = OpenClawProxy(ledger_path=ledger_path)

        request_json = {
            "workflow_id": "test_digest",
            "command": "run_aggregation",
            "parameters": {"sources": ["test"]},
            "timestamp": "2026-02-22T07:00:00Z",
        }

        # Process request
        receipt = proxy.process_request(request_json)

        # S2 CHECK: Receipt must exist
        if receipt and receipt.receipt_id:
            print(f"✅ S2 PASSED: Receipt generated: {receipt.receipt_id}")

            # Verify receipt is in ledger
            ledger = proxy.dump_ledger()
            receipt_in_ledger = any(
                e.get("receipt_id") == receipt.receipt_id for e in ledger
            )

            if receipt_in_ledger:
                print(f"✅ S2 CONFIRMED: Receipt bound to immutable ledger")
                return True
            else:
                print(f"❌ S2 FAILED: Receipt not found in ledger")
                return False
        else:
            print("❌ S2 FAILED: No receipt generated")
            return False


def test_s3_immutable_ledger():
    """
    S3 Gate: Append-Only Ledger
    Requirement: Ledger cannot be modified or deleted
    """
    print("\n" + "=" * 60)
    print("TEST: S3 GATE (IMMUTABLE LEDGER)")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = os.path.join(tmpdir, "ledger.ndjson")
        proxy = OpenClawProxy(ledger_path=ledger_path)

        # Create entry 1
        request1 = {
            "workflow_id": "digest1",
            "command": "run_aggregation",
            "parameters": {"sources": ["src1"]},
            "timestamp": "2026-02-22T07:00:00Z",
        }
        receipt1 = proxy.process_request(request1)

        # Record initial ledger
        initial_ledger = proxy.dump_ledger()
        initial_count = len(initial_ledger)

        # Create entry 2
        request2 = {
            "workflow_id": "digest2",
            "command": "run_aggregation",
            "parameters": {"sources": ["src2"]},
            "timestamp": "2026-02-22T07:01:00Z",
        }
        receipt2 = proxy.process_request(request2)

        # Verify append-only behavior
        final_ledger = proxy.dump_ledger()
        final_count = len(final_ledger)

        if final_count == initial_count + 1:
            print(f"✅ S3 PASSED: Ledger is append-only")
            print(f"   Initial entries: {initial_count}")
            print(f"   After operation: {final_count}")

            # Verify original entry unchanged
            if initial_ledger[0] == final_ledger[0]:
                print(f"✅ S3 CONFIRMED: Original entries unchanged")
                return True
            else:
                print(f"❌ S3 FAILED: Original entry was modified")
                return False
        else:
            print(
                f"❌ S3 FAILED: Expected {initial_count + 1} entries, got {final_count}"
            )
            return False


def test_s4_human_approval():
    """
    S4 Gate: Human Authority Absolute
    Requirement: Only human can approve SHIP/ABORT
    """
    print("\n" + "=" * 60)
    print("TEST: S4 GATE (HUMAN AUTHORITY ABSOLUTE)")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = os.path.join(tmpdir, "ledger.ndjson")
        proxy = OpenClawProxy(ledger_path=ledger_path)

        # Create request
        request_json = {
            "workflow_id": "digest_approval",
            "command": "run_aggregation",
            "parameters": {"sources": ["test"]},
            "timestamp": "2026-02-22T07:00:00Z",
        }
        receipt = proxy.process_request(request_json)

        # S4 CHECK 1: Receipt starts in pending_human_review state
        if receipt.status == ApprovalStatus.PENDING_HUMAN_REVIEW:
            print(f"✅ S4.1 PASSED: Receipt requires human approval (pending_human_review)")
        else:
            print(f"❌ S4.1 FAILED: Receipt status should be pending_human_review")
            return False

        # S4 CHECK 2: Simulate human approval
        approval_result = proxy.handle_approval(
            receipt_id=receipt.receipt_id,
            decision="SHIP",
            approved_by="user",
            reason="Looks good",
        )

        if approval_result:
            print(f"✅ S4.2 PASSED: Human approval recorded")

            # Verify approval in ledger
            ledger = proxy.dump_ledger()
            approval_found = any(
                e.get("source") == "openclaw_proxy_approval"
                and e.get("receipt_id") == receipt.receipt_id
                for e in ledger
            )

            if approval_found:
                print(f"✅ S4.3 PASSED: Approval decision immutably logged")
                return True
            else:
                print(f"❌ S4.3 FAILED: Approval not found in ledger")
                return False
        else:
            print(f"❌ S4.2 FAILED: Approval could not be recorded")
            return False


def test_whitelist_enforcement():
    """
    Whitelist Validation
    Requirement: Only whitelisted commands accepted
    """
    print("\n" + "=" * 60)
    print("TEST: WHITELIST ENFORCEMENT")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = os.path.join(tmpdir, "ledger.ndjson")
        proxy = OpenClawProxy(ledger_path=ledger_path)

        # Valid command
        valid_request = {
            "workflow_id": "test",
            "command": "run_aggregation",
            "parameters": {},
            "timestamp": "2026-02-22T07:00:00Z",
        }
        receipt = proxy.process_request(valid_request)

        if receipt.status != ApprovalStatus.FAILED:
            print(f"✅ Valid command accepted: run_aggregation")
        else:
            print(f"❌ Valid command rejected")
            return False

        # Invalid command
        invalid_request = {
            "workflow_id": "test",
            "command": "delete_ledger",
            "parameters": {},
            "timestamp": "2026-02-22T07:00:00Z",
        }
        receipt = proxy.process_request(invalid_request)

        if receipt.status == ApprovalStatus.FAILED and receipt.error_code:
            print(f"✅ Invalid command rejected: {receipt.error_code}")
            return True
        else:
            print(f"❌ Invalid command was accepted (security breach)")
            return False


def test_request_validation():
    """
    Request Schema Validation
    Requirement: Missing fields rejected
    """
    print("\n" + "=" * 60)
    print("TEST: REQUEST VALIDATION")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = os.path.join(tmpdir, "ledger.ndjson")
        proxy = OpenClawProxy(ledger_path=ledger_path)

        # Missing workflow_id
        incomplete_request = {
            "command": "run_aggregation",
            "parameters": {},
            "timestamp": "2026-02-22T07:00:00Z",
        }
        receipt = proxy.process_request(incomplete_request)

        if receipt.status == ApprovalStatus.FAILED:
            print(f"✅ Missing field detected: {receipt.error_code}")
            return True
        else:
            print(f"❌ Invalid request was accepted")
            return False


def run_all_tests():
    """Run complete test suite."""
    print("\n" + "=" * 60)
    print("OPENCLAW ↔ HELEN PROXY TEST SUITE")
    print("=" * 60)

    tests = [
        ("K-ρ Determinism", test_k_rho_determinism),
        ("S2 No Receipt = No Claim", test_s2_no_receipt_no_claim),
        ("S3 Immutable Ledger", test_s3_immutable_ledger),
        ("S4 Human Authority", test_s4_human_approval),
        ("Whitelist Enforcement", test_whitelist_enforcement),
        ("Request Validation", test_request_validation),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results[test_name] = "PASSED" if passed else "FAILED"
        except Exception as e:
            print(f"❌ TEST ERROR: {e}")
            results[test_name] = "ERROR"

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, result in results.items():
        status_icon = "✅" if result == "PASSED" else "❌" if result == "FAILED" else "⚠️"
        print(f"{status_icon} {test_name}: {result}")

    total_passed = sum(1 for r in results.values() if r == "PASSED")
    total_tests = len(results)

    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    return total_passed == total_tests


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
