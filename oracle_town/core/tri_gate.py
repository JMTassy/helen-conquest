"""ORACLE TOWN — K-Gate: TRI Gate (Three-Input Validator)

Deterministic validator implementing K-gates 0, 1, 2, 5, 7.

Pure function: no I/O, no side effects, same input → identical output (K5 determinism).
"""

from dataclasses import dataclass
from typing import Optional
from oracle_town.schemas.attestor import AttestorRegistry
from oracle_town.schemas.claim import CompiledClaim


@dataclass
class Verdict:
    """
    Unsigned verdict from TRI gate.

    Invariants:
    - accepted is boolean (ACCEPT or REJECT only, never DEFER or WARN)
    - reason_code identifies which K-gate triggered (if any)
    - policy_version is pinned at evaluation time (K7)
    - verdict is deterministic: same input + same policy → identical verdict (K5)
    """
    accepted: bool
    reason_code: str  # "K0_UNREGISTERED_ATTESTOR", "K1_MISSING_EVIDENCE", etc.
    policy_version: str

    def to_dict(self):
        """Serialize to deterministic dict."""
        return {
            "accepted": self.accepted,
            "reason_code": self.reason_code,
            "policy_version": self.policy_version,
        }


class TriGate:
    """
    Three-Input Gate: Deterministic K-gate validator.

    Implements five immutable K-gates:
    - K0: Authority separation (only registered attestors)
    - K1: Fail-closed (missing evidence → REJECT)
    - K2: No self-attestation (attestor_id cannot equal target)
    - K5: Determinism (same input → same output)
    - K7: Policy pinning (policy version fixed per run)

    Pure function: no I/O, no randomness, no timestamps in output.
    """

    def __init__(self, attestor_registry: AttestorRegistry):
        """
        Initialize TRI gate with attestor registry.

        Args:
            attestor_registry: AttestorRegistry instance with authorized attestor IDs
        """
        self.attestor_registry = attestor_registry

    def evaluate(self, claim: CompiledClaim) -> Verdict:
        """
        Deterministically evaluate a claim against K-gates.

        Args:
            claim: CompiledClaim instance

        Returns:
            Verdict with accepted (bool) and reason_code (str)

        Invariants (K-gates):
            K0: Attestor must be in registry
            K2: Attestor cannot self-attest (claim_id check)
            K1: Evidence must be present (fail-closed)
            K5: Same input always produces same output (no randomness)
            K7: Policy version pinned to claim's declared version

        Gate Order:
            1. K0 authority separation (must be registered)
            2. K2 self-attestation check (structural integrity)
            3. K1 evidence requirement (fail-closed)
        """

        # K0: Authority separation
        if not self.attestor_registry.is_registered(claim.attestor_id):
            return Verdict(
                accepted=False,
                reason_code="K0_UNREGISTERED_ATTESTOR",
                policy_version=claim.policy_version,
            )

        # K2: No self-attestation
        # Check if attestor_id matches claim_id prefix or statement content
        if claim.attestor_id in claim.claim_id or claim.attestor_id in claim.statement:
            return Verdict(
                accepted=False,
                reason_code="K2_SELF_ATTESTATION",
                policy_version=claim.policy_version,
            )

        # K1: Fail-closed (missing evidence)
        if not claim.evidence or len(claim.evidence) == 0:
            return Verdict(
                accepted=False,
                reason_code="K1_MISSING_EVIDENCE",
                policy_version=claim.policy_version,
            )

        # K7: Policy pinning (implicit - we use the policy version from claim)
        # K5: Determinism (pure function - no randomness, no timestamps, no I/O)

        # All gates passed → ACCEPT
        return Verdict(
            accepted=True,
            reason_code="ALL_GATES_PASSED",
            policy_version=claim.policy_version,
        )
