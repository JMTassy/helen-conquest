# tests/governance_regression/test_k_gates.py

import pytest
from oracle_town.core.tri_gate import TriGate
from oracle_town.schemas.claim import CompiledClaim
from oracle_town.schemas.attestor import AttestorRegistry


def minimal_claim(**overrides):
    base = {
        "claim_id": "TEST-001",
        "statement": "Test claim",
        "evidence": [],
        "attestor_id": "attestor_alpha",
        "policy_version": "v1.0",
        "timestamp": "2026-01-31T00:00:00Z",
    }
    base.update(overrides)
    return CompiledClaim(**base)


def test_k0_unregistered_attestor_rejected():
    """
    K0: No unregistered attestor may pass.
    """
    registry = AttestorRegistry(attestors=[])  # empty on purpose
    gate = TriGate(attestor_registry=registry)

    claim = minimal_claim(attestor_id="unknown_attestor")

    verdict = gate.evaluate(claim)

    assert verdict.accepted is False
    assert verdict.reason_code == "K0_UNREGISTERED_ATTESTOR"


def test_k1_missing_evidence_fail_closed():
    """
    K1: Missing evidence must REJECT, never WARN or ACCEPT.
    """
    registry = AttestorRegistry(attestors=["attestor_alpha"])
    gate = TriGate(attestor_registry=registry)

    claim = minimal_claim(evidence=[])

    verdict = gate.evaluate(claim)

    assert verdict.accepted is False
    assert verdict.reason_code == "K1_MISSING_EVIDENCE"


def test_k2_self_attestation_rejected():
    """
    K2: An entity cannot attest its own claim.
    """
    registry = AttestorRegistry(attestors=["attestor_alpha"])
    gate = TriGate(attestor_registry=registry)

    claim = minimal_claim(
        attestor_id="attestor_alpha",
        statement="attestor_alpha claims attestor_alpha is valid",
    )

    verdict = gate.evaluate(claim)

    assert verdict.accepted is False
    assert verdict.reason_code == "K2_SELF_ATTESTATION"


def test_k5_determinism_same_input_same_verdict():
    """
    K5: Determinism — same input must produce byte-identical verdicts.
    """
    registry = AttestorRegistry(attestors=["attestor_alpha"])
    gate = TriGate(attestor_registry=registry)

    claim = minimal_claim(evidence=["doc_a"])

    v1 = gate.evaluate(claim)
    v2 = gate.evaluate(claim)

    assert v1.to_dict() == v2.to_dict()


def test_k7_policy_pinning_enforced():
    """
    K7: Verdict must be pinned to declared policy version.
    """
    registry = AttestorRegistry(attestors=["attestor_alpha"])
    gate = TriGate(attestor_registry=registry)

    claim = minimal_claim(policy_version="v1.0")

    verdict = gate.evaluate(claim)

    assert verdict.policy_version == "v1.0"
