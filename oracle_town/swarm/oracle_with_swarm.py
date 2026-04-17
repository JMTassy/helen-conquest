#!/usr/bin/env python3
"""
ORACLE TOWN with Internal Swarm

Extends oracle_kernel_v1 by adding internal debate cycle.

Flow:
1. External proposal arrives
2. Debate coordinator routes to swarm
3. Agents evaluate in parallel (deterministically)
4. Final decision made
5. If ACCEPT, route to Mayor for receipt
6. Log all debate to ledger

This transforms ORACLE from single-decision-maker to micro-polity.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import kernel
sys.path.insert(0, str(Path(__file__).parent.parent / "kernel"))
from oracle_kernel_v1 import OracleKernel, Claim, Receipt

# Import swarm agents
from agents import (
    Proposal, Vote, DebateResult, DebateCoordinator,
    WardenAgent, StewardAgent, ArchivistAgent, VoteType
)


class OracleWithSwarm(OracleKernel):
    """
    ORACLE kernel augmented with internal swarm debate.

    Inherits:
    - Deterministic state machine
    - Append-only ledger
    - Receipt generation

    Adds:
    - Internal agent swarm
    - Debate cycle
    - Conflict measurement
    """

    def __init__(
        self,
        policy_version: str = "POLICY_v1.0",
        deterministic_time: Optional[str] = None,
        deterministic_counter_seed: int = 0,
    ):
        super().__init__(
            policy_version=policy_version,
            deterministic_time=deterministic_time,
            deterministic_counter_seed=deterministic_counter_seed,
        )

        # Initialize swarm
        self.agents = [
            WardenAgent(name="Warden-Alpha"),
            StewardAgent(name="Steward-Alpha"),
            ArchivistAgent(name="Archivist-Alpha"),
        ]
        self.debate_coordinator = DebateCoordinator(self.agents)

        # Metrics
        self.debate_count = 0
        self.consensus_count = 0
        self.contested_count = 0
        self.debate_logs: List[Dict[str, Any]] = []

    def process_proposal_with_debate(self, proposal: Proposal) -> DebateResult:
        """
        Process external proposal through internal swarm debate.

        Flow:
        1. Conduct debate
        2. Log to ledger
        3. Record metrics

        Returns:
            DebateResult with votes and final decision
        """
        # Conduct debate (deterministic)
        result = self.debate_coordinator.conduct_debate(
            proposal, {"proposal_count": self.debate_count}
        )

        self.debate_count += 1

        # Update metrics
        if result.consensus:
            self.consensus_count += 1
        elif result.final_decision == "CONTESTED":
            self.contested_count += 1

        # Log to ledger
        self.ledger.record("DEBATE", {
            "debate_id": f"D-{self.debate_count:06d}",
            "proposal_id": proposal.proposal_id,
            "final_decision": result.final_decision,
            "accept_count": result.accept_count,
            "reject_count": result.reject_count,
            "modify_count": result.modify_count,
            "consensus": result.consensus,
            "average_confidence": result.average_confidence,
        })

        # Log individual votes
        for vote in result.votes:
            self.ledger.record("AGENT_VOTE", {
                "debate_id": f"D-{self.debate_count:06d}",
                "agent_name": vote.agent_name,
                "agent_type": vote.agent_type,
                "vote": vote.vote,
                "confidence": vote.confidence,
                "reasoning": vote.reasoning,
            })

        # Store debate log
        self.debate_logs.append({
            "debate_count": self.debate_count,
            "proposal_id": proposal.proposal_id,
            "final_decision": result.final_decision,
            "votes": [
                {
                    "agent": v.agent_name,
                    "vote": v.vote,
                    "confidence": v.confidence,
                }
                for v in result.votes
            ],
        })

        return result

    def convert_proposal_to_claim(self, proposal: Proposal, debate_result: DebateResult) -> Claim:
        """
        Convert debate result into kernel claim for receipt generation.

        Only creates claim if debate result is ACCEPT or CONTESTED (for logging).
        """
        claim = Claim(
            claim_id=f"CLAIM-{proposal.proposal_id}",
            claim_type="DEBATE_RESULT",
            proposer=f"DEBATE_COORDINATOR",
            intent=debate_result.final_decision,
            evidence={
                "content_hash": "debate_encoded",
                "debate_decision": debate_result.final_decision,
                "consensus": debate_result.consensus,
                "average_confidence": debate_result.average_confidence,
                "accept_count": debate_result.accept_count,
                "reject_count": debate_result.reject_count,
            },
            timestamp=proposal.timestamp,
        )
        return claim

    def full_debate_to_receipt(self, proposal: Proposal) -> Dict[str, Any]:
        """
        Full pipeline: Proposal → Debate → Claim → Receipt

        Returns:
            {
                "proposal_id": str,
                "debate_result": DebateResult,
                "claim": Claim,
                "receipt": Receipt,
                "pipeline_status": "SUCCESS" | "REJECTED",
            }
        """
        # Stage 1: Debate
        debate_result = self.process_proposal_with_debate(proposal)

        # Stage 2: Convert to claim
        claim = self.convert_proposal_to_claim(proposal, debate_result)

        # Stage 3: Process through kernel
        receipt = self.process_claim(claim)

        return {
            "proposal_id": proposal.proposal_id,
            "debate_result": debate_result,
            "claim": claim,
            "receipt": receipt,
            "pipeline_status": "SUCCESS" if receipt.decision == "ACCEPT" else "CONTESTED",
        }

    def get_swarm_metrics(self) -> Dict[str, Any]:
        """Return swarm performance metrics"""
        return {
            "debates_conducted": self.debate_count,
            "consensus_count": self.consensus_count,
            "consensus_rate": self.consensus_count / max(self.debate_count, 1),
            "contested_count": self.contested_count,
            "conflict_rate": self.contested_count / max(self.debate_count, 1),
            "debate_logs": self.debate_logs,
        }

    def get_agent_vote_history(self, agent_type: Optional[str] = None) -> List[Vote]:
        """
        Get vote history for all agents or specific type.

        Args:
            agent_type: "Warden" | "Steward" | "Archivist" | None (all)
        """
        all_votes = []
        for agent in self.agents:
            all_votes.extend(agent.get_vote_history())

        if agent_type:
            return [v for v in all_votes if v.agent_type == agent_type]
        return all_votes


# ═══════════════════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════════════════

def demo():
    """Demonstrate ORACLE with internal swarm"""
    print("\n" + "=" * 70)
    print("ORACLE TOWN with Internal Swarm")
    print("=" * 70 + "\n")

    oracle = OracleWithSwarm(
        deterministic_time="2026-02-17T12:00:00Z",
        deterministic_counter_seed=100,
    )

    # Test proposals
    test_proposals = [
        Proposal(
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
            evidence={"confidence": 0.8, "source": "observational_data"},
            timestamp="2026-02-17T12:00:00Z",
        ),
        Proposal(
            proposal_id="P-002",
            proposer="External-Agent",
            intent="RADICAL_RESTRUCTURE",
            content={
                "type": "structural",
                "action": "RESTRUCTURE",
                "growth_potential": 0.2,
                "state_delta": 0.9,  # Extreme change
                "is_novel": True,
            },
            evidence={"confidence": 0.3, "source": "speculative"},
            timestamp="2026-02-17T12:00:00Z",
        ),
        Proposal(
            proposal_id="P-003",
            proposer="External-Agent",
            intent="MAINTAIN_STABILITY",
            content={
                "type": "maintenance",
                "action": "STABILIZE",
                "growth_potential": 0.1,
                "state_delta": 0.0,
                "is_novel": False,
            },
            evidence={"confidence": 0.95, "source": "historical_data"},
            timestamp="2026-02-17T12:00:00Z",
        ),
    ]

    print("Processing proposals through debate cycle...\n")
    for proposal in test_proposals:
        result = oracle.full_debate_to_receipt(proposal)

        print(f"Proposal: {result['proposal_id']} ({proposal.intent})")
        print(f"  Debate Result: {result['debate_result'].final_decision}")
        print(f"  Votes: {result['debate_result'].accept_count}A / {result['debate_result'].reject_count}R / {result['debate_result'].modify_count}M")
        print(f"  Consensus: {result['debate_result'].consensus}")
        print(f"  Receipt Decision: {result['receipt'].decision}")
        print()

    # Finalize epoch
    epoch_root = oracle.finalize_epoch()
    print(f"Epoch finalized: {epoch_root}\n")

    # Metrics
    metrics = oracle.get_swarm_metrics()
    print("📊 Swarm Metrics:")
    print(f"  Debates: {metrics['debates_conducted']}")
    print(f"  Consensus Rate: {metrics['consensus_rate']:.0%}")
    print(f"  Conflict Rate: {metrics['conflict_rate']:.0%}")
    print()

    # Ledger
    ledger_state = oracle.get_ledger_state()
    print(f"📜 Ledger:")
    print(f"  Total Entries: {ledger_state['entry_count']}")
    print()


if __name__ == "__main__":
    demo()
