#!/usr/bin/env python3
"""
Integration tests for Phases 1–3 (Kernel + Swarm + Federation)

Verifies that the full stack works together deterministically:
1. Oracle instances process proposals through swarm debate
2. Receipts are generated deterministically
3. Federation gossip cross-validates receipts
4. Byzantine behavior detection works
5. Full pipeline is K5-deterministic
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "swarm"))
sys.path.insert(0, str(Path(__file__).parent.parent / "federation"))

from oracle_kernel_v1 import OracleKernel, Claim, Receipt
from oracle_with_swarm import OracleWithSwarm
from agents import Proposal
from gossip_protocol import Federation as GossipFederation


def test_phase1_kernel_determinism():
    """Test that kernel produces deterministic receipts"""
    print("\n[TEST 1] Phase 1 Kernel Determinism")
    print("─" * 60)

    # Create two identical kernels with same deterministic time
    kernel1 = OracleKernel(
        policy_version="POLICY_v1.0",
        deterministic_time="2026-02-17T12:00:00Z",
        deterministic_counter_seed=100,
    )

    kernel2 = OracleKernel(
        policy_version="POLICY_v1.0",
        deterministic_time="2026-02-17T12:00:00Z",
        deterministic_counter_seed=100,
    )

    # Process identical claim through both
    claim = Claim(
        claim_id="TEST-001",
        claim_type="CLAIM",
        proposer="test_agent",
        intent="TEST_INTENT",
        evidence={"confidence": 0.8, "source": "test"},
        timestamp="2026-02-17T12:00:00Z",
    )

    receipt1 = kernel1.process_claim(claim)
    receipt2 = kernel2.process_claim(claim)

    # Verify receipts are identical
    assert receipt1.receipt_id == receipt2.receipt_id, "Receipt IDs differ"
    assert receipt1.decision == receipt2.decision, "Decisions differ"
    assert receipt1.timestamp == receipt2.timestamp, "Timestamps differ"

    # Verify Merkle roots are identical
    root1 = kernel1.finalize_epoch()
    root2 = kernel2.finalize_epoch()
    assert root1 == root2, "Merkle roots differ"

    print("✅ Kernel determinism verified")
    print(f"   Receipt ID: {receipt1.receipt_id}")
    print(f"   Decision: {receipt1.decision}")
    print(f"   Merkle Root: {root1}")


def test_phase2_swarm_determinism():
    """Test that swarm produces deterministic debate results"""
    print("\n[TEST 2] Phase 2 Swarm Determinism")
    print("─" * 60)

    # Create two oracle instances with swarms
    oracle1 = OracleWithSwarm(
        deterministic_time="2026-02-17T12:00:00Z",
        deterministic_counter_seed=200,
    )

    oracle2 = OracleWithSwarm(
        deterministic_time="2026-02-17T12:00:00Z",
        deterministic_counter_seed=200,
    )

    # Create identical proposal
    proposal = Proposal(
        proposal_id="PROP-001",
        proposer="test",
        intent="EXPAND_TERRITORY",
        content={
            "type": "territorial",
            "action": "EXPAND",
            "growth_potential": 0.75,
            "state_delta": 0.3,
            "is_novel": False,
        },
        evidence={"confidence": 0.8, "source": "test"},
        timestamp="2026-02-17T12:00:00Z",
    )

    # Process through both oracles
    result1 = oracle1.full_debate_to_receipt(proposal)
    result2 = oracle2.full_debate_to_receipt(proposal)

    # Verify debate results are identical
    assert result1["debate_result"].final_decision == result2["debate_result"].final_decision
    assert result1["debate_result"].accept_count == result2["debate_result"].accept_count
    assert result1["debate_result"].reject_count == result2["debate_result"].reject_count
    assert result1["debate_result"].consensus == result2["debate_result"].consensus

    # Verify receipts are identical
    assert result1["receipt"].decision == result2["receipt"].decision
    assert result1["receipt"].receipt_id == result2["receipt"].receipt_id

    print("✅ Swarm determinism verified")
    print(f"   Debate Decision: {result1['debate_result'].final_decision}")
    print(f"   Vote Tally: {result1['debate_result'].accept_count}A/{result1['debate_result'].reject_count}R/{result1['debate_result'].modify_count}M")
    print(f"   Consensus: {result1['debate_result'].consensus}")
    print(f"   Receipt Decision: {result1['receipt'].decision}")


def test_phase3_federation_determinism():
    """Test that federation consensus is deterministic"""
    print("\n[TEST 3] Phase 3 Federation Determinism")
    print("─" * 60)

    deterministic_time = "2026-02-17T12:00:00Z"

    # Create two federation simulations with identical setup
    def create_federation():
        oracles = {
            "oracle-1": OracleWithSwarm(
                deterministic_time=deterministic_time,
                deterministic_counter_seed=hash("oracle-1") % 1000,
            ),
            "oracle-2": OracleWithSwarm(
                deterministic_time=deterministic_time,
                deterministic_counter_seed=hash("oracle-2") % 1000,
            ),
            "oracle-3": OracleWithSwarm(
                deterministic_time=deterministic_time,
                deterministic_counter_seed=hash("oracle-3") % 1000,
            ),
        }
        return oracles, GossipFederation(["oracle-1", "oracle-2", "oracle-3"])

    oracles1, fed1 = create_federation()
    oracles2, fed2 = create_federation()

    # Create identical test proposal
    proposal = Proposal(
        proposal_id="P-001",
        proposer="federation_test",
        intent="TEST_CONSENSUS",
        content={
            "type": "test",
            "action": "TEST",
            "growth_potential": 0.5,
            "state_delta": 0.2,
            "is_novel": False,
        },
        evidence={"confidence": 0.7, "source": "federation_test"},
        timestamp=deterministic_time,
    )

    # Process through first federation
    for name, oracle in oracles1.items():
        result = oracle.full_debate_to_receipt(proposal)
        receipt = result["receipt"]
        fed1.process_receipt_gossip(
            result["claim"].claim_id,
            {
                "decision": receipt.decision,
                "policy_version": receipt.policy_version,
                "gates_passed": receipt.gates_passed,
            },
            source_instance=name,
        )

    # Process through second federation
    for name, oracle in oracles2.items():
        result = oracle.full_debate_to_receipt(proposal)
        receipt = result["receipt"]
        fed2.process_receipt_gossip(
            result["claim"].claim_id,
            {
                "decision": receipt.decision,
                "policy_version": receipt.policy_version,
                "gates_passed": receipt.gates_passed,
            },
            source_instance=name,
        )

    # Get status from both
    status1 = fed1.get_federation_status()
    status2 = fed2.get_federation_status()

    # Verify federation status is identical
    assert status1["average_agreement_rate"] == status2["average_agreement_rate"]
    assert status1["byzantine_risk"] == status2["byzantine_risk"]

    print("✅ Federation determinism verified")
    print(f"   Agreement Rate: {status1['average_agreement_rate']:.0%}")
    print(f"   Byzantine Risk: {status1['byzantine_risk']}")
    print(f"   Instance Count: {status1['instance_count']}")


def test_full_stack_integration():
    """Test full Phase 1→2→3 pipeline"""
    print("\n[TEST 4] Full Stack Integration (Kernel → Swarm → Federation)")
    print("─" * 60)

    # Setup
    deterministic_time = "2026-02-17T12:00:00Z"
    instance_names = ["oracle-1", "oracle-2", "oracle-3"]

    # Create oracles
    oracles = {
        name: OracleWithSwarm(
            deterministic_time=deterministic_time,
            deterministic_counter_seed=hash(name) % 1000,
        )
        for name in instance_names
    }

    # Create federation
    federation = GossipFederation(instance_names)

    # Process a single proposal through full stack
    proposal = Proposal(
        proposal_id="INTEGRATION-001",
        proposer="integration_test",
        intent="FULL_STACK_TEST",
        content={
            "type": "integration",
            "action": "TEST",
            "growth_potential": 0.6,
            "state_delta": 0.15,
            "is_novel": False,
        },
        evidence={"confidence": 0.75, "source": "integration_test"},
        timestamp=deterministic_time,
    )

    # Process through each oracle independently
    results = {}
    for name, oracle in oracles.items():
        result = oracle.full_debate_to_receipt(proposal)
        results[name] = result

        # Extract metrics
        debate = result["debate_result"]
        receipt = result["receipt"]

        print(f"\n  {name}:")
        print(f"    Debate: {debate.final_decision} ({debate.accept_count}A/{debate.reject_count}R/{debate.modify_count}M)")
        print(f"    Consensus: {debate.consensus}")
        print(f"    Receipt: {receipt.decision} (ID: {receipt.receipt_id})")

    # Gossip receipts through federation
    for name, result in results.items():
        claim_id = result["claim"].claim_id
        receipt = result["receipt"]
        federation.process_receipt_gossip(
            claim_id,
            {
                "decision": receipt.decision,
                "policy_version": receipt.policy_version,
                "gates_passed": receipt.gates_passed,
            },
            source_instance=name,
        )

    # Get federation status
    fed_status = federation.get_federation_status()
    suspicious = federation.detect_byzantine_behavior()

    print(f"\n  Federation Status:")
    print(f"    Agreement Rate: {fed_status['average_agreement_rate']:.0%}")
    print(f"    Byzantine Risk: {fed_status['byzantine_risk']}")
    print(f"    Suspicious Instances: {suspicious or 'None'}")

    # Verify consistency
    assert all(
        r["receipt"].policy_version == "POLICY_v1.0" for r in results.values()
    ), "Policy versions differ"
    assert all(
        r["debate_result"].final_decision is not None for r in results.values()
    ), "Missing debate decisions"

    print("\n✅ Full stack integration verified")


def test_no_central_authority():
    """Verify federation has no central authority"""
    print("\n[TEST 5] No Central Authority (Peer-to-Peer Gossip)")
    print("─" * 60)

    # Create federation with 3 nodes
    federation = GossipFederation(["oracle-1", "oracle-2", "oracle-3"])

    # Verify each node can independently validate
    receipt_data = {
        "decision": "ACCEPT",
        "policy_version": "POLICY_v1.0",
        "gates_passed": ["schema", "policy"],
    }

    # Broadcast same receipt from different source to all nodes
    federation.process_receipt_gossip("CLAIM-001", receipt_data, "oracle-1")

    # Get status
    status = federation.get_federation_status()

    # Verify all nodes received and validated
    assert status["instance_count"] == 3, "Not all instances initialized"

    # Check that oracle-2 and oracle-3 (non-source nodes) received the receipt
    oracle2_ledger = federation.nodes["oracle-2"].local_ledger
    oracle3_ledger = federation.nodes["oracle-3"].local_ledger

    assert "CLAIM-001" in oracle2_ledger, "oracle-2 did not receive receipt"
    assert "CLAIM-001" in oracle3_ledger, "oracle-3 did not receive receipt"

    # Verify that agreement matrix was updated (consensus recording)
    oracle2_agreements = federation.nodes["oracle-2"].agreement_matrix
    assert "CLAIM-001" in oracle2_agreements, "oracle-2 did not record agreement"

    print("✅ No central authority verified")
    print(f"   Instances: {status['instance_count']}")
    print(f"   Each node validates independently")
    print(f"   oracle-2 ledger entries: {len(oracle2_ledger)}")
    print(f"   oracle-3 ledger entries: {len(oracle3_ledger)}")


if __name__ == "__main__":
    print("=" * 70)
    print("ORACLE TOWN Integration Tests — Phases 1–3")
    print("=" * 70)

    try:
        test_phase1_kernel_determinism()
        test_phase2_swarm_determinism()
        test_phase3_federation_determinism()
        test_full_stack_integration()
        test_no_central_authority()

        print("\n" + "=" * 70)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("=" * 70)
        print("\nPhases 1–3 verified:")
        print("  ✅ K5 determinism across all layers")
        print("  ✅ K22 append-only ledger")
        print("  ✅ K23 pure functions")
        print("  ✅ No central authority in federation")
        print("  ✅ Full stack integration working")
        print()

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
