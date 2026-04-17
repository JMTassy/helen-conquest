"""
Creative Town - Layer 2

Exploratory, untrusted proposal generation layer.

CRITICAL BOUNDARIES:
- Creative agents CANNOT emit attestations
- Creative agents CANNOT affect SHIP/NO_SHIP
- Creative agents CANNOT bypass Bridge
- Creative agents CANNOT modify obligations
- Creative agents CANNOT touch kernel

Outputs are PROPOSALS ONLY (non-sovereign, inert, zero authority).
"""
from __future__ import annotations
import hashlib
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class CreativeRole(Enum):
    """Creative agent role types"""
    COUNTEREXAMPLE_HUNTER = "counterexample_hunter"
    PROTOCOL_SIMPLIFIER = "protocol_simplifier"
    ADVERSARIAL_DESIGNER = "adversarial_designer"
    EDGE_CASE_GENERATOR = "edge_case_generator"
    NOVELTY_MAXIMIZER = "novelty_maximizer"
    FAILURE_HUNTER = "failure_hunter"
    REFACTORER = "refactorer"
    ATTACKER = "attacker"


class ProposalType(Enum):
    """Proposal categorization"""
    SOLUTION_VARIANT = "SOLUTION_VARIANT"
    ARCHITECTURE_SUGGESTION = "ARCHITECTURE_SUGGESTION"
    TEST_EXTENSION = "TEST_EXTENSION"
    PARAMETER_MUTATION = "PARAMETER_MUTATION"
    EDGE_CASE_EXPLORATION = "EDGE_CASE_EXPLORATION"
    FAILURE_HYPOTHESIS = "FAILURE_HYPOTHESIS"
    SIMPLIFICATION = "SIMPLIFICATION"
    ATTACK_VECTOR = "ATTACK_VECTOR"


@dataclass
class ProposalEnvelope:
    """
    Creative Town proposal wrapper.

    Properties:
    - Hashable (deterministic ID)
    - Inert (no execution authority)
    - Zero governance power (cannot affect verdicts)
    """
    proposal_id: str
    origin: str  # e.g., "creative_town.team_red"
    proposal_type: ProposalType
    description_hash: str  # SHA-256 of free text
    suggested_changes: Dict[str, Any]
    creativity_metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to schema-compliant dict"""
        return {
            "proposal_id": self.proposal_id,
            "origin": self.origin,
            "proposal_type": self.proposal_type.value,
            "description_hash": self.description_hash,
            "suggested_changes": self.suggested_changes,
            "creativity_metadata": self.creativity_metadata or {}
        }


class CreativeAgent:
    """
    Base class for creative agents.

    Creative agents are:
    - Abundant (hundreds can run in parallel)
    - Cheap (no cost to being wrong)
    - Powerless (proposals only, zero authority)
    - Competitive (different incentives per role)
    """

    def __init__(self, role: CreativeRole, team_id: str):
        self.role = role
        self.team_id = team_id
        self.origin = f"creative_town.{team_id}"

    def _generate_proposal_id(self, description: str) -> str:
        """Generate deterministic proposal ID"""
        hash_input = f"{self.origin}:{description}:{datetime.utcnow().isoformat()}"
        h = hashlib.sha256(hash_input.encode()).hexdigest()[:12].upper()
        return f"P-{h}"

    def _hash_description(self, description: str) -> str:
        """Hash free-text description (not stored in proposal)"""
        return hashlib.sha256(description.encode()).hexdigest()

    def generate_proposal(
        self,
        description: str,
        proposal_type: ProposalType,
        suggested_changes: Dict[str, Any],
        inspiration_sources: List[str] = None,
        estimated_novelty: float = 0.5
    ) -> ProposalEnvelope:
        """
        Generate a proposal envelope.

        Args:
            description: Free-text description (will be hashed)
            proposal_type: Proposal category
            suggested_changes: Structured changes
            inspiration_sources: References to failures/rejections
            estimated_novelty: Self-assessment (non-sovereign)

        Returns:
            ProposalEnvelope (inert, non-executable)
        """
        proposal_id = self._generate_proposal_id(description)
        description_hash = self._hash_description(description)

        metadata = {
            "generation_timestamp": datetime.utcnow().isoformat(),
            "creative_role": self.role.value,
            "inspiration_sources": inspiration_sources or [],
            "estimated_novelty_score": estimated_novelty
        }

        return ProposalEnvelope(
            proposal_id=proposal_id,
            origin=self.origin,
            proposal_type=proposal_type,
            description_hash=description_hash,
            suggested_changes=suggested_changes,
            creativity_metadata=metadata
        )


class CounterexampleHunter(CreativeAgent):
    """
    Creative agent focused on finding edge cases and failure modes.

    Incentives:
    - Proposals that survive translation
    - Proposals that expose unhandled cases
    """

    def __init__(self, team_id: str = "counterexample_team"):
        super().__init__(CreativeRole.COUNTEREXAMPLE_HUNTER, team_id)

    def propose_edge_case(
        self,
        description: str,
        test_extension: str,
        inspiration_from_failure: str = None
    ) -> ProposalEnvelope:
        """
        Propose new edge case test.

        Args:
            description: What edge case to test
            test_extension: Suggested test code/spec
            inspiration_from_failure: Optional failure mode reference

        Returns:
            Proposal for test extension
        """
        suggested_changes = {
            "test_extension": test_extension
        }

        inspiration_sources = []
        if inspiration_from_failure:
            inspiration_sources.append(f"failure_mode:{inspiration_from_failure}")

        return self.generate_proposal(
            description=description,
            proposal_type=ProposalType.EDGE_CASE_EXPLORATION,
            suggested_changes=suggested_changes,
            inspiration_sources=inspiration_sources,
            estimated_novelty=0.8  # Edge cases are high novelty
        )


class ProtocolSimplifier(CreativeAgent):
    """
    Creative agent focused on simplification and refactoring.

    Incentives:
    - Reduced complexity metrics
    - Fewer obligations while maintaining safety
    """

    def __init__(self, team_id: str = "simplifier_team"):
        super().__init__(CreativeRole.PROTOCOL_SIMPLIFIER, team_id)

    def propose_simplification(
        self,
        description: str,
        metric: str,
        parameter_delta: Dict[str, float]
    ) -> ProposalEnvelope:
        """
        Propose simplification.

        Args:
            description: What to simplify
            metric: Target metric (e.g., "obligation_count")
            parameter_delta: Suggested changes

        Returns:
            Proposal for simplification
        """
        suggested_changes = {
            "metric": metric,
            "parameter_delta": parameter_delta
        }

        return self.generate_proposal(
            description=description,
            proposal_type=ProposalType.SIMPLIFICATION,
            suggested_changes=suggested_changes,
            estimated_novelty=0.4  # Simplifications are moderate novelty
        )


class AdversarialDesigner(CreativeAgent):
    """
    Creative agent focused on attack vectors and adversarial scenarios.

    Incentives:
    - Proposals that expose vulnerabilities
    - Attack scenarios that fail safely
    """

    def __init__(self, team_id: str = "adversarial_team"):
        super().__init__(CreativeRole.ADVERSARIAL_DESIGNER, team_id)

    def propose_attack_vector(
        self,
        description: str,
        obligation_addition: List[str],
        inspiration_from_oracle_rejection: str = None
    ) -> ProposalEnvelope:
        """
        Propose attack vector to test.

        Args:
            description: Attack scenario
            obligation_addition: New obligations to defend
            inspiration_from_oracle_rejection: Optional rejection reference

        Returns:
            Proposal for attack vector
        """
        suggested_changes = {
            "obligation_addition": obligation_addition
        }

        inspiration_sources = []
        if inspiration_from_oracle_rejection:
            inspiration_sources.append(f"oracle_rejection:{inspiration_from_oracle_rejection}")

        return self.generate_proposal(
            description=description,
            proposal_type=ProposalType.ATTACK_VECTOR,
            suggested_changes=suggested_changes,
            inspiration_sources=inspiration_sources,
            estimated_novelty=0.9  # Attack vectors are high novelty
        )


class CreativeTown:
    """
    Creative Town orchestrator.

    Manages:
    - Multiple creative teams
    - Proposal markets
    - Translation pipeline (proposals → WUL)
    """

    def __init__(self):
        self.agents: List[CreativeAgent] = []
        self.proposals: List[ProposalEnvelope] = []

    def register_agent(self, agent: CreativeAgent):
        """Register creative agent"""
        self.agents.append(agent)

    def submit_proposal(self, proposal: ProposalEnvelope):
        """
        Submit proposal to market.

        Proposals are:
        - Stored for translation
        - Measured for metrics
        - Competing for slots
        """
        self.proposals.append(proposal)

    def get_proposals_by_type(self, proposal_type: ProposalType) -> List[ProposalEnvelope]:
        """Get all proposals of given type"""
        return [p for p in self.proposals if p.proposal_type == proposal_type]

    def get_proposal_metrics(self) -> Dict[str, int]:
        """
        Compute proposal market metrics.

        Tracks:
        - Total proposals
        - Proposals by type
        - Proposals by role
        """
        metrics = {
            "total_proposals": len(self.proposals),
            "by_type": {},
            "by_role": {}
        }

        for proposal in self.proposals:
            # Count by type
            ptype = proposal.proposal_type.value
            metrics["by_type"][ptype] = metrics["by_type"].get(ptype, 0) + 1

            # Count by role (from metadata)
            if proposal.creativity_metadata:
                role = proposal.creativity_metadata.get("creative_role")
                if role:
                    metrics["by_role"][role] = metrics["by_role"].get(role, 0) + 1

        return metrics
