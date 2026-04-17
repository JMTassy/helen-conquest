#!/usr/bin/env python3
"""
ORACLE TOWN Federation — Gossip Protocol

Three independent ORACLE instances coordinate without central authority.

Protocol:
- Each ORACLE maintains local ledger
- Periodically gossips receipts to peers
- Peers validate receipts against their gates
- Disagreements logged explicitly (contested claims)
- Consensus emerges from agreement patterns

Key Principle:
No forced agreement. Disagreement is data.
"""

import hashlib
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


class GossipMessageType(Enum):
    """Types of gossip messages"""
    RECEIPT_SHARE = "RECEIPT_SHARE"       # "Here's a receipt I processed"
    VALIDATION_QUERY = "VALIDATION_QUERY" # "Do you agree with this?"
    VALIDATION_RESPONSE = "VALIDATION_RESPONSE"  # "Yes/No I agree"
    CONSENSUS_REPORT = "CONSENSUS_REPORT" # "Here's the voting matrix"


@dataclass
class GossipMessage:
    """Message in gossip protocol"""
    message_id: str
    message_type: str              # GossipMessageType enum value
    sender_instance: str           # "oracle-1", "oracle-2", "oracle-3"
    timestamp: str
    content: Dict[str, Any]
    signature: Optional[str] = None  # Hash-based signature


@dataclass
class ValidationAgreement:
    """Record of whether peers agree on a claim"""
    claim_id: str
    voting_instances: Dict[str, str]  # {"oracle-1": "ACCEPT", "oracle-2": "REJECT", ...}
    agreement_count: int
    disagreement_count: int
    consensus: bool                    # True if unanimous
    contested: bool                    # True if any disagreement


class GossipNode:
    """
    Single node in federation.

    Maintains:
    - Local ledger
    - Peer list
    - Validation agreement matrix
    - Consensus reports
    """

    def __init__(self, instance_id: str, peers: List[str]):
        self.instance_id = instance_id
        self.peers = peers  # Other oracle instances
        self.local_ledger: Dict[str, Any] = {}  # claim_id → receipt
        self.inbox: List[GossipMessage] = []
        self.outbox: List[GossipMessage] = []
        self.agreement_matrix: Dict[str, ValidationAgreement] = {}
        self.message_counter = 0

    def receive_receipt(self, claim_id: str, receipt: Dict[str, Any], source_instance: str):
        """
        Receive receipt from peer via gossip.

        Flow:
        1. Log the receipt
        2. Validate against local gates (deterministic)
        3. Record agreement/disagreement
        4. Prepare response
        """
        # Store in local ledger
        self.local_ledger[claim_id] = {
            "receipt": receipt,
            "source_instance": source_instance,
            "received_at": "2026-02-17T12:00:00Z",  # In real system, actual time
        }

        # Validate locally (deterministic gate check)
        local_decision = self._validate_receipt_locally(claim_id, receipt)

        # Record agreement
        if claim_id not in self.agreement_matrix:
            self.agreement_matrix[claim_id] = ValidationAgreement(
                claim_id=claim_id,
                voting_instances={self.instance_id: local_decision},
                agreement_count=1,
                disagreement_count=0,
                consensus=False,
                contested=False,
            )
        else:
            # Update existing agreement record
            agg = self.agreement_matrix[claim_id]
            agg.voting_instances[source_instance] = receipt.get("decision", "UNKNOWN")

        # Prepare validation response
        response_msg = self._create_validation_response(
            claim_id, receipt, local_decision, source_instance
        )
        self.outbox.append(response_msg)

    def _validate_receipt_locally(self, claim_id: str, receipt: Dict[str, Any]) -> str:
        """
        Deterministic local validation of receipt.

        In a real system, this would re-run gates.
        For federation test, we simulate:
        - High confidence receipts → usually ACCEPT
        - Low confidence receipts → might disagree
        - Policy version mismatch → REJECT
        """
        policy_version = receipt.get("policy_version", "UNKNOWN")
        decision = receipt.get("decision", "UNKNOWN")

        # Simulate local gate check
        if policy_version != "POLICY_v1.0":
            return "REJECT"  # Policy mismatch

        # Deterministic disagreement based on hash
        claim_hash = hashlib.sha256(claim_id.encode()).hexdigest()
        hash_value = int(claim_hash, 16) % 100

        # 20% of receipts will be contested (deterministic)
        if hash_value < 20:
            return "REJECT" if decision == "ACCEPT" else "ACCEPT"

        return decision

    def _create_validation_response(
        self, claim_id: str, receipt: Dict[str, Any], local_decision: str, peer_instance: str
    ) -> GossipMessage:
        """Create response message"""
        self.message_counter += 1
        return GossipMessage(
            message_id=f"MSG-{self.instance_id}-{self.message_counter:04d}",
            message_type=GossipMessageType.VALIDATION_RESPONSE.value,
            sender_instance=self.instance_id,
            timestamp="2026-02-17T12:00:00Z",
            content={
                "claim_id": claim_id,
                "peer_instance": peer_instance,
                "our_decision": local_decision,
                "their_decision": receipt.get("decision"),
                "agreement": local_decision == receipt.get("decision"),
            },
        )

    def gossip_to_peers(self) -> List[GossipMessage]:
        """
        Send all pending messages to peers.

        In real system: network round-trip
        For test: returns messages that other nodes receive
        """
        messages_to_send = list(self.outbox)
        self.outbox.clear()
        return messages_to_send

    def generate_consensus_report(self) -> Dict[str, Any]:
        """
        Generate consensus report for this epoch.

        Shows:
        - Claims processed
        - Agreement rate
        - Contested claims
        - Instance voting patterns
        """
        total_claims = len(self.agreement_matrix)
        unanimous_claims = sum(
            1 for agg in self.agreement_matrix.values() if agg.consensus
        )
        contested_claims = sum(
            1 for agg in self.agreement_matrix.values() if agg.contested
        )

        agreement_rate = unanimous_claims / max(total_claims, 1)
        contested_rate = contested_claims / max(total_claims, 1)

        return {
            "instance_id": self.instance_id,
            "total_claims": total_claims,
            "unanimous_claims": unanimous_claims,
            "contested_claims": contested_claims,
            "agreement_rate": agreement_rate,
            "contested_rate": contested_rate,
            "voting_matrix": {
                claim_id: agg.voting_instances
                for claim_id, agg in self.agreement_matrix.items()
            },
        }

    def get_agreement_stats(self) -> Tuple[int, int, int]:
        """Return (total, unanimous, contested) counts"""
        total = len(self.agreement_matrix)
        unanimous = sum(1 for agg in self.agreement_matrix.values() if agg.consensus)
        contested = sum(1 for agg in self.agreement_matrix.values() if agg.contested)
        return total, unanimous, contested


class Federation:
    """
    Manages 3 ORACLE nodes and orchestrates gossip rounds.

    Responsibilities:
    - Initialize nodes
    - Simulate network rounds
    - Collect consensus reports
    - Detect Byzantine behavior
    """

    def __init__(self, instance_names: List[str]):
        self.instance_names = instance_names
        self.nodes = {
            name: GossipNode(name, [n for n in instance_names if n != name])
            for name in instance_names
        }
        self.round_number = 0
        self.federation_ledger: List[Dict[str, Any]] = []

    def process_receipt_gossip(self, claim_id: str, receipt: Dict[str, Any], source_instance: str):
        """
        Simulate receipt propagation through federation.

        All nodes receive and validate the receipt.
        """
        for instance_name, node in self.nodes.items():
            if instance_name != source_instance:
                node.receive_receipt(claim_id, receipt, source_instance)

    def run_gossip_round(self) -> List[Dict[str, Any]]:
        """
        Simulate one round of gossip.

        Returns:
            Consensus reports from all nodes
        """
        self.round_number += 1

        # Collect consensus reports before round
        pre_reports = {
            name: node.generate_consensus_report() for name, node in self.nodes.items()
        }

        # (In real system: nodes would send messages now)
        # (Messages would be delivered and processed)

        # Collect consensus reports after round
        post_reports = {
            name: node.generate_consensus_report() for name, node in self.nodes.items()
        }

        # Log to federation ledger
        self.federation_ledger.append({
            "round": self.round_number,
            "pre_reports": pre_reports,
            "post_reports": post_reports,
        })

        return list(post_reports.values())

    def get_federation_status(self) -> Dict[str, Any]:
        """
        Get overall federation health.

        Shows:
        - Agreement rates across instances
        - Contested claims
        - Byzantine suspicion level
        """
        all_reports = [node.generate_consensus_report() for node in self.nodes.values()]

        avg_agreement_rate = (
            sum(r["agreement_rate"] for r in all_reports) / len(all_reports)
            if all_reports
            else 0
        )

        total_contested = sum(r["contested_claims"] for r in all_reports)

        return {
            "round": self.round_number,
            "instance_count": len(self.nodes),
            "average_agreement_rate": avg_agreement_rate,
            "total_contested_claims": total_contested,
            "byzantine_risk": "LOW" if avg_agreement_rate > 0.8 else "MEDIUM",
            "reports": all_reports,
        }

    def detect_byzantine_behavior(self) -> List[str]:
        """
        Detect if any instance is behaving suspiciously.

        Heuristics:
        - Disagrees with others >30% of the time
        - Systematic pattern (not random)
        """
        suspicious_instances = []

        for instance_name, node in self.nodes.items():
            total, unanimous, contested = node.get_agreement_stats()

            if total > 0:
                disagreement_rate = contested / total

                if disagreement_rate > 0.3:
                    suspicious_instances.append(
                        f"{instance_name} (disagreement_rate={disagreement_rate:.0%})"
                    )

        return suspicious_instances


# ═══════════════════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════════════════

def demo():
    """Demonstrate federation gossip protocol"""
    print("\n" + "=" * 70)
    print("ORACLE TOWN Federation — Gossip Protocol Demo")
    print("=" * 70 + "\n")

    # Initialize federation
    federation = Federation(["oracle-1", "oracle-2", "oracle-3"])

    print("🤝 Simulating federation gossip rounds...\n")

    # Simulate 5 rounds of gossip
    for round_num in range(1, 6):
        print(f"Round {round_num}:")

        # Generate test receipts (deterministically)
        for i in range(3):
            receipt = {
                "claim_id": f"C-{round_num:02d}-{i:03d}",
                "decision": "ACCEPT" if i % 2 == 0 else "REJECT",
                "policy_version": "POLICY_v1.0",
                "confidence": 0.8 + (i * 0.05),
            }

            # Broadcast receipt through federation
            federation.process_receipt_gossip(
                receipt["claim_id"],
                receipt,
                f"oracle-{(i % 3) + 1}",
            )

        # Run gossip round
        reports = federation.run_gossip_round()

        # Print federation status
        status = federation.get_federation_status()
        print(f"  Average agreement rate: {status['average_agreement_rate']:.0%}")
        print(f"  Contested claims: {status['total_contested_claims']}")
        print(f"  Byzantine risk: {status['byzantine_risk']}")
        print()

    # Final analysis
    print("\n📊 Final Federation Status:")
    status = federation.get_federation_status()

    for report in status["reports"]:
        print(f"\n  {report['instance_id']}:")
        print(f"    Total claims: {report['total_claims']}")
        print(f"    Agreement rate: {report['agreement_rate']:.0%}")
        print(f"    Contested: {report['contested_claims']}")

    # Check for Byzantine behavior
    suspicious = federation.detect_byzantine_behavior()
    if suspicious:
        print(f"\n⚠️ Suspicious instances detected:")
        for instance in suspicious:
            print(f"  {instance}")
    else:
        print(f"\n✅ No Byzantine behavior detected")

    print()


if __name__ == "__main__":
    demo()
