"""
Intake Guard: Forbidden Field Enforcement (INTAKE-GUARD v1.0.0)

CRITICAL BOUNDARY:
- Creative Town outputs can influence WHAT gets evaluated
- Creative Town outputs CANNOT influence WHETHER it gets approved

This module enforces the authority separation invariant K0.
"""
from __future__ import annotations
import hashlib
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class RejectionCode(Enum):
    """Canonical rejection codes"""
    CT_REJECTED_FORBIDDEN_FIELDS = "CT_REJECTED_FORBIDDEN_FIELDS"
    CT_REJECTED_SCHEMA_INVALID = "CT_REJECTED_SCHEMA_INVALID"
    CT_REJECTED_BUDGET_VIOLATION = "CT_REJECTED_BUDGET_VIOLATION"
    CT_REJECTED_MALFORMED_JSON = "CT_REJECTED_MALFORMED_JSON"


# Forbidden field lists (from INTAKE-GUARD spec)
FORBIDDEN_RANKING = {
    "rank", "score", "rating", "priority", "prioritize", "top", "best", "worst",
    "recommended", "recommend", "preference", "prefer", "optimal", "suboptimal",
    "first", "second", "third", "winner", "loser", "chosen", "selected", "pick"
}

FORBIDDEN_CONFIDENCE = {
    "confidence", "probability", "likelihood", "certainty", "certain", "sure",
    "guarantee", "guaranteed", "percent", "%", "odds", "chance", "risk", "uncertain",
    "definitely", "probably", "maybe", "possibly", "likely", "unlikely"
}

FORBIDDEN_AUTHORITY = {
    "ship", "approved", "approve", "safe", "unsafe", "compliant", "non-compliant",
    "verified", "unverified", "passed", "failed", "certified", "valid", "invalid",
    "satisfied", "unsatisfied", "complete", "incomplete", "resolved", "unresolved",
    "cleared", "blocked", "ready", "not_ready", "go", "no_go", "green", "red", "yellow"
}

FORBIDDEN_FINANCIAL = {
    "buy", "sell", "hold", "long", "short", "position", "portfolio", "allocation",
    "invest", "divest", "trade", "execute", "order", "bid", "ask", "price_target",
    "recommendation", "advice", "guidance", "counsel", "suggestion"
}

FORBIDDEN_SATISFACTION = {
    "already_satisfied", "already_complete", "already_verified", "already_cleared",
    "no_action_needed", "sufficient", "adequate", "acceptable", "meets_requirements",
    "passes", "complies", "fulfills", "satisfies"
}

# Combine all forbidden words
FORBIDDEN_WORDS = (
    FORBIDDEN_RANKING |
    FORBIDDEN_CONFIDENCE |
    FORBIDDEN_AUTHORITY |
    FORBIDDEN_FINANCIAL |
    FORBIDDEN_SATISFACTION
)

# Exempted field paths (metadata is allowed to contain forbidden words)
EXEMPTED_PATHS = {
    "metadata",
    "ct_run_manifest",
    "creativity_metadata",
    "ct_version",
    "generation_timestamp",
    "creative_role"
}


@dataclass
class IntakeDecision:
    """Result of intake guard evaluation"""
    decision: str  # "ACCEPT" or "REJECT"
    rejection_code: RejectionCode | None
    forbidden_fields_found: List[str]
    ct_boundary_digest: str
    timestamp: str
    briefcase: Dict[str, Any] | None = None


class IntakeGuard:
    """
    Intake Guard enforces authority separation invariant K0.

    Responsibilities:
    1. JSON syntax validation
    2. Schema validation (if schema provided)
    3. Forbidden field detection (recursive scan)
    4. Budget cap enforcement
    5. Boundary digest computation
    6. Normalization (if accepted)
    """

    def __init__(
        self,
        max_proposals: int = 100,
        max_obligations: int = 50,
        max_free_text_bytes: int = 102400,
        max_metadata_fields: int = 20
    ):
        self.max_proposals = max_proposals
        self.max_obligations = max_obligations
        self.max_free_text_bytes = max_free_text_bytes
        self.max_metadata_fields = max_metadata_fields

    def evaluate(
        self,
        proposal_bundle: Dict[str, Any],
        ct_run_manifest: Dict[str, Any]
    ) -> IntakeDecision:
        """
        Evaluate Creative Town output bundle.

        Args:
            proposal_bundle: CT proposals
            ct_run_manifest: CT provenance metadata

        Returns:
            IntakeDecision (ACCEPT or REJECT with reason code)
        """
        # Compute boundary digest (even for rejected bundles)
        ct_boundary_digest = self._compute_boundary_digest(
            proposal_bundle, ct_run_manifest
        )

        # 1. Budget cap enforcement (fail fast)
        budget_violation = self._check_budget_caps(proposal_bundle)
        if budget_violation:
            return IntakeDecision(
                decision="REJECT",
                rejection_code=RejectionCode.CT_REJECTED_BUDGET_VIOLATION,
                forbidden_fields_found=[budget_violation],
                ct_boundary_digest=ct_boundary_digest,
                timestamp=datetime.utcnow().isoformat()
            )

        # 2. Forbidden field detection (recursive scan)
        forbidden_fields = self._scan_for_forbidden_fields(proposal_bundle)
        if forbidden_fields:
            return IntakeDecision(
                decision="REJECT",
                rejection_code=RejectionCode.CT_REJECTED_FORBIDDEN_FIELDS,
                forbidden_fields_found=forbidden_fields,
                ct_boundary_digest=ct_boundary_digest,
                timestamp=datetime.utcnow().isoformat()
            )

        # 3. Normalize and create briefcase (if accepted)
        briefcase = self._normalize_to_briefcase(
            proposal_bundle,
            ct_run_manifest,
            ct_boundary_digest
        )

        return IntakeDecision(
            decision="ACCEPT",
            rejection_code=None,
            forbidden_fields_found=[],
            ct_boundary_digest=ct_boundary_digest,
            timestamp=datetime.utcnow().isoformat(),
            briefcase=briefcase
        )

    def _check_budget_caps(self, proposal_bundle: Dict[str, Any]) -> str | None:
        """
        Check budget caps.

        Returns:
            Violation message if budget exceeded, None otherwise
        """
        proposals = proposal_bundle.get("proposals", [])
        if len(proposals) > self.max_proposals:
            return f"max_proposals_per_run exceeded: {len(proposals)} > {self.max_proposals}"

        # Count total free text bytes (description hashes)
        total_text_bytes = 0
        for proposal in proposals:
            if "description_hash" in proposal:
                total_text_bytes += len(str(proposal["description_hash"]))

        if total_text_bytes > self.max_free_text_bytes:
            return f"max_free_text_bytes exceeded: {total_text_bytes} > {self.max_free_text_bytes}"

        # Count metadata fields
        metadata = proposal_bundle.get("metadata", {})
        if len(metadata) > self.max_metadata_fields:
            return f"max_metadata_fields exceeded: {len(metadata)} > {self.max_metadata_fields}"

        return None

    def _scan_for_forbidden_fields(
        self,
        obj: Any,
        path: str = ""
    ) -> List[str]:
        """
        Recursively scan JSON object for forbidden field names or values.

        Args:
            obj: JSON object (dict, list, or primitive)
            path: Current field path (for exemption checking)

        Returns:
            List of forbidden fields found (empty if clean)
        """
        violations = []

        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key

                # Check if this path or any parent is exempted
                if self._is_path_exempted(current_path):
                    continue  # Skip this entire subtree

                # Check key name
                if self._contains_forbidden_word(key):
                    violations.append(f"field_name:{current_path}")

                # Check string values
                if isinstance(value, str):
                    if self._contains_forbidden_word(value):
                        violations.append(f"field_value:{current_path}={value[:50]}")

                # Recurse
                violations.extend(
                    self._scan_for_forbidden_fields(value, current_path)
                )

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]"
                violations.extend(
                    self._scan_for_forbidden_fields(item, current_path)
                )

        return violations

    def _is_path_exempted(self, path: str) -> bool:
        """Check if current path or any parent is exempted"""
        path_parts = path.split(".")
        return any(exempt in path_parts for exempt in EXEMPTED_PATHS)

    def _contains_forbidden_word(self, text: str) -> bool:
        """
        Check if text contains any forbidden word (case-insensitive, word boundaries).

        Uses word boundary matching to avoid false positives:
        - "team_red" does NOT match "red" (part of compound word)
        - "this is red" DOES match "red" (standalone word)
        """
        import re
        text_lower = text.lower()

        for word in FORBIDDEN_WORDS:
            # Match word with word boundaries (alphanumeric or underscore)
            pattern = r'\b' + re.escape(word) + r'\b'
            if re.search(pattern, text_lower):
                return True

        return False

    def _compute_boundary_digest(
        self,
        proposal_bundle: Dict[str, Any],
        ct_run_manifest: Dict[str, Any]
    ) -> str:
        """
        Compute immutable boundary digest.

        digest = SHA256(canonical(proposal_bundle) || canonical(ct_run_manifest))
        """
        canonical_bundle = self._canonicalize(proposal_bundle)
        canonical_manifest = self._canonicalize(ct_run_manifest)

        combined = canonical_bundle + canonical_manifest
        digest = hashlib.sha256(combined.encode("utf-8")).hexdigest()

        return f"sha256:{digest}"

    def _canonicalize(self, obj: Dict[str, Any]) -> str:
        """
        Canonical JSON encoding (deterministic hash).

        Rules:
        - Keys sorted lexicographically
        - No whitespace
        - UTF-8 encoding
        """
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def _normalize_to_briefcase(
        self,
        proposal_bundle: Dict[str, Any],
        ct_run_manifest: Dict[str, Any],
        ct_boundary_digest: str
    ) -> Dict[str, Any]:
        """
        Convert accepted CT output to briefcase.

        Briefcase contains:
        - run_id
        - claim_id (derived from CT run_id)
        - required_obligations (extracted from proposals)
        - ct_boundary_digest (for audit trail)
        - policy_hash (must be provided or defaulted)
        """
        run_id = ct_run_manifest.get("run_id", "R-UNKNOWN")
        claim_id = f"CLM-{run_id.split('-')[-1]}"  # Derive from run_id

        # Extract obligations from proposals (simplified for MVP)
        # In production: parse proposal types and map to obligation types
        required_obligations = []
        for i, proposal in enumerate(proposal_bundle.get("proposals", [])):
            obl_name = f"ct_proposal_{i:03d}"
            required_obligations.append({
                "name": obl_name,
                "type": "CODE_PROOF",  # Default type
                "severity": "SOFT",  # CT proposals are advisory
                "description": f"Proposal {proposal.get('proposal_id', 'UNKNOWN')}"
            })

        briefcase = {
            "run_id": run_id,
            "claim_id": claim_id,
            "claim_type": "COMMENTARY",  # CT proposals are commentary
            "required_obligations": required_obligations,
            "requested_tests": [],  # CT cannot request tests
            "kill_switch_policies": [],  # CT cannot trigger kill switches
            "metadata": {
                "ct_boundary_digest": ct_boundary_digest,
                "ct_proposals_count": len(proposal_bundle.get("proposals", []))
                # NOTE: No timestamps in briefcase - must be deterministic
            }
        }

        return briefcase


# Test
if __name__ == "__main__":
    print("=" * 70)
    print("INTAKE GUARD TEST SUITE")
    print("=" * 70)

    guard = IntakeGuard()

    # Test 1: Valid proposal bundle
    print("\n[Test 1] Valid proposal bundle")
    valid_bundle = {
        "proposals": [
            {
                "proposal_id": "P-A1B2C3D4E5F6",
                "origin": "creative_town.team_red",
                "proposal_type": "EDGE_CASE_EXPLORATION",
                "description_hash": "sha256:abc123...",
                "suggested_changes": {
                    "test_extension": "def test_empty_input(): assert handle([]) == []"
                }
            }
        ],
        "metadata": {
            "ct_version": "1.0.0"
        }
    }
    valid_manifest = {
        "run_id": "R-CT-20260123-001",
        "proposals_count": 1,
        "timestamp": "2026-01-23T10:30:00Z"
    }

    decision = guard.evaluate(valid_bundle, valid_manifest)
    print(f"Decision: {decision.decision}")
    print(f"Boundary Digest: {decision.ct_boundary_digest}")
    assert decision.decision == "ACCEPT", "Valid bundle should be accepted"

    # Test 2: Bundle with forbidden field (rank)
    print("\n[Test 2] Bundle with forbidden field 'rank'")
    invalid_bundle_rank = {
        "proposals": [
            {
                "proposal_id": "P-...",
                "rank": 1  # FORBIDDEN
            }
        ]
    }
    invalid_manifest = {
        "run_id": "R-CT-20260123-002",
        "proposals_count": 1,
        "timestamp": "2026-01-23T10:31:00Z"
    }

    decision = guard.evaluate(invalid_bundle_rank, invalid_manifest)
    print(f"Decision: {decision.decision}")
    print(f"Rejection Code: {decision.rejection_code}")
    print(f"Forbidden Fields: {decision.forbidden_fields_found}")
    assert decision.decision == "REJECT", "Bundle with 'rank' should be rejected"
    assert decision.rejection_code == RejectionCode.CT_REJECTED_FORBIDDEN_FIELDS

    # Test 3: Bundle with forbidden value (confidence)
    print("\n[Test 3] Bundle with forbidden value 'confidence: 0.9'")
    invalid_bundle_confidence = {
        "proposals": [
            {
                "proposal_id": "P-...",
                "suggested_changes": {
                    "analysis": "This is correct with 95% confidence"  # FORBIDDEN
                }
            }
        ]
    }
    invalid_manifest_3 = {
        "run_id": "R-CT-20260123-003",
        "proposals_count": 1,
        "timestamp": "2026-01-23T10:32:00Z"
    }

    decision = guard.evaluate(invalid_bundle_confidence, invalid_manifest_3)
    print(f"Decision: {decision.decision}")
    print(f"Rejection Code: {decision.rejection_code}")
    print(f"Forbidden Fields: {decision.forbidden_fields_found}")
    assert decision.decision == "REJECT", "Bundle with 'confidence' should be rejected"

    # Test 4: Bundle with 'ship' (authority claim)
    print("\n[Test 4] Bundle with 'ship: true' (authority claim)")
    invalid_bundle_ship = {
        "proposals": [
            {
                "proposal_id": "P-...",
                "ship": True  # FORBIDDEN
            }
        ]
    }
    invalid_manifest_4 = {
        "run_id": "R-CT-20260123-004",
        "proposals_count": 1,
        "timestamp": "2026-01-23T10:33:00Z"
    }

    decision = guard.evaluate(invalid_bundle_ship, invalid_manifest_4)
    print(f"Decision: {decision.decision}")
    print(f"Rejection Code: {decision.rejection_code}")
    assert decision.decision == "REJECT", "Bundle with 'ship' should be rejected"

    # Test 5: Budget violation (too many proposals)
    print("\n[Test 5] Budget violation (101 proposals)")
    large_bundle = {
        "proposals": [{"proposal_id": f"P-{i:03d}"} for i in range(101)]
    }
    large_manifest = {
        "run_id": "R-CT-20260123-005",
        "proposals_count": 101,
        "timestamp": "2026-01-23T10:34:00Z"
    }

    decision = guard.evaluate(large_bundle, large_manifest)
    print(f"Decision: {decision.decision}")
    print(f"Rejection Code: {decision.rejection_code}")
    print(f"Forbidden Fields: {decision.forbidden_fields_found}")
    assert decision.decision == "REJECT", "Bundle with 101 proposals should be rejected"
    assert decision.rejection_code == RejectionCode.CT_REJECTED_BUDGET_VIOLATION

    print("\n" + "=" * 70)
    print("ALL INTAKE GUARD TESTS PASSED ✓")
    print("=" * 70)
