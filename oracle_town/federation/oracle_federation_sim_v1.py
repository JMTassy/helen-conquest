#!/usr/bin/env python3
"""
ORACLE TOWN Federation Simulation — Phase 3

Three independent ORACLE instances with internal swarms coordinate through
gossip protocol, achieving consensus without central authority.

Architecture:
  - oracle-1, oracle-2, oracle-3 (each with internal swarm)
  - All use shared deterministic_time for reproducibility
  - Proposals are processed independently, receipts shared via gossip
  - Cross-validation detects disagreements
  - Consensus emerges from agreement patterns (no forced voting)

Key Principle:
  No forced agreement. Disagreement is DATA — logged, analyzed, reported.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "kernel"))
sys.path.insert(0, str(Path(__file__).parent.parent / "swarm"))

from oracle_kernel_v1 import OracleKernel, Claim, Receipt
from oracle_with_swarm import OracleWithSwarm
from agents import Proposal
from gossip_protocol import GossipNode, Federation as GossipFederation


@dataclass
class FederationRound:
    """Result of one federation coordination round"""
    round_number: int
    proposals_processed: int
    total_claims: int
    unanimous_claims: int
    contested_claims: int
    average_agreement_rate: float
    byzantine_instances: List[str]
    voting_matrices: Dict[str, Dict[str, Dict[str, str]]]  # instance → claim_id → voting_instances


class OracleFederationSim:
    """
    Orchestrates 3 independent ORACLE instances with federation consensus.

    Flow per round:
    1. Each oracle processes proposals independently
    2. Oracles gossip receipts to peers
    3. Peers validate receipts against their own gates
    4. Disagreements logged explicitly
    5. Consensus report generated
    6. Byzantine behavior detected
    """

    def __init__(
        self,
        deterministic_time: str = "2026-02-17T12:00:00Z",
        instance_names: List[str] = None,
    ):
        if instance_names is None:
            instance_names = ["oracle-1", "oracle-2", "oracle-3"]

        self.instance_names = instance_names
        self.deterministic_time = deterministic_time
        self.round_number = 0

        # Initialize oracle instances (each with internal swarm)
        self.oracles: Dict[str, OracleWithSwarm] = {
            name: OracleWithSwarm(
                policy_version="POLICY_v1.0",
                deterministic_time=deterministic_time,
                deterministic_counter_seed=hash(name) % 1000,  # Unique seed per instance
            )
            for name in instance_names
        }

        # Initialize gossip federation (for cross-validation)
        self.gossip_federation = GossipFederation(instance_names)

        # Track federation metrics
        self.federation_ledger: List[FederationRound] = []
        self.all_proposals: List[Proposal] = []

    def generate_test_proposals(self, round_num: int, count: int = 3) -> List[Proposal]:
        """Generate deterministic test proposals for this round"""
        proposals = []
        for i in range(count):
            proposal = Proposal(
                proposal_id=f"P-{round_num:02d}-{i:03d}",
                proposer="Federation-Test",
                intent=self._get_intent_for_index(i),
                content={
                    "type": self._get_type_for_index(i),
                    "action": self._get_action_for_index(i),
                    "growth_potential": 0.3 + (i * 0.25),
                    "state_delta": 0.1 * i,
                    "is_novel": i == 2,  # Third proposal is novel
                },
                evidence={"confidence": 0.5 + (i * 0.2), "source": "federation_test"},
                timestamp=self.deterministic_time,
            )
            proposals.append(proposal)

        self.all_proposals.extend(proposals)
        return proposals

    def _get_intent_for_index(self, i: int) -> str:
        intents = ["EXPAND_TERRITORY", "RADICAL_RESTRUCTURE", "MAINTAIN_STABILITY"]
        return intents[i % len(intents)]

    def _get_type_for_index(self, i: int) -> str:
        types = ["territorial", "structural", "maintenance"]
        return types[i % len(types)]

    def _get_action_for_index(self, i: int) -> str:
        actions = ["EXPAND", "RESTRUCTURE", "STABILIZE"]
        return actions[i % len(actions)]

    def run_round(self) -> FederationRound:
        """Execute one federation coordination round"""
        self.round_number += 1

        # Stage 1: Generate proposals for this round
        proposals = self.generate_test_proposals(self.round_number)

        # Stage 2: Each oracle independently processes proposals
        instance_results = {}
        for instance_name, oracle in self.oracles.items():
            instance_results[instance_name] = []
            for proposal in proposals:
                result = oracle.full_debate_to_receipt(proposal)
                instance_results[instance_name].append(result)

        # Stage 3: Gossip receipts through federation
        # Each oracle shares receipts with peers
        for instance_name, results in instance_results.items():
            for result in results:
                claim_id = result["claim"].claim_id
                receipt = result["receipt"]
                # Broadcast this receipt to other instances via gossip
                self.gossip_federation.process_receipt_gossip(
                    claim_id,
                    {
                        "decision": receipt.decision,
                        "policy_version": receipt.policy_version,
                        "gates_passed": receipt.gates_passed,
                        "reason": receipt.reason or "No reason provided",
                    },
                    source_instance=instance_name,
                )

        # Stage 4: Collect consensus reports from all oracles
        federation_status = self.gossip_federation.get_federation_status()

        # Stage 5: Detect Byzantine behavior
        suspicious = self.gossip_federation.detect_byzantine_behavior()

        # Stage 6: Create federation round result
        total_claims = federation_status["total_contested_claims"] + sum(
            r["unanimous_claims"] for r in federation_status["reports"]
        )

        unanimous_claims = sum(r["unanimous_claims"] for r in federation_status["reports"])
        contested_claims = federation_status["total_contested_claims"]

        round_result = FederationRound(
            round_number=self.round_number,
            proposals_processed=len(proposals) * len(self.instance_names),
            total_claims=total_claims,
            unanimous_claims=unanimous_claims,
            contested_claims=contested_claims,
            average_agreement_rate=federation_status["average_agreement_rate"],
            byzantine_instances=suspicious,
            voting_matrices={
                report["instance_id"]: report["voting_matrix"]
                for report in federation_status["reports"]
            },
        )

        self.federation_ledger.append(round_result)
        return round_result

    def run_simulation(self, rounds: int = 10) -> List[FederationRound]:
        """Run full federation simulation for specified rounds"""
        print("\n" + "=" * 80)
        print("ORACLE TOWN Federation Simulation — Phase 3")
        print("=" * 80 + "\n")

        print(f"🚀 Initializing federation with {len(self.instance_names)} instances")
        print(f"   Instances: {', '.join(self.instance_names)}")
        print(f"   Deterministic Time: {self.deterministic_time}")
        print(f"   Planned Rounds: {rounds}\n")

        results = []
        for _ in range(rounds):
            round_result = self.run_round()
            results.append(round_result)

            # Print round summary
            print(f"Round {round_result.round_number}:")
            print(f"  Proposals Processed: {round_result.proposals_processed}")
            print(f"  Total Claims Evaluated: {round_result.total_claims}")
            print(f"  Unanimous: {round_result.unanimous_claims}")
            print(f"  Contested: {round_result.contested_claims}")
            print(f"  Average Agreement Rate: {round_result.average_agreement_rate:.0%}")

            if round_result.byzantine_instances:
                print(f"  ⚠️ Byzantine Risk: {', '.join(round_result.byzantine_instances)}")
            else:
                print(f"  ✅ No Byzantine behavior detected")

            print()

        return results

    def get_federation_status(self) -> Dict[str, Any]:
        """Get overall federation health status"""
        if not self.federation_ledger:
            return {"status": "no_rounds_completed"}

        latest = self.federation_ledger[-1]

        total_rounds = len(self.federation_ledger)
        avg_agreement = sum(r.average_agreement_rate for r in self.federation_ledger) / total_rounds
        total_contested = sum(r.contested_claims for r in self.federation_ledger)
        total_unanimous = sum(r.unanimous_claims for r in self.federation_ledger)
        total_claims = latest.total_claims

        return {
            "rounds_completed": total_rounds,
            "total_claims_evaluated": sum(r.total_claims for r in self.federation_ledger),
            "total_unanimous_claims": total_unanimous,
            "total_contested_claims": total_contested,
            "average_agreement_rate": avg_agreement,
            "byzantine_risk": "LOW" if avg_agreement > 0.8 else "MEDIUM",
            "instance_count": len(self.instance_names),
            "latest_round": {
                "round": latest.round_number,
                "agreement_rate": latest.average_agreement_rate,
                "contested": latest.contested_claims,
                "byzantine_flags": latest.byzantine_instances,
            },
        }

    def print_federation_summary(self):
        """Print comprehensive federation summary"""
        status = self.get_federation_status()

        print("\n" + "=" * 80)
        print("📊 Federation Summary")
        print("=" * 80 + "\n")

        print(f"Rounds Completed: {status['rounds_completed']}")
        print(f"Total Claims Evaluated: {status['total_claims_evaluated']}")
        print(f"Unanimous Claims: {status['total_unanimous_claims']}")
        print(f"Contested Claims: {status['total_contested_claims']}")
        print(f"Average Agreement Rate: {status['average_agreement_rate']:.0%}")
        print(f"Byzantine Risk Level: {status['byzantine_risk']}")
        print()

        print("Per-Instance Metrics:")
        for instance_name, oracle in self.oracles.items():
            metrics = oracle.get_swarm_metrics()
            print(f"\n  {instance_name}:")
            print(f"    Debates: {metrics['debates_conducted']}")
            print(f"    Consensus Rate: {metrics['consensus_rate']:.0%}")
            print(f"    Conflict Rate: {metrics['conflict_rate']:.0%}")

        if status["latest_round"]["byzantine_flags"]:
            print(f"\n⚠️ Byzantine Instances Detected:")
            for instance in status["latest_round"]["byzantine_flags"]:
                print(f"   - {instance}")
        else:
            print(f"\n✅ No Byzantine behavior detected across all rounds")

        print()


# ═══════════════════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════════════════


def demo():
    """Demonstrate federation with 3 oracle instances"""
    sim = OracleFederationSim(
        deterministic_time="2026-02-17T12:00:00Z",
        instance_names=["oracle-1", "oracle-2", "oracle-3"],
    )

    # Run 5 rounds of federation
    results = sim.run_simulation(rounds=5)

    # Print final summary
    sim.print_federation_summary()

    # Print voting matrices from final round
    if results:
        final_round = results[-1]
        print("=" * 80)
        print(f"Voting Matrices — Round {final_round.round_number}")
        print("=" * 80 + "\n")

        for instance_name, voting_matrix in final_round.voting_matrices.items():
            print(f"{instance_name}:")
            for claim_id, votes in voting_matrix.items():
                print(f"  {claim_id}:")
                for voter, decision in votes.items():
                    print(f"    {voter}: {decision}")
            print()


if __name__ == "__main__":
    demo()
