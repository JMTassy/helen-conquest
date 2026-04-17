#!/usr/bin/env python3
"""
Internal Swarm Agents

Three competing agents evaluate proposals within a single ORACLE instance.

Each agent:
- Has a unique bias/strategy
- Evaluates proposals deterministically
- Votes ACCEPT/REJECT/MODIFY
- Is logged for audit trail

Agents do NOT mutate state directly.
They only emit verdicts → ledger decides.

Agents:
1. WardenAgent — Risk-averse, rejects high uncertainty
2. StewardAgent — Action-biased, favors growth
3. ArchivistAgent — Consistency-biased, rejects contradictions
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class VoteType(Enum):
    """Agent voting options"""
    ACCEPT = "ACCEPT"           # Approve proposal
    REJECT = "REJECT"           # Reject proposal
    MODIFY = "MODIFY"           # Accept with modification


@dataclass
class Proposal:
    """A proposal for the swarm to evaluate"""
    proposal_id: str
    proposer: str               # Which external agent proposed
    intent: str                 # What is being proposed
    content: Dict[str, Any]     # Proposal payload
    evidence: Dict[str, Any]    # Supporting evidence
    timestamp: str              # ISO 8601


@dataclass
class Vote:
    """Vote by an agent on a proposal"""
    agent_name: str
    agent_type: str             # "Warden" | "Steward" | "Archivist"
    proposal_id: str
    vote: str                   # VoteType enum value
    confidence: float           # 0.0 - 1.0
    reasoning: str              # Justification
    recommendation: Optional[str] = None  # If MODIFY, suggest change


@dataclass
class DebateResult:
    """Result of debate cycle on a proposal"""
    proposal_id: str
    votes: List[Vote]
    final_decision: str         # "ACCEPT" | "REJECT" | "CONTESTED"
    accept_count: int
    reject_count: int
    modify_count: int
    average_confidence: float
    consensus: bool             # True if unanimous


class Agent(ABC):
    """Base class for swarm agents"""

    def __init__(self, name: str, agent_type: str):
        self.name = name
        self.agent_type = agent_type
        self.vote_history: List[Vote] = []

    @abstractmethod
    def evaluate(self, proposal: Proposal, context: Dict[str, Any]) -> Vote:
        """
        Evaluate a proposal and produce a vote.

        Args:
            proposal: Proposal to evaluate
            context: System state context (previous decisions, etc.)

        Returns:
            Vote object with decision and reasoning
        """
        pass

    def vote(self, proposal: Proposal, context: Dict[str, Any]) -> Vote:
        """Generate and log a vote"""
        vote = self.evaluate(proposal, context)
        self.vote_history.append(vote)
        return vote

    def get_vote_history(self) -> List[Vote]:
        """Return voting history (read-only)"""
        return list(self.vote_history)


# ═══════════════════════════════════════════════════════════════════════════
# CONCRETE AGENTS
# ═══════════════════════════════════════════════════════════════════════════

class WardenAgent(Agent):
    """
    Risk-averse agent.

    Rejects proposals with:
    - High uncertainty (low evidence confidence)
    - New patterns not in history
    - Aggressive changes to state

    Strategy: "Fail-closed by default"
    """

    def __init__(self, name: str = "Warden-01"):
        super().__init__(name, "Warden")
        self.uncertainty_threshold = 0.3  # Reject if evidence confidence < 30%
        self.max_state_delta = 0.5         # Reject changes > 50% of current state

    def evaluate(self, proposal: Proposal, context: Dict[str, Any]) -> Vote:
        """
        Risk-averse evaluation.

        Fail-closed: require high confidence before accepting.
        """
        # Extract confidence signal from evidence
        evidence_confidence = proposal.evidence.get("confidence", 0.0)

        if evidence_confidence < self.uncertainty_threshold:
            return Vote(
                agent_name=self.name,
                agent_type=self.agent_type,
                proposal_id=proposal.proposal_id,
                vote=VoteType.REJECT.value,
                confidence=0.9,  # High confidence in rejection
                reasoning=f"Evidence confidence ({evidence_confidence:.1%}) below threshold ({self.uncertainty_threshold:.1%})",
            )

        # Check for extreme state deltas
        proposed_delta = proposal.content.get("state_delta", 0.0)
        if abs(proposed_delta) > self.max_state_delta:
            return Vote(
                agent_name=self.name,
                agent_type=self.agent_type,
                proposal_id=proposal.proposal_id,
                vote=VoteType.REJECT.value,
                confidence=0.8,
                reasoning=f"Proposed change ({abs(proposed_delta):.1%}) exceeds safety limit ({self.max_state_delta:.1%})",
            )

        # Check for novel patterns (not in history)
        is_novel = proposal.content.get("is_novel", False)
        if is_novel:
            return Vote(
                agent_name=self.name,
                agent_type=self.agent_type,
                proposal_id=proposal.proposal_id,
                vote=VoteType.MODIFY.value,
                confidence=0.6,
                reasoning="Novel pattern detected. Recommend gradual implementation with monitoring.",
                recommendation="Reduce scope to 25% pilot before full rollout",
            )

        # Default: cautious accept
        return Vote(
            agent_name=self.name,
            agent_type=self.agent_type,
            proposal_id=proposal.proposal_id,
            vote=VoteType.ACCEPT.value,
            confidence=min(evidence_confidence, 0.75),  # Cap confidence
            reasoning="Proposal meets risk thresholds. Accept with caution.",
        )


class StewardAgent(Agent):
    """
    Action-biased agent.

    Favors proposals that:
    - Increase territory / resources
    - Create growth opportunities
    - Expand capability

    Strategy: "Growth enables resilience"
    """

    def __init__(self, name: str = "Steward-01"):
        super().__init__(name, "Steward")
        self.growth_incentive = 0.7  # Favor proposals with >70% growth potential
        self.max_reject_rate = 0.2   # Resist rejecting >20% of reasonable proposals

    def evaluate(self, proposal: Proposal, context: Dict[str, Any]) -> Vote:
        """
        Action-biased evaluation.

        Favor expansion and growth.
        """
        # Extract growth signal
        growth_potential = proposal.content.get("growth_potential", 0.0)
        evidence_confidence = proposal.evidence.get("confidence", 0.0)

        # Growth proposals strongly favored
        if growth_potential > self.growth_incentive and evidence_confidence > 0.2:
            return Vote(
                agent_name=self.name,
                agent_type=self.agent_type,
                proposal_id=proposal.proposal_id,
                vote=VoteType.ACCEPT.value,
                confidence=0.85,
                reasoning=f"High growth potential ({growth_potential:.1%}). Accept to enable expansion.",
            )

        # Maintenance/defensive proposals: accept if reasonable
        if evidence_confidence > 0.3:
            return Vote(
                agent_name=self.name,
                agent_type=self.agent_type,
                proposal_id=proposal.proposal_id,
                vote=VoteType.ACCEPT.value,
                confidence=min(evidence_confidence, 0.7),
                reasoning="Sufficient evidence. Accept to proceed with action.",
            )

        # Low confidence but not zero: suggest modification
        if evidence_confidence > 0.15:
            return Vote(
                agent_name=self.name,
                agent_type=self.agent_type,
                proposal_id=proposal.proposal_id,
                vote=VoteType.MODIFY.value,
                confidence=0.5,
                reasoning="Low evidence, but actionable. Suggest implementation with learning cycle.",
                recommendation="Proceed with small scale initially, measure results",
            )

        # Only reject if evidence is truly inadequate
        return Vote(
            agent_name=self.name,
            agent_type=self.agent_type,
            proposal_id=proposal.proposal_id,
            vote=VoteType.REJECT.value,
            confidence=0.6,
            reasoning="Evidence too weak to act on. Request additional data.",
        )


class ArchivistAgent(Agent):
    """
    Consistency-biased agent.

    Rejects proposals that:
    - Contradict previous decisions
    - Violate established patterns
    - Break documented rules

    Strategy: "Institutional memory"
    """

    def __init__(self, name: str = "Archivist-01"):
        super().__init__(name, "Archivist")
        self.previous_decisions: Dict[str, str] = {}  # proposal_type -> decision
        self.contradiction_threshold = 0.4  # >40% contradiction = reject

    def evaluate(self, proposal: Proposal, context: Dict[str, Any]) -> Vote:
        """
        Consistency-biased evaluation.

        Check for contradictions with history.
        """
        proposal_type = proposal.content.get("type", "unknown")
        intent = proposal.intent

        # Check if this type has prior decisions
        if proposal_type in self.previous_decisions:
            prior_decision = self.previous_decisions[proposal_type]
            current_intent = proposal.content.get("action")

            # Detect contradiction
            if prior_decision != current_intent:
                contradiction_score = proposal.content.get("contradiction_score", 0.5)

                if contradiction_score > self.contradiction_threshold:
                    return Vote(
                        agent_name=self.name,
                        agent_type=self.agent_type,
                        proposal_id=proposal.proposal_id,
                        vote=VoteType.REJECT.value,
                        confidence=0.9,
                        reasoning=f"Contradicts prior decision on {proposal_type}. Prior: {prior_decision}, Current: {current_intent}",
                    )
                else:
                    return Vote(
                        agent_name=self.name,
                        agent_type=self.agent_type,
                        proposal_id=proposal.proposal_id,
                        vote=VoteType.MODIFY.value,
                        confidence=0.7,
                        reasoning=f"Minor contradiction with prior decision. Recommend reconciliation.",
                        recommendation="Document rationale for policy change if intentional",
                    )

        # Accept if consistent with history or novel (no prior)
        return Vote(
            agent_name=self.name,
            agent_type=self.agent_type,
            proposal_id=proposal.proposal_id,
            vote=VoteType.ACCEPT.value,
            confidence=0.8,
            reasoning="Consistent with institutional history. Accept.",
        )

    def record_decision(self, proposal_type: str, decision: str):
        """Record decision for future consistency checks"""
        self.previous_decisions[proposal_type] = decision


# ═══════════════════════════════════════════════════════════════════════════
# DEBATE COORDINATOR
# ═══════════════════════════════════════════════════════════════════════════

class DebateCoordinator:
    """
    Orchestrates agent debate and produces final decision.

    Flow:
    1. Agents evaluate proposal (all vote in parallel, deterministically)
    2. Tally votes
    3. Deterministic tie-breaker if needed
    4. Record debate to ledger
    """

    def __init__(self, agents: List[Agent], deterministic_governor: Optional[callable] = None):
        self.agents = agents
        self.deterministic_governor = deterministic_governor or self._default_governor
        self.debate_history: List[DebateResult] = []

    def conduct_debate(self, proposal: Proposal, context: Dict[str, Any]) -> DebateResult:
        """
        Run full debate cycle on a proposal.

        Returns:
            DebateResult with all votes and final decision
        """
        votes: List[Vote] = []

        # All agents vote (deterministically)
        for agent in self.agents:
            vote = agent.vote(proposal, context)
            votes.append(vote)

        # Tally votes
        accept_count = sum(1 for v in votes if v.vote == VoteType.ACCEPT.value)
        reject_count = sum(1 for v in votes if v.vote == VoteType.REJECT.value)
        modify_count = sum(1 for v in votes if v.vote == VoteType.MODIFY.value)

        # Compute average confidence
        avg_confidence = sum(v.confidence for v in votes) / len(votes) if votes else 0.0

        # Determine final decision
        final_decision = self._determine_outcome(
            accept_count, reject_count, modify_count, proposal, votes
        )

        # Check for consensus
        consensus = accept_count == len(votes) or reject_count == len(votes)

        result = DebateResult(
            proposal_id=proposal.proposal_id,
            votes=votes,
            final_decision=final_decision,
            accept_count=accept_count,
            reject_count=reject_count,
            modify_count=modify_count,
            average_confidence=avg_confidence,
            consensus=consensus,
        )

        self.debate_history.append(result)
        return result

    def _determine_outcome(
        self,
        accept_count: int,
        reject_count: int,
        modify_count: int,
        proposal: Proposal,
        votes: List[Vote],
    ) -> str:
        """
        Deterministic decision rule.

        Priority:
        1. Unanimous accept → ACCEPT
        2. Any reject → CONTESTED (unless unanimous reject)
        3. Majority accept → ACCEPT
        4. Otherwise → CONTESTED
        """
        total = accept_count + reject_count + modify_count

        # Unanimous
        if accept_count == total:
            return "ACCEPT"
        if reject_count == total:
            return "REJECT"

        # Any reject → contested (prevents false positives)
        if reject_count > 0:
            return "CONTESTED"

        # Majority accept
        if accept_count > total / 2:
            return "ACCEPT"

        # Tie or majority modify
        if modify_count >= accept_count:
            return "CONTESTED"

        return "CONTESTED"

    def _default_governor(self, votes: List[Vote]) -> str:
        """Default tie-breaker (unused if _determine_outcome handles everything)"""
        accept = sum(1 for v in votes if v.vote == VoteType.ACCEPT.value)
        reject = sum(1 for v in votes if v.vote == VoteType.REJECT.value)
        return "ACCEPT" if accept > reject else "REJECT"

    def get_debate_history(self) -> List[DebateResult]:
        """Return debate history (read-only)"""
        return list(self.debate_history)


if __name__ == "__main__":
    # Demo
    print("🤖 Internal Swarm Agents\n")

    agents = [
        WardenAgent(),
        StewardAgent(),
        ArchivistAgent(),
    ]

    coordinator = DebateCoordinator(agents)

    # Test proposal
    proposal = Proposal(
        proposal_id="P-001",
        proposer="External-Agent",
        intent="EXPAND_TERRITORY",
        content={
            "type": "territorial",
            "action": "EXPAND",
            "growth_potential": 0.75,
            "state_delta": 0.3,
            "is_novel": False,
        },
        evidence={
            "confidence": 0.8,
            "source": "observational_data",
        },
        timestamp="2026-02-17T12:00:00Z",
    )

    result = coordinator.conduct_debate(proposal, {})

    print(f"Proposal: {proposal.intent}")
    print(f"Final Decision: {result.final_decision}")
    print(f"Votes: {result.accept_count} accept, {result.reject_count} reject, {result.modify_count} modify")
    print(f"Consensus: {result.consensus}")
    print()
    for vote in result.votes:
        print(f"  {vote.agent_type}: {vote.vote} (confidence: {vote.confidence:.0%})")
        print(f"    Reason: {vote.reasoning}")
