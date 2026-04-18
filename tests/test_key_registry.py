#!/usr/bin/env python3
"""
Simple test runner for key-registry CI gates.

These tests exercise fail-closed behaviors and do not require pytest.
Run: `python3 tests/test_key_registry.py`
"""
from oracle_town.core.policy import create_default_policy
from oracle_town.core.mayor_rsm import MayorRSM
import json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def load_registry_hash():
    with open(os.path.join(ROOT, "oracle_town/keys/registry_manifest.json")) as f:
        return json.load(f)["registry_hash"]


def base_briefcase(policy):
    return {
        "run_id": "R-TEST-001",
        "claim_id": "CLM-TEST",
        "claim_type": "CHANGE_REQUEST",
        "required_obligations": [
            {
                "name": "gdpr_consent_banner",
                "type": "CODE_PROOF",
                "severity": "HARD",
                "required_evidence": ["consent_flow_diagram"],
                "required_attestor_classes": ["CI_RUNNER", "LEGAL"],
                "min_quorum": 2
            }
        ],
        "requested_tests": [],
        "kill_switch_policies": [],
        "metadata": {"policy_hash": policy.policy_hash}
    }


def run_mayor(policy, briefcase, ledger):
    keys_path = os.path.join(ROOT, "oracle_town/keys/public_keys.json")
    mayor = MayorRSM(public_keys_path=keys_path)
    decision = mayor.decide(policy, briefcase, ledger)
    return decision


def test_unknown_key_rejected():
    policy = create_default_policy()
    policy.key_registry_hash = load_registry_hash()
    policy.policy_hash = policy.compute_hash()

    briefcase = base_briefcase(policy)

    ledger = {
        "run_id": briefcase["run_id"],
        "claim_id": briefcase["claim_id"],
        "policy_hash": policy.policy_hash,
        "attestations": [
            {
                "attestation_id": "ATT-U1",
                "run_id": briefcase["run_id"],
                "claim_id": briefcase["claim_id"],
                "obligation_name": "gdpr_consent_banner",
                "attestor_id": "unknown_attestor",
                "attestor_class": "CI_RUNNER",
                "policy_hash": policy.policy_hash,
                "evidence_digest": "sha256:abc",
                "signing_key_id": "key-UNKNOWN-999",
                "signature": "ed25519:MOCK",
                "policy_match": 1,
                "timestamp": "2026-01-23T00:00:00Z"
            }
        ]
    }

    decision = run_mayor(policy, briefcase, ledger)
    assert decision.decision == "NO_SHIP"
    assert any("KEY_UNKNOWN" in r for r in decision.blocking_reasons), decision.blocking_reasons
    print("test_unknown_key_rejected: PASS")


def test_class_mismatch_rejected():
    policy = create_default_policy()
    policy.key_registry_hash = load_registry_hash()
    policy.policy_hash = policy.compute_hash()

    briefcase = base_briefcase(policy)

    ledger = {
        "run_id": briefcase["run_id"],
        "claim_id": briefcase["claim_id"],
        "policy_hash": policy.policy_hash,
        "attestations": [
            {
                "attestation_id": "ATT-C1",
                "run_id": briefcase["run_id"],
                "claim_id": briefcase["claim_id"],
                "obligation_name": "gdpr_consent_banner",
                "attestor_id": "ci_runner_001",
                "attestor_class": "LEGAL",  # wrong class for key-2026-01-ci
                "policy_hash": policy.policy_hash,
                "evidence_digest": "sha256:abc",
                "signing_key_id": "key-2026-01-ci",
                "signature": "ed25519:MOCK",
                "policy_match": 1,
                "timestamp": "2026-01-23T00:00:00Z"
            }
        ]
    }

    decision = run_mayor(policy, briefcase, ledger)
    assert decision.decision == "NO_SHIP"
    assert any("KEY_CLASS_MISMATCH" in r for r in decision.blocking_reasons), decision.blocking_reasons
    print("test_class_mismatch_rejected: PASS")


def test_revoked_key_rejected():
    policy = create_default_policy()
    policy.key_registry_hash = load_registry_hash()
    # mark key revoked in policy
    from oracle_town.core.policy import RevokedKey
    policy.revoked_keys.append(RevokedKey("key-2025-12-legal-old", "2026-01-15T00:00:00Z", "Key compromise"))
    policy.policy_hash = policy.compute_hash()

    briefcase = base_briefcase(policy)

    ledger = {
        "run_id": briefcase["run_id"],
        "claim_id": briefcase["claim_id"],
        "policy_hash": policy.policy_hash,
        "attestations": [
            {
                "attestation_id": "ATT-R1",
                "run_id": briefcase["run_id"],
                "claim_id": briefcase["claim_id"],
                "obligation_name": "gdpr_consent_banner",
                "attestor_id": "legal_reviewer_fake",
                "attestor_class": "LEGAL",
                "policy_hash": policy.policy_hash,
                "evidence_digest": "sha256:abc",
                "signing_key_id": "key-2025-12-legal-old",
                "signature": "ed25519:MOCK",
                "policy_match": 1,
                "timestamp": "2026-01-23T00:00:00Z"
            }
        ]
    }

    decision = run_mayor(policy, briefcase, ledger)
    assert decision.decision == "NO_SHIP"
    assert any("Revoked key" in r or "KEY_REVOKED" in r for r in decision.blocking_reasons), decision.blocking_reasons
    print("test_revoked_key_rejected: PASS")


def test_scope_violation_rejected():
    policy = create_default_policy()
    policy.key_registry_hash = load_registry_hash()
    policy.policy_hash = policy.compute_hash()

    briefcase = base_briefcase(policy)
    # use obligation not allowed for legal key
    briefcase['required_obligations'][0]['name'] = 'security_audit'

    ledger = {
        "run_id": briefcase["run_id"],
        "claim_id": briefcase["claim_id"],
        "policy_hash": policy.policy_hash,
        "attestations": [
            {
                "attestation_id": "ATT-S1",
                "run_id": briefcase["run_id"],
                "claim_id": briefcase["claim_id"],
                "obligation_name": "security_audit",
                "attestor_id": "legal_reviewer_001",
                "attestor_class": "LEGAL",
                "policy_hash": policy.policy_hash,
                "evidence_digest": "sha256:abc",
                "signing_key_id": "key-2026-01-legal",
                "signature": "ed25519:MOCK",
                "policy_match": 1,
                "timestamp": "2026-01-23T00:00:00Z"
            }
        ]
    }

    decision = run_mayor(policy, briefcase, ledger)
    assert decision.decision == "NO_SHIP"
    assert any("KEY_SCOPE_VIOLATION" in r for r in decision.blocking_reasons), decision.blocking_reasons
    print("test_scope_violation_rejected: PASS")


def test_registry_hash_pinning():
    policy = create_default_policy()
    # intentionally pin wrong registry hash
    policy.key_registry_hash = "sha256:0000000000000000000000000000000000000000000000000000000000000000"
    policy.policy_hash = policy.compute_hash()

    briefcase = base_briefcase(policy)

    ledger = {"run_id": briefcase["run_id"], "claim_id": briefcase["claim_id"], "policy_hash": policy.policy_hash, "attestations": []}

    decision = run_mayor(policy, briefcase, ledger)
    assert decision.decision == "NO_SHIP"
    assert any("REGISTRY_HASH_MISMATCH" in r for r in decision.blocking_reasons), decision.blocking_reasons
    print("test_registry_hash_pinning: PASS")


def test_replay_with_same_registry():
    policy = create_default_policy()
    policy.key_registry_hash = load_registry_hash()
    policy.policy_hash = policy.compute_hash()

    briefcase = base_briefcase(policy)

    # Build minimal valid attestations to satisfy quorum
    att_ci = {
        "attestation_id": "ATT-D1",
        "run_id": briefcase["run_id"],
        "claim_id": briefcase["claim_id"],
        "obligation_name": "gdpr_consent_banner",
        "attestor_id": "ci_runner_001",
        "attestor_class": "CI_RUNNER",
        "policy_hash": policy.policy_hash,
        "evidence_digest": "sha256:abc",
        "signing_key_id": "key-2026-01-ci",
        "signature": "ed25519:MOCK",
        "policy_match": 1,
        "timestamp": "2026-01-23T00:00:00Z"
    }
    att_legal = {
        "attestation_id": "ATT-D2",
        "run_id": briefcase["run_id"],
        "claim_id": briefcase["claim_id"],
        "obligation_name": "gdpr_consent_banner",
        "attestor_id": "legal_reviewer_001",
        "attestor_class": "LEGAL",
        "policy_hash": policy.policy_hash,
        "evidence_digest": "sha256:def",
        "signing_key_id": "key-2026-01-legal",
        "signature": "ed25519:MOCK",
        "policy_match": 1,
        "timestamp": "2026-01-23T00:00:00Z"
    }

    ledger = {"run_id": briefcase["run_id"], "claim_id": briefcase["claim_id"], "policy_hash": policy.policy_hash, "attestations": [att_ci, att_legal]}

    d1 = run_mayor(policy, briefcase, ledger)
    d2 = run_mayor(policy, briefcase, ledger)
    assert d1.decision_digest == d2.decision_digest
    print("test_replay_with_same_registry: PASS")


def main():
    tests = [
        test_unknown_key_rejected,
        test_class_mismatch_rejected,
        test_revoked_key_rejected,
        test_scope_violation_rejected,
        test_registry_hash_pinning,
        test_replay_with_same_registry
    ]

    for t in tests:
        t()

    print('\nALL key-registry tests PASSED')


if __name__ == '__main__':
    main()
