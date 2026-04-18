"""
superteam/improve.py

MODE 2: Superteam Improvement Engine

Analyzes NO_SHIP verdicts and generates improvement proposals to close receipt gaps.
Implements Mayor % evaluation scoring for proposed improvements.

Core Functionality:
- Identify missing HARD obligations
- Generate targeted improvement proposals
- Score improvements (Mayor % evaluation)
- Apply improvements to attestation bundles

Constitutional Axioms:
- A1: NO_RECEIPT = NO_SHIP (improvements target receipt gaps)
- A2: Non-sovereign production (superteam proposes, Mayor decides)
- A6: Improvement proposals are deterministic given tribunal + receipts
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
import hashlib
import json


@dataclass
class ImprovementProposal:
    """A single improvement proposal from the superteam."""
    type: str  # e.g., "add_attestation", "fix_validation", "update_obligation"
    target: str  # Obligation name or component
    description: str  # Human-readable description
    impact: str  # Expected impact (e.g., "Reduces receipt gap by 1")
    mayor_score: int  # Mayor evaluation: 0-100%
    payload: Dict[str, Any]  # Concrete changes to apply

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "target": self.target,
            "description": self.description,
            "impact": self.impact,
            "mayor_score": self.mayor_score,
            "payload": self.payload
        }


class SuperteamImprover:
    """
    Superteam Improvement Engine.

    Analyzes governance failures and proposes improvements.
    """

    VERSION = "SUPERTEAM_IMPROVER_v0.1.0"

    # Mayor scoring weights
    WEIGHTS = {
        "hard_obligation_satisfied": 40,  # Closing a HARD gap
        "soft_obligation_satisfied": 10,  # Closing a SOFT gap
        "validation_fix": 30,  # Fixing validation errors
        "policy_compliance": 20  # Improving policy compliance
    }

    def __init__(self):
        """Initialize the improver."""
        pass

    def analyze_and_propose(
        self,
        claim: Dict[str, Any],
        tribunal: Dict[str, Any],
        attestations: Dict[str, Any],
        decision: Dict[str, Any]
    ) -> List[ImprovementProposal]:
        """
        Analyze a NO_SHIP decision and generate improvement proposals.

        Args:
            claim: The claim being evaluated
            tribunal: Tribunal bundle with obligations
            attestations: Current attestation bundle
            decision: Mayor decision record (NO_SHIP)

        Returns:
            List of improvement proposals
        """
        if decision.get("decision") == "SHIP":
            # No improvements needed
            return []

        proposals = []

        # Extract blocking reasons
        blocking = decision.get("blocking", [])
        receipt_gap = decision.get("receipt_gap", 0)

        # Strategy 1: Address receipt gaps (missing HARD obligations)
        if receipt_gap > 0:
            missing_obligations = decision.get("missing_obligations", [])
            proposals.extend(
                self._propose_missing_attestations(
                    missing_obligations,
                    tribunal,
                    receipt_gap
                )
            )

        # Strategy 2: Address kill switch failures
        kill_switches = decision.get("kill_switches", [])
        for ks in kill_switches:
            if ks.get("status") != "pass":
                proposals.extend(
                    self._propose_kill_switch_fix(ks, claim)
                )

        # Strategy 3: Address validation failures (if applicable)
        # This would be for WUL-CORE validation failures
        validation_errors = decision.get("validation_errors", [])
        for error in validation_errors:
            proposals.extend(
                self._propose_validation_fix(error, claim)
            )

        return proposals

    def _propose_missing_attestations(
        self,
        missing_obligations: List[Dict[str, Any]],
        tribunal: Dict[str, Any],
        receipt_gap: int
    ) -> List[ImprovementProposal]:
        """Propose attestations for missing obligations."""
        proposals = []

        for missing in missing_obligations:
            obl_name = missing.get("name")
            severity = missing.get("severity", "HARD")
            expected_attestor = missing.get("expected_attestor", "unknown")
            reason_code = missing.get("reason_code", "MISSING")

            # Calculate mayor score
            if severity == "HARD":
                base_score = self.WEIGHTS["hard_obligation_satisfied"]
            else:
                base_score = self.WEIGHTS["soft_obligation_satisfied"]

            # Adjust score based on receipt gap (distribute 100% across all gaps)
            mayor_score = min(100, int((100 / receipt_gap) if receipt_gap > 0 else 100))

            proposal = ImprovementProposal(
                type="add_attestation",
                target=obl_name,
                description=f"Superteam will provide attestation for '{obl_name}' from {expected_attestor}",
                impact=f"Reduces receipt gap by 1 (from {receipt_gap})",
                mayor_score=mayor_score,
                payload={
                    "obligation_name": obl_name,
                    "attestor": expected_attestor,
                    "attestation_valid": True,
                    "policy_match": 1,
                    "payload_hash": self._generate_attestation_hash(obl_name)
                }
            )

            proposals.append(proposal)

        return proposals

    def _propose_kill_switch_fix(
        self,
        kill_switch: Dict[str, Any],
        claim: Dict[str, Any]
    ) -> List[ImprovementProposal]:
        """Propose fixes for failed kill switches."""
        proposals = []

        ks_name = kill_switch.get("name")

        proposal = ImprovementProposal(
            type="fix_kill_switch",
            target=ks_name,
            description=f"Fix kill switch violation: {ks_name}",
            impact=f"Resolves {ks_name} policy failure",
            mayor_score=self.WEIGHTS["policy_compliance"],
            payload={
                "kill_switch_name": ks_name,
                "proposed_fix": f"Adjust claim to comply with {ks_name} policy"
            }
        )

        proposals.append(proposal)

        return proposals

    def _propose_validation_fix(
        self,
        validation_error: Dict[str, Any],
        claim: Dict[str, Any]
    ) -> List[ImprovementProposal]:
        """Propose fixes for validation errors."""
        proposals = []

        error_type = validation_error.get("type", "unknown")

        proposal = ImprovementProposal(
            type="fix_validation",
            target=error_type,
            description=f"Fix validation error: {validation_error.get('detail', 'unknown')}",
            impact="Resolves validation failure",
            mayor_score=self.WEIGHTS["validation_fix"],
            payload={
                "error_type": error_type,
                "proposed_fix": validation_error.get("suggested_fix", "Manual review required")
            }
        )

        proposals.append(proposal)

        return proposals

    def apply_improvements(
        self,
        attestations: Dict[str, Any],
        proposals: List[ImprovementProposal]
    ) -> Dict[str, Any]:
        """
        Apply improvement proposals to attestation bundle.

        Args:
            attestations: Current attestation bundle
            proposals: List of proposals to apply

        Returns:
            Updated attestation bundle
        """
        # Deep copy to avoid mutation
        updated = {
            "attestations": list(attestations.get("attestations", []))
        }

        for proposal in proposals:
            if proposal.type == "add_attestation":
                # Add new attestation
                updated["attestations"].append(proposal.payload)

            elif proposal.type == "fix_kill_switch":
                # Kill switch fixes would typically require claim modification
                # For now, we just record the proposal
                pass

            elif proposal.type == "fix_validation":
                # Validation fixes would require claim/token tree modification
                # For now, we just record the proposal
                pass

        return updated

    def _generate_attestation_hash(self, obligation_name: str) -> str:
        """Generate a deterministic hash for attestation payload."""
        payload = {
            "obligation": obligation_name,
            "version": self.VERSION,
            "generated": True
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode('utf-8')
        ).hexdigest()

    def format_proposal_summary(
        self,
        proposals: List[ImprovementProposal]
    ) -> str:
        """Format proposals for human-readable display."""
        if not proposals:
            return "No improvements proposed."

        lines = [
            f"Superteam proposed {len(proposals)} improvements:\n"
        ]

        for i, proposal in enumerate(proposals, 1):
            lines.append(f"{i}. {proposal.type}: {proposal.target}")
            lines.append(f"   Description: {proposal.description}")
            lines.append(f"   Impact: {proposal.impact}")
            lines.append(f"   Mayor Score: {proposal.mayor_score}%\n")

        return "\n".join(lines)


def propose_improvements(
    claim: Dict[str, Any],
    tribunal: Dict[str, Any],
    attestations: Dict[str, Any],
    decision: Dict[str, Any]
) -> List[ImprovementProposal]:
    """
    Convenience function: Analyze and propose improvements.

    Args:
        claim: The claim being evaluated
        tribunal: Tribunal bundle
        attestations: Attestation bundle
        decision: Mayor decision (NO_SHIP)

    Returns:
        List of improvement proposals
    """
    improver = SuperteamImprover()
    return improver.analyze_and_propose(claim, tribunal, attestations, decision)


def apply_improvements(
    attestations: Dict[str, Any],
    proposals: List[ImprovementProposal]
) -> Dict[str, Any]:
    """
    Convenience function: Apply improvements to attestations.

    Args:
        attestations: Current attestation bundle
        proposals: Improvement proposals

    Returns:
        Updated attestation bundle
    """
    improver = SuperteamImprover()
    return improver.apply_improvements(attestations, proposals)
