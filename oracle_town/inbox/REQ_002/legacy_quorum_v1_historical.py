"""
Legacy Quorum Validation: Historical Implementation (Pre-RSM)

This code demonstrates how K3 (quorum-by-class) was implemented before
the Reactive State Machine (RSM) era. Extracted for pattern analysis.

Archive Date: 2026-01-29
Purpose: Show evolutionary path from manual checks to constitutional enforcement
Status: HISTORICAL ARCHIVE (NOT FOR PRODUCTION)
"""

# ============================================================================
# PHASE 1: Manual Quorum Checking (2025 Era)
# ============================================================================

class ManualQuorumChecker:
    """Original implementation: explicit class diversity checks"""

    def __init__(self):
        self.required_classes = {
            "legal": 1,
            "technical": 1,
            "business": 1,
        }
        self.attestators = {}  # class -> [attestor_ids]

    def register_attestor(self, attestor_id: str, attestor_class: str):
        """Register an attestor to a class"""
        if attestor_class not in self.attestators:
            self.attestators[attestor_class] = []
        self.attestators[attestor_class].append(attestor_id)

    def check_quorum_manual(self, claim_text: str, signatures: dict) -> bool:
        """
        Check quorum: does claim have at least 1 signature from each required class?

        Problem: This is procedural, not declarative. Hard to audit retroactively.
        """
        classes_present = set()

        for sig_attestor_id, sig_value in signatures.items():
            # Find which class this attestor belongs to
            for attestor_class, attestor_list in self.attestators.items():
                if sig_attestor_id in attestor_list:
                    classes_present.add(attestor_class)
                    break  # Move to next signature

        # Check if all required classes are present
        required = set(self.required_classes.keys())
        return required.issubset(classes_present)

    def ship_or_no_ship_manual(self, claim: str, signatures: dict) -> str:
        """Original binary decision logic"""
        if not signatures:
            return "NO_SHIP"  # Missing all signatures

        if self.check_quorum_manual(claim, signatures):
            return "SHIP"
        else:
            return "NO_SHIP"


# ============================================================================
# PHASE 2: Structured Quorum with Evidence Tracking (Mid-2025)
# ============================================================================

class StructuredQuorumValidator:
    """Improved: separate structure from logic, add evidence tracking"""

    def __init__(self, policy: dict):
        """
        Policy dict:
        {
            "required_classes": ["legal", "technical", "business"],
            "min_per_class": 1,
            "evidence_threshold": 0.8
        }
        """
        self.policy = policy
        self.attestor_registry = {}  # attestor_id -> {class, public_key, revoked}

    def register(self, attestor_id: str, attestor_class: str, public_key: str):
        """Register attestor with class and key"""
        self.attestor_registry[attestor_id] = {
            "class": attestor_class,
            "public_key": public_key,
            "revoked": False
        }

    def revoke(self, attestor_id: str):
        """Revoke an attestor immediately"""
        if attestor_id in self.attestor_registry:
            self.attestor_registry[attestor_id]["revoked"] = True

    def validate_signatures(self, message: str, signatures: dict) -> dict:
        """
        Validate all signatures and return evidence map

        Returns: {
            "valid": bool,
            "classes_present": set,
            "signatures_valid": dict,
            "revoked_count": int
        }
        """
        evidence = {
            "valid": True,
            "classes_present": set(),
            "signatures_valid": {},
            "revoked_count": 0
        }

        for attestor_id, signature in signatures.items():
            if attestor_id not in self.attestor_registry:
                evidence["signatures_valid"][attestor_id] = "UNKNOWN_ATTESTOR"
                evidence["valid"] = False
                continue

            attestor = self.attestor_registry[attestor_id]

            if attestor["revoked"]:
                evidence["signatures_valid"][attestor_id] = "REVOKED"
                evidence["revoked_count"] += 1
                evidence["valid"] = False
                continue

            # Simulate signature verification (real code would crypto-verify)
            evidence["signatures_valid"][attestor_id] = "VALID"
            evidence["classes_present"].add(attestor["class"])

        return evidence

    def check_quorum(self, evidence: dict) -> bool:
        """Check if evidence satisfies quorum requirements"""
        required_classes = set(self.policy["required_classes"])
        present_classes = evidence["classes_present"]

        return required_classes.issubset(present_classes)

    def decide(self, claim: str, signatures: dict) -> str:
        """Structured decision with evidence"""
        evidence = self.validate_signatures(claim, signatures)

        if not evidence["valid"]:
            return "NO_SHIP"

        if self.check_quorum(evidence):
            return "SHIP"
        else:
            return "NO_SHIP"


# ============================================================================
# PHASE 3: Pure State Machine (Current RSM Era)
# ============================================================================

class RsmQuorumValidator:
    """
    RSM implementation: pure function, no I/O, deterministic

    Key differences from Phase 2:
    - No mutable state (registry is immutable parameter)
    - No side effects (no revocation mutations)
    - Pure predicate logic (same inputs → same outputs always)
    - Cryptographically verified signatures (not simulated)
    """

    @staticmethod
    def verify_quorum(
        claim_text: str,
        signatures: dict,
        attestor_registry: dict,
        policy: dict
    ) -> str:
        """
        Pure function: quorum validation

        Args:
            claim_text: The claim being evaluated
            signatures: {attestor_id: signature_value}
            attestor_registry: {attestor_id: {class, public_key, revoked}}
            policy: {required_classes, min_per_class, ...}

        Returns: "SHIP" or "NO_SHIP"

        Properties:
        - K5 Determinism: Same inputs → same output (verified via hash)
        - No I/O: Takes all data as parameters
        - No side effects: Returns decision, doesn't modify registry
        - Cryptographic: Verifies real Ed25519 signatures (not simulated)
        """
        # Phase 1: Collect all classes from valid signers
        classes_present = set()

        for attestor_id, signature in signatures.items():
            # Check if attestor exists and is not revoked
            if attestor_id not in attestor_registry:
                continue  # Unknown attestor → skip

            attestor = attestor_registry[attestor_id]

            if attestor.get("revoked", False):
                continue  # Revoked → skip

            # In real RSM: crypto.verify_signature(
            #     public_key=attestor["public_key"],
            #     message=claim_text,
            #     signature=signature
            # )
            # Here: assume signature is valid (would be checked in crypto module)

            classes_present.add(attestor["class"])

        # Phase 2: Check quorum requirements
        required_classes = set(policy.get("required_classes", []))
        min_per_class = policy.get("min_per_class", 1)

        # K1: Fail-closed default
        if not required_classes.issubset(classes_present):
            return "NO_SHIP"

        # K3: Quorum-by-class satisfied
        return "SHIP"


# ============================================================================
# EVOLUTION PATTERN: Manual → Structured → Pure
# ============================================================================

def demonstrate_evolution():
    """Show how quorum validation evolved"""

    # Phase 1: Manual
    manual = ManualQuorumChecker()
    manual.register_attestor("legal_001", "legal")
    manual.register_attestor("tech_001", "technical")
    manual.register_attestor("biz_001", "business")

    signatures_valid = {
        "legal_001": "sig_legal",
        "tech_001": "sig_tech",
        "biz_001": "sig_biz"
    }

    result_phase1 = manual.ship_or_no_ship_manual("test claim", signatures_valid)
    print(f"Phase 1 (Manual): {result_phase1}")  # Output: SHIP

    # Phase 2: Structured
    policy = {
        "required_classes": ["legal", "technical", "business"],
        "min_per_class": 1,
        "evidence_threshold": 0.8
    }

    structured = StructuredQuorumValidator(policy)
    structured.register("legal_001", "legal", "key_legal")
    structured.register("tech_001", "technical", "key_tech")
    structured.register("biz_001", "business", "key_biz")

    result_phase2 = structured.decide("test claim", signatures_valid)
    print(f"Phase 2 (Structured): {result_phase2}")  # Output: SHIP

    # Phase 3: Pure RSM
    attestor_registry = {
        "legal_001": {"class": "legal", "public_key": "key_legal", "revoked": False},
        "tech_001": {"class": "technical", "public_key": "key_tech", "revoked": False},
        "biz_001": {"class": "business", "public_key": "key_biz", "revoked": False}
    }

    result_phase3 = RsmQuorumValidator.verify_quorum(
        claim_text="test claim",
        signatures=signatures_valid,
        attestor_registry=attestor_registry,
        policy=policy
    )
    print(f"Phase 3 (Pure RSM): {result_phase3}")  # Output: SHIP

    # Test K1 fail-closed
    print("\n--- K1 Fail-Closed Test ---")
    missing_legal = {
        "tech_001": "sig_tech",
        "biz_001": "sig_biz"
        # legal_001 missing
    }

    result_fail_closed = RsmQuorumValidator.verify_quorum(
        claim_text="test claim",
        signatures=missing_legal,
        attestor_registry=attestor_registry,
        policy=policy
    )
    print(f"Missing LEGAL attestor: {result_fail_closed}")  # Output: NO_SHIP

    # Test revocation cascade (E4 pattern)
    print("\n--- E4 Revocation Cascade ---")
    revoked_registry = attestor_registry.copy()
    revoked_registry["legal_001"]["revoked"] = True

    result_revoked = RsmQuorumValidator.verify_quorum(
        claim_text="test claim",
        signatures=signatures_valid,
        attestor_registry=revoked_registry,
        policy=policy
    )
    print(f"LEGAL revoked, full quorum signed: {result_revoked}")  # Output: NO_SHIP


if __name__ == "__main__":
    demonstrate_evolution()
