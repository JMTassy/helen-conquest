"""
Policy Module: Policy Versioning + Change Control (POLICY-GOV v1.0.0)

Policies are the constitution. Policy changes must be governed.
"""
from __future__ import annotations
import hashlib
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class QuorumRule:
    """Quorum-by-class rule for an obligation"""
    required_attestor_classes: List[str]
    min_quorum: int


@dataclass
class RevokedKey:
    """Revoked signing key"""
    key_id: str
    revoked_at: str
    reason: str


@dataclass
class RevokedAttestor:
    """Revoked attestor"""
    attestor_id: str
    revoked_at: str
    reason: str


@dataclass
class Policy:
    """
    Governance policy with versioning, quorum rules, and revocation.

    Immutability: Policy is immutable per run (pinned by policy_hash).
    """
    policy_id: str
    policy_version: str  # MAJOR.MINOR.PATCH
    policy_hash: str  # sha256:...
    effective_date: str  # ISO 8601
    parent_policy_hash: Optional[str]
    change_rationale: Optional[str]
    quorum_rules: Dict[str, QuorumRule]  # obligation_name -> QuorumRule
    default_min_quorum: int
    revoked_keys: List[RevokedKey]
    revoked_attestors: List[RevokedAttestor]
    budget_caps: Dict[str, int]
    invariants: Dict[str, bool]
    sampling_rate: float
    metadata: Dict[str, Any]
    key_registry_hash: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization"""
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "policy_hash": self.policy_hash,
            "effective_date": self.effective_date,
            "parent_policy_hash": self.parent_policy_hash,
            "change_rationale": self.change_rationale,
            "quorum_rules": {
                "default_min_quorum": self.default_min_quorum,
                "obligation_specific_rules": {
                    obl_name: {
                        "required_attestor_classes": rule.required_attestor_classes,
                        "min_quorum": rule.min_quorum
                    }
                    for obl_name, rule in self.quorum_rules.items()
                }
            },
            "revoked_keys": [
                {"key_id": k.key_id, "revoked_at": k.revoked_at, "reason": k.reason}
                for k in self.revoked_keys
            ],
            "revoked_attestors": [
                {"attestor_id": a.attestor_id, "revoked_at": a.revoked_at, "reason": a.reason}
                for a in self.revoked_attestors
            ],
            "key_registry_hash": self.key_registry_hash,
            "budget_caps": self.budget_caps,
            "invariants": self.invariants,
            "sampling_rate": self.sampling_rate,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Policy:
        """Load policy from dict"""
        quorum_rules_data = data.get("quorum_rules", {})
        default_min_quorum = quorum_rules_data.get("default_min_quorum", 2)

        quorum_rules = {}
        for obl_name, rule_data in quorum_rules_data.get("obligation_specific_rules", {}).items():
            quorum_rules[obl_name] = QuorumRule(
                required_attestor_classes=rule_data["required_attestor_classes"],
                min_quorum=rule_data["min_quorum"]
            )

        revoked_keys = [
            RevokedKey(k["key_id"], k["revoked_at"], k["reason"])
            for k in data.get("revoked_keys", [])
        ]

        revoked_attestors = [
            RevokedAttestor(a["attestor_id"], a["revoked_at"], a["reason"])
            for a in data.get("revoked_attestors", [])
        ]

        key_registry_hash = data.get("key_registry_hash")

        return cls(
            policy_id=data["policy_id"],
            policy_version=data["policy_version"],
            policy_hash=data["policy_hash"],
            effective_date=data["effective_date"],
            parent_policy_hash=data.get("parent_policy_hash"),
            change_rationale=data.get("change_rationale"),
            quorum_rules=quorum_rules,
            default_min_quorum=default_min_quorum,
            revoked_keys=revoked_keys,
            revoked_attestors=revoked_attestors,
            budget_caps=data.get("budget_caps", {}),
            invariants=data.get("invariants", {}),
            sampling_rate=data.get("sampling_rate", 0.05),
            metadata=data.get("metadata", {})
            ,
            key_registry_hash=key_registry_hash
        )

    def compute_hash(self) -> str:
        """
        Compute deterministic policy hash.

        Returns:
            sha256:... hash of canonical policy JSON
        """
        # Create dict without policy_hash field (to avoid circular reference)
        policy_dict = self.to_dict()
        policy_dict.pop("policy_hash", None)

        # Canonical JSON encoding
        canonical = json.dumps(policy_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        return f"sha256:{digest}"

    def verify_hash(self) -> bool:
        """Verify that stored policy_hash matches computed hash"""
        computed = self.compute_hash()
        return computed == self.policy_hash

    def is_key_revoked(self, key_id: str) -> bool:
        """Check if signing key is revoked"""
        return any(k.key_id == key_id for k in self.revoked_keys)

    def is_attestor_revoked(self, attestor_id: str) -> bool:
        """Check if attestor is revoked"""
        return any(a.attestor_id == attestor_id for a in self.revoked_attestors)

    def get_quorum_rule(self, obligation_name: str) -> QuorumRule:
        """
        Get quorum rule for obligation.

        Returns obligation-specific rule if exists, else default rule.
        """
        if obligation_name in self.quorum_rules:
            return self.quorum_rules[obligation_name]

        # Default rule
        return QuorumRule(
            required_attestor_classes=["CI_RUNNER"],
            min_quorum=self.default_min_quorum
        )


def create_default_policy() -> Policy:
    """
    Create default policy for testing/MVP.

    Production: Load from policy.json file.
    """
    policy = Policy(
        policy_id="POL-ORACLE-TOWN-MVP",
        policy_version="1.0.0",
        policy_hash="",  # Will be computed
        effective_date=datetime.utcnow().isoformat(),
        parent_policy_hash=None,
        change_rationale="Initial policy for Oracle Town MVP",
        quorum_rules={
            "gdpr_consent_banner": QuorumRule(
                required_attestor_classes=["CI_RUNNER", "LEGAL"],
                min_quorum=2
            ),
            "security_audit": QuorumRule(
                required_attestor_classes=["CI_RUNNER", "SECURITY"],
                min_quorum=2
            )
        },
        default_min_quorum=1,
        revoked_keys=[],
        revoked_attestors=[],
        budget_caps={
            "max_proposals_per_run": 100,
            "max_obligations_per_run": 50,
            "max_free_text_bytes": 102400,
            "max_metadata_fields": 20
        },
        invariants={
            "fail_closed": True,
            "no_self_attestation": True,
            "quorum_by_class": True,
            "receipt_required": True,
            "determinism": True
        },
        sampling_rate=0.05,
        metadata={}
        ,
        key_registry_hash=""
    )

    # Compute and set hash
    policy.policy_hash = policy.compute_hash()

    return policy


# Test
if __name__ == "__main__":
    print("=" * 70)
    print("POLICY MODULE TEST")
    print("=" * 70)

    # Create default policy
    policy = create_default_policy()

    print(f"\nPolicy ID: {policy.policy_id}")
    print(f"Version: {policy.policy_version}")
    print(f"Hash: {policy.policy_hash}")
    print(f"Default Min Quorum: {policy.default_min_quorum}")

    # Verify hash
    assert policy.verify_hash(), "Policy hash verification failed"
    print("\n✓ Policy hash verified")

    # Test quorum rules
    rule = policy.get_quorum_rule("gdpr_consent_banner")
    print(f"\n[Quorum Rule] gdpr_consent_banner:")
    print(f"  Required Classes: {rule.required_attestor_classes}")
    print(f"  Min Quorum: {rule.min_quorum}")

    # Test revocation
    assert not policy.is_key_revoked("key-2026-01-ci"), "Key should not be revoked"
    print("\n✓ Revocation checks working")

    # Test serialization
    policy_dict = policy.to_dict()
    policy_loaded = Policy.from_dict(policy_dict)
    assert policy_loaded.policy_hash == policy.policy_hash, "Serialization failed"
    print("\n✓ Serialization roundtrip successful")

    # Test determinism (compute hash 10 times)
    print("\n[Determinism Test] Computing hash 10 times...")
    hashes = [policy.compute_hash() for _ in range(10)]
    assert len(set(hashes)) == 1, "Hash computation is not deterministic"
    print(f"✓ All hashes identical: {hashes[0]}")

    print("\n" + "=" * 70)
    print("ALL POLICY MODULE TESTS PASSED ✓")
    print("=" * 70)
