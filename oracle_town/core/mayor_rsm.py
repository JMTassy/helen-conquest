"""
Mayor Agent (RSM v0): Pure Predicate with Quorum-by-Class Enforcement

CRITICAL: Mayor is a pure function over (policy, briefcase, ledger).
NO LLM outputs. NO environment reads. NO timestamps (except logging).
"""
from __future__ import annotations
import hashlib
import json
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from oracle_town.core.policy import Policy, QuorumRule
from oracle_town.core.crypto import verify_ed25519, build_canonical_message, canonical_json_bytes
from oracle_town.core.key_registry import KeyRegistry


@dataclass
class Attestation:
    """Attestation (receipt) from ledger"""
    attestation_id: str
    run_id: str
    claim_id: str
    obligation_name: str
    attestor_id: str
    attestor_class: str
    policy_hash: str
    evidence_digest: str
    signing_key_id: str
    signature: str
    policy_match: int  # 0 or 1 (binary)
    timestamp: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Attestation:
        return cls(
            attestation_id=data.get("attestation_id", ""),
            run_id=data["run_id"],
            claim_id=data["claim_id"],
            obligation_name=data["obligation_name"],
            attestor_id=data["attestor_id"],
            attestor_class=data["attestor_class"],
            policy_hash=data["policy_hash"],
            evidence_digest=data["evidence_digest"],
            signing_key_id=data["signing_key_id"],
            signature=data["signature"],
            policy_match=data["policy_match"],
            timestamp=data["timestamp"]
        )


@dataclass
class Obligation:
    """Obligation from briefcase"""
    name: str
    type: str
    severity: str  # HARD or SOFT
    description: str
    required_evidence: List[str] = field(default_factory=list)
    required_attestor_classes: List[str] = field(default_factory=lambda: None)  # Quorum-by-class (explicit)
    min_quorum: int = None  # Minimum number of distinct classes required

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Obligation:
        return cls(
            name=data["name"],
            type=data["type"],
            severity=data["severity"],
            description=data.get("description", ""),
            required_evidence=data.get("required_evidence", []),
            required_attestor_classes=data.get("required_attestor_classes"),
            min_quorum=data.get("min_quorum")
        )


@dataclass
class DecisionRecord:
    """Immutable decision record"""
    run_id: str
    claim_id: str
    decision: str  # SHIP or NO_SHIP
    policy_hash: str
    briefcase_digest: str
    ledger_digest: str
    blocking_reasons: List[str]
    decision_digest: str  # For replay verification
    timestamp: str
    code_version: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "claim_id": self.claim_id,
            "decision": self.decision,
            "policy_hash": self.policy_hash,
            "briefcase_digest": self.briefcase_digest,
            "ledger_digest": self.ledger_digest,
            "blocking_reasons": self.blocking_reasons,
            "decision_digest": self.decision_digest,
            "timestamp": self.timestamp,
            "code_version": self.code_version
        }


class MayorRSM:
    """
    Mayor Agent with RSM v0 enforcement.

    Pure predicate: decision = f(policy, briefcase, ledger)

    Constitutional Rules (ordered):
    1. Policy hash mismatch → NO_SHIP (fail-closed)
    1.5. Signature verification → invalid attestations dropped
    2. Revoked key/attestor → attestation invalid
    3. Missing quorum-by-class → NO_SHIP
    4. Obligation not satisfied (policy_match=0) → NO_SHIP
    5. Missing evidence digest → NO_SHIP (NO_RECEIPT = NO_SHIP)
    6. All checks pass → SHIP
    """

    def __init__(self, code_version: str = "oracle_town_rsm_v1.0.0", public_keys_path: str = None):
        self.code_version = code_version
        self.public_keys = None
        self.key_registry = None
        if public_keys_path:
            # public_keys_path expected to be path to public_keys.json
            manifest_path = None
            try:
                import os
                manifest_path = os.path.join(os.path.dirname(public_keys_path), "registry_manifest.json")
            except Exception:
                manifest_path = None

            self.key_registry = KeyRegistry(public_keys_path, manifest_path)
            self.public_keys = self.key_registry.registry

    def _load_public_keys(self, path: str) -> Dict[str, Any]:
        """Load public key registry from JSON file"""
        import os
        if not os.path.exists(path):
            raise FileNotFoundError(f"Public keys registry not found: {path}")
        with open(path, 'r') as f:
            return json.load(f)

    def decide(
        self,
        policy: Policy,
        briefcase: Dict[str, Any],
        ledger: Dict[str, Any]
    ) -> DecisionRecord:
        """
        Pure predicate: produce binary verdict.

        Args:
            policy: Policy object (with quorum rules, revocation lists)
            briefcase: Canonical kernel input (obligations)
            ledger: Attestations (receipts) from Factory

        Returns:
            DecisionRecord with SHIP or NO_SHIP + reasons
        """
        run_id = briefcase["run_id"]
        claim_id = briefcase["claim_id"]

        # Parse obligations and attestations
        obligations = [Obligation.from_dict(o) for o in briefcase["required_obligations"]]
        attestations = [Attestation.from_dict(a) for a in ledger.get("attestations", [])]

        # Compute digests (for determinism)
        # NOTE: Must exclude self-referential digest fields
        briefcase_digest = self._compute_digest(briefcase)

        # Exclude ledger_digest field when computing digest
        ledger_copy = dict(ledger)
        ledger_copy.pop("ledger_digest", None)
        ledger_digest = self._compute_digest(ledger_copy)

        # Apply constitutional rules
        decision, blocking_reasons = self._apply_constitutional_rules(
            policy, obligations, attestations, briefcase, ledger
        )

        # Compute decision digest (for replay verification)
        decision_digest = self._compute_decision_digest(
            run_id, claim_id, decision, policy.policy_hash, briefcase_digest, ledger_digest
        )

        return DecisionRecord(
            run_id=run_id,
            claim_id=claim_id,
            decision=decision,
            policy_hash=policy.policy_hash,
            briefcase_digest=briefcase_digest,
            ledger_digest=ledger_digest,
            blocking_reasons=blocking_reasons,
            decision_digest=decision_digest,
            timestamp=datetime.utcnow().isoformat(),
            code_version=self.code_version
        )

    def _apply_constitutional_rules(
        self,
        policy: Policy,
        obligations: List[Obligation],
        attestations: List[Attestation],
        briefcase: Dict[str, Any],
        ledger: Dict[str, Any]
    ) -> Tuple[str, List[str]]:
        """
        Apply constitutional rules in strict order.

        Returns:
            (decision, blocking_reasons)
        """
        blocking_reasons = []

        # Rule 1: Policy hash verification
        policy_hash_in_briefcase = briefcase.get("metadata", {}).get("policy_hash")
        policy_hash_in_ledger = ledger.get("policy_hash")

        if policy_hash_in_briefcase and policy_hash_in_briefcase != policy.policy_hash:
            return ("NO_SHIP", ["Policy hash mismatch in briefcase"])

        if policy_hash_in_ledger and policy_hash_in_ledger != policy.policy_hash:
            return ("NO_SHIP", ["Policy hash mismatch in ledger"])

        # Rule 1.5: Attestation policy hash must match current policy
        for att in attestations:
            if att.policy_hash != policy.policy_hash:
                blocking_reasons.append(
                    f"POLICY_HASH_MISMATCH: attestation {att.attestation_id} signed for policy {att.policy_hash[:30]}..., "
                    f"but current policy is {policy.policy_hash[:30]}... (obligation: {att.obligation_name})"
                )

        if blocking_reasons:
            return ("NO_SHIP", blocking_reasons)

        # Rule 1.6: Signature verification (if key registry available)
        if self.key_registry:
            # If policy pins a registry, ensure it matches
            policy_registry_hash = getattr(policy, 'key_registry_hash', None)
            if policy_registry_hash and self.key_registry.registry_hash != policy_registry_hash:
                return ("NO_SHIP", [f"REGISTRY_HASH_MISMATCH: policy expects {policy_registry_hash}, got {self.key_registry.registry_hash}"])

            for att in attestations:
                sig_valid, reason = self._verify_attestation_signature(att, policy)
                if not sig_valid:
                    blocking_reasons.append(reason)

            # If any signature invalid, reject immediately
            if blocking_reasons:
                return ("NO_SHIP", blocking_reasons)

        # Rule 2: Revocation check (filter out revoked attestations)
        valid_attestations = []
        for att in attestations:
            if policy.is_key_revoked(att.signing_key_id):
                blocking_reasons.append(
                    f"Revoked key: {att.signing_key_id} (obligation: {att.obligation_name})"
                )
                continue

            if policy.is_attestor_revoked(att.attestor_id):
                blocking_reasons.append(
                    f"Revoked attestor: {att.attestor_id} (obligation: {att.obligation_name})"
                )
                continue

            valid_attestations.append(att)

        # If revocations found, reject immediately
        if blocking_reasons:
            return ("NO_SHIP", blocking_reasons)

        # Rule 3: Quorum-by-class enforcement (HARD obligations only)
        hard_obligations = [o for o in obligations if o.severity == "HARD"]

        for obl in hard_obligations:
            quorum_satisfied, reason = self._check_quorum_by_class(
                obl, valid_attestations, policy
            )

            if not quorum_satisfied:
                blocking_reasons.append(reason)

        # If any HARD obligation failed quorum, reject
        if blocking_reasons:
            return ("NO_SHIP", blocking_reasons)

        # Rule 4: Evidence digest check (NO_RECEIPT = NO_SHIP)
        for att in valid_attestations:
            if not att.evidence_digest or att.evidence_digest == "":
                blocking_reasons.append(
                    f"Missing evidence digest: {att.obligation_name}"
                )

        if blocking_reasons:
            return ("NO_SHIP", blocking_reasons)

        # Rule 5: All checks pass → SHIP
        return ("SHIP", [])

    def _check_quorum_by_class(
        self,
        obligation: Obligation,
        attestations: List[Attestation],
        policy: Policy
    ) -> Tuple[bool, str]:
        """
        Check quorum-by-class for obligation.

        Quorum rules are read from the obligation itself (not inferred from policy).
        This ensures explicit, non-ambiguous quorum requirements.

        Returns:
            (satisfied, reason)
        """
        # Get quorum requirements from obligation (HARD requirement)
        required_classes = getattr(obligation, 'required_attestor_classes', None)
        min_quorum = getattr(obligation, 'min_quorum', None)

        # If obligation doesn't declare quorum, fall back to policy
        if not required_classes or not min_quorum:
            quorum_rule = policy.get_quorum_rule(obligation.name)
            required_classes = quorum_rule.required_attestor_classes
            min_quorum = quorum_rule.min_quorum

        # Find attestations for this obligation
        obl_attestations = [
            att for att in attestations
            if att.obligation_name == obligation.name and att.policy_match == 1
        ]

        # Group by attestor_class
        classes_present = set(att.attestor_class for att in obl_attestations)

        # Check if all required classes are present
        required_classes_set = set(required_classes)
        missing_classes = required_classes_set - classes_present

        if missing_classes:
            # CRITICAL: Sort missing classes lexicographically for determinism
            sorted_missing = sorted(missing_classes)
            return (
                False,
                f"Quorum not met for '{obligation.name}': missing classes {sorted_missing}"
            )

        # Check if min_quorum satisfied
        if len(classes_present) < min_quorum:
            return (
                False,
                f"Quorum not met for '{obligation.name}': {len(classes_present)} < {min_quorum}"
            )

        return (True, "")

    def _verify_attestation_signature(
        self,
        attestation: Attestation,
        policy: Policy
    ) -> Tuple[bool, str]:
        """
        Verify Ed25519 signature for attestation.

        Checks:
        1. Signing key exists in registry
        2. Attestor class matches key registry
        3. Attestor ID is allowed for this key
        4. Signature is cryptographically valid

        Returns:
            (valid, reason)
        """
        # Use key registry to verify existence and bindings
        if not self.key_registry:
            return (False, "KEY_REGISTRY_NOT_LOADED")

        ok, code = self.key_registry.verify_attestor_binding(
            attestation.attestor_id,
            attestation.attestor_class,
            attestation.signing_key_id,
            obligation=attestation.obligation_name,
            policy_id=policy.policy_id if hasattr(policy, 'policy_id') else None
        )

        if not ok:
            # Map registry error codes to messages
            if code == "KEY_UNKNOWN":
                return (False, f"KEY_UNKNOWN: {attestation.signing_key_id} (obligation: {attestation.obligation_name})")
            if code == "KEY_CLASS_MISMATCH":
                reg = self.key_registry.get_key(attestation.signing_key_id) or {}
                return (False, f"KEY_CLASS_MISMATCH: {attestation.signing_key_id} expected class {reg.get('attestor_class')} got {attestation.attestor_class} (obligation: {attestation.obligation_name})")
            if code == "KEY_ATTESTOR_NOT_ALLOWLISTED":
                return (False, f"KEY_ATTESTOR_NOT_ALLOWLISTED: {attestation.attestor_id} not allowlisted for key {attestation.signing_key_id} (obligation: {attestation.obligation_name})")
            return (False, f"KEY_REGISTRY_ERROR: {code} (obligation: {attestation.obligation_name})")

        # Retrieve key info for signature verification
        key_info = self.key_registry.get_key(attestation.signing_key_id)

        # Build canonical message
        canonical_message = build_canonical_message(
            run_id=attestation.run_id,
            claim_id=attestation.claim_id,
            obligation_name=attestation.obligation_name,
            attestor_id=attestation.attestor_id,
            attestor_class=attestation.attestor_class,
            policy_hash=attestation.policy_hash,
            evidence_digest=attestation.evidence_digest,
            policy_match=attestation.policy_match,
            key_registry_hash=self.key_registry.registry_hash if self.key_registry else None
        )
        message_bytes = canonical_json_bytes(canonical_message)

        # Verify signature
        # Support both legacy and new registry field names
        public_key_b64 = key_info.get("public_key_base64") or key_info.get("public_key_ed25519_b64")
        if not public_key_b64:
            return (False, f"KEY_REGISTRY_MALFORMED: no public key for {attestation.signing_key_id}")
        signature_b64 = attestation.signature.replace("ed25519:", "")

        try:
            is_valid = verify_ed25519(public_key_b64, message_bytes, signature_b64)
            if not is_valid:
                return (
                    False,
                    f"Invalid signature: {attestation.attestation_id} (key: {attestation.signing_key_id}, "
                    f"obligation: {attestation.obligation_name})"
                )
        except Exception as e:
            return (
                False,
                f"Signature verification failed: {attestation.attestation_id} - {str(e)} "
                f"(obligation: {attestation.obligation_name})"
            )

        return (True, "")

    def _compute_digest(self, obj: Dict[str, Any]) -> str:
        """Compute canonical digest of object"""
        canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return f"sha256:{digest}"

    def _compute_decision_digest(
        self,
        run_id: str,
        claim_id: str,
        decision: str,
        policy_hash: str,
        briefcase_digest: str,
        ledger_digest: str
    ) -> str:
        """
        Compute decision digest for replay verification.

        digest = SHA256(run_id || claim_id || decision || policy_hash || briefcase_digest || ledger_digest)
        """
        message = {
            "run_id": run_id,
            "claim_id": claim_id,
            "decision": decision,
            "policy_hash": policy_hash,
            "briefcase_digest": briefcase_digest,
            "ledger_digest": ledger_digest
        }
        return self._compute_digest(message)


# Test
if __name__ == "__main__":
    from oracle_town.core.policy import create_default_policy
    from oracle_town.core.crypto import sign_ed25519, build_canonical_message, canonical_json_bytes
    import os

    print("=" * 70)
    print("MAYOR RSM TEST SUITE")
    print("=" * 70)

    # Try to load public keys if available
    keys_path = os.path.join(os.path.dirname(__file__), "..", "keys", "public_keys.json")
    private_keys_path = os.path.join(os.path.dirname(__file__), "..", "keys", "private_keys_TEST_ONLY.json")

    if os.path.exists(keys_path) and os.path.exists(private_keys_path):
        print(f"\n✓ Loading public keys from {keys_path}")
        mayor = MayorRSM(public_keys_path=keys_path)
        print(f"✓ Loaded {len(mayor.public_keys)} keys")

        # Load private keys for test signing
        with open(private_keys_path, 'r') as f:
            private_keys = json.load(f)
        print(f"✓ Loaded {len(private_keys)} private keys for test signing")

        # Helper to sign attestations in tests
        def sign_test_attestation(att):
            canonical_msg = build_canonical_message(
                att["run_id"], att["claim_id"], att["obligation_name"],
                att["attestor_id"], att["attestor_class"], att["policy_hash"],
                att["evidence_digest"], att["policy_match"]
            )
            msg_bytes = canonical_json_bytes(canonical_msg)
            sig = sign_ed25519(private_keys[att["signing_key_id"]], msg_bytes)
            return f"ed25519:{sig}"
    else:
        print(f"\n⚠ Keys not found")
        print("⚠ Signature verification will be skipped")
        mayor = MayorRSM()
        sign_test_attestation = lambda att: "ed25519:mock_signature"

    policy = create_default_policy()

    # Test 1: SHIP with valid quorum
    print("\n[Test 1] SHIP with valid quorum")
    briefcase = {
        "run_id": "R-20260123-001",
        "claim_id": "CLM-001",
        "claim_type": "CHANGE_REQUEST",
        "required_obligations": [
            {
                "name": "gdpr_consent_banner",
                "type": "CODE_PROOF",
                "severity": "HARD",
                "description": "Implement GDPR consent banner",
                "required_evidence": ["consent_flow_diagram"]
            }
        ],
        "requested_tests": [],
        "kill_switch_policies": [],
        "metadata": {"policy_hash": policy.policy_hash}
    }

    # Create attestations with real signatures
    attestation_ci = {
        "attestation_id": "ATT-001",
        "run_id": "R-20260123-001",
        "claim_id": "CLM-001",
        "obligation_name": "gdpr_consent_banner",
        "attestor_id": "ci_runner_001",
        "attestor_class": "CI_RUNNER",
        "policy_hash": policy.policy_hash,
        "evidence_digest": "sha256:abc123",
        "signing_key_id": "key-2026-01-ci",
        "signature": "",
        "policy_match": 1,
        "timestamp": "2026-01-23T10:00:00Z"
    }
    attestation_ci["signature"] = sign_test_attestation(attestation_ci)

    attestation_legal = {
        "attestation_id": "ATT-002",
        "run_id": "R-20260123-001",
        "claim_id": "CLM-001",
        "obligation_name": "gdpr_consent_banner",
        "attestor_id": "legal_reviewer_001",
        "attestor_class": "LEGAL",
        "policy_hash": policy.policy_hash,
        "evidence_digest": "sha256:ghi789",
        "signing_key_id": "key-2026-01-legal",
        "signature": "",
        "policy_match": 1,
        "timestamp": "2026-01-23T10:05:00Z"
    }
    attestation_legal["signature"] = sign_test_attestation(attestation_legal)

    ledger = {
        "run_id": "R-20260123-001",
        "claim_id": "CLM-001",
        "policy_hash": policy.policy_hash,
        "attestations": [attestation_ci, attestation_legal],
        "ledger_digest": "sha256:ledger001",
        "timestamp": "2026-01-23T10:10:00Z"
    }

    decision = mayor.decide(policy, briefcase, ledger)
    print(f"Decision: {decision.decision}")
    print(f"Blocking Reasons: {decision.blocking_reasons}")
    print(f"Decision Digest: {decision.decision_digest}")
    assert decision.decision == "SHIP", "Should SHIP with valid quorum"

    # Test 2: NO_SHIP with missing quorum (only 1 class present)
    print("\n[Test 2] NO_SHIP with missing quorum")

    attestation_ci_only = {
        "attestation_id": "ATT-003",
        "run_id": "R-20260123-002",
        "claim_id": "CLM-002",
        "obligation_name": "gdpr_consent_banner",
        "attestor_id": "ci_runner_001",
        "attestor_class": "CI_RUNNER",
        "policy_hash": policy.policy_hash,
        "evidence_digest": "sha256:abc123",
        "signing_key_id": "key-2026-01-ci",
        "signature": "",
        "policy_match": 1,
        "timestamp": "2026-01-23T10:00:00Z"
    }
    attestation_ci_only["signature"] = sign_test_attestation(attestation_ci_only)

    ledger_missing_quorum = {
        "run_id": "R-20260123-002",
        "claim_id": "CLM-002",
        "policy_hash": policy.policy_hash,
        "attestations": [attestation_ci_only],  # Missing LEGAL class
        "ledger_digest": "sha256:ledger002",
        "timestamp": "2026-01-23T10:10:00Z"
    }

    briefcase2 = briefcase.copy()
    briefcase2["run_id"] = "R-20260123-002"
    briefcase2["claim_id"] = "CLM-002"

    decision = mayor.decide(policy, briefcase2, ledger_missing_quorum)
    print(f"Decision: {decision.decision}")
    print(f"Blocking Reasons: {decision.blocking_reasons}")
    assert decision.decision == "NO_SHIP", "Should NO_SHIP with missing quorum"
    assert "missing classes" in decision.blocking_reasons[0], "Should mention missing classes"

    # Test 3: NO_SHIP with revoked key
    print("\n[Test 3] NO_SHIP with revoked key")
    policy_with_revocation = create_default_policy()
    from oracle_town.core.policy import RevokedKey
    policy_with_revocation.revoked_keys.append(
        RevokedKey("key-2026-01-ci", "2026-01-23T09:00:00Z", "Key compromise")
    )
    policy_with_revocation.policy_hash = policy_with_revocation.compute_hash()

    # Update briefcase and ledger to match new policy hash
    briefcase3 = briefcase.copy()
    briefcase3["metadata"] = {"policy_hash": policy_with_revocation.policy_hash}

    # Need to re-sign attestations with new policy hash
    attestation_ci_revoked = {
        "attestation_id": "ATT-004",
        "run_id": "R-20260123-001",
        "claim_id": "CLM-001",
        "obligation_name": "gdpr_consent_banner",
        "attestor_id": "ci_runner_001",
        "attestor_class": "CI_RUNNER",
        "policy_hash": policy_with_revocation.policy_hash,
        "evidence_digest": "sha256:abc123",
        "signing_key_id": "key-2026-01-ci",  # This key is revoked
        "signature": "",
        "policy_match": 1,
        "timestamp": "2026-01-23T10:00:00Z"
    }
    attestation_ci_revoked["signature"] = sign_test_attestation(attestation_ci_revoked)

    attestation_legal_revoked = {
        "attestation_id": "ATT-005",
        "run_id": "R-20260123-001",
        "claim_id": "CLM-001",
        "obligation_name": "gdpr_consent_banner",
        "attestor_id": "legal_reviewer_001",
        "attestor_class": "LEGAL",
        "policy_hash": policy_with_revocation.policy_hash,
        "evidence_digest": "sha256:ghi789",
        "signing_key_id": "key-2026-01-legal",
        "signature": "",
        "policy_match": 1,
        "timestamp": "2026-01-23T10:05:00Z"
    }
    attestation_legal_revoked["signature"] = sign_test_attestation(attestation_legal_revoked)

    ledger3 = {
        "run_id": "R-20260123-001",
        "claim_id": "CLM-001",
        "policy_hash": policy_with_revocation.policy_hash,
        "attestations": [attestation_ci_revoked, attestation_legal_revoked],
        "ledger_digest": "sha256:ledger003",
        "timestamp": "2026-01-23T10:10:00Z"
    }

    decision = mayor.decide(policy_with_revocation, briefcase3, ledger3)
    print(f"Decision: {decision.decision}")
    print(f"Blocking Reasons: {decision.blocking_reasons}")
    assert decision.decision == "NO_SHIP", "Should NO_SHIP with revoked key"
    assert "Revoked key" in decision.blocking_reasons[0], "Should mention revoked key"

    # Test 4: Replay determinism
    print("\n[Test 4] Replay determinism (10 iterations)")
    digests = []
    for i in range(10):
        decision = mayor.decide(policy, briefcase, ledger)
        digests.append(decision.decision_digest)

    assert len(set(digests)) == 1, "Decision digest should be deterministic"
    print(f"✓ All decision digests identical: {digests[0]}")

    print("\n" + "=" * 70)
    print("ALL MAYOR RSM TESTS PASSED ✓")
    print("=" * 70)
