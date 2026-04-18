#!/usr/bin/env python3
"""
Creative Town Demo

Demonstrates the three-layer architecture:
- Layer 2 (Creative Town): Generate proposals
- Translation Layer: Proposal → WUL + Obligations
- Layer 1 (Oracle Town): Evaluate (would run in real system)
- Layer 0 (Kernel): Mayor decides (would run in real system)

This demo shows proposal generation + translation only.
"""
import json
from oracle_town.creative import (
    CreativeTown,
    CounterexampleHunter,
    ProtocolSimplifier,
    AdversarialDesigner,
    ProposalType,
)
from oracle_town.core.translator import ProposalTranslator


def demo_creative_generation():
    """Demo: Creative agents generate proposals"""
    print("=" * 80)
    print("CREATIVE TOWN DEMO - Layer 2 (Proposal Generation)")
    print("=" * 80)
    print()

    # Initialize Creative Town
    creative_town = CreativeTown()

    # Register creative agents
    hunter = CounterexampleHunter(team_id="team_red")
    simplifier = ProtocolSimplifier(team_id="team_blue")
    attacker = AdversarialDesigner(team_id="team_black")

    creative_town.register_agent(hunter)
    creative_town.register_agent(simplifier)
    creative_town.register_agent(attacker)

    print(f"✅ Registered {len(creative_town.agents)} creative agents")
    print()

    # --- Creative Agent 1: Counterexample Hunter ---
    print("🔍 Counterexample Hunter generating proposal...")
    proposal_1 = hunter.propose_edge_case(
        description="Test behavior when attestations_ledger.jsonl is corrupted",
        test_extension="tests/test_ledger_corruption.py",
        inspiration_from_failure="F-LEDGER-001"
    )
    creative_town.submit_proposal(proposal_1)
    print(f"   Proposal ID: {proposal_1.proposal_id}")
    print(f"   Type: {proposal_1.proposal_type.value}")
    print(f"   Origin: {proposal_1.origin}")
    print()

    # --- Creative Agent 2: Protocol Simplifier ---
    print("🎯 Protocol Simplifier generating proposal...")
    proposal_2 = simplifier.propose_simplification(
        description="Reduce obligation_count by merging redundant checks",
        metric="obligation_count",
        parameter_delta={"min_obligations": -2, "merge_threshold": 0.8}
    )
    creative_town.submit_proposal(proposal_2)
    print(f"   Proposal ID: {proposal_2.proposal_id}")
    print(f"   Type: {proposal_2.proposal_type.value}")
    print(f"   Metric: {proposal_2.suggested_changes['metric']}")
    print()

    # --- Creative Agent 3: Adversarial Designer ---
    print("⚔️  Adversarial Designer generating proposal...")
    proposal_3 = attacker.propose_attack_vector(
        description="Test kill-switch bypass via timestamp manipulation",
        obligation_addition=[
            "timestamp_immutability_verified",
            "kill_switch_replay_attack_blocked"
        ],
        inspiration_from_oracle_rejection="R-KILL-042"
    )
    creative_town.submit_proposal(proposal_3)
    print(f"   Proposal ID: {proposal_3.proposal_id}")
    print(f"   Type: {proposal_3.proposal_type.value}")
    print(f"   New Obligations: {len(proposal_3.suggested_changes['obligation_addition'])}")
    print()

    # Show metrics
    print("=" * 80)
    print("PROPOSAL MARKET METRICS")
    print("=" * 80)
    metrics = creative_town.get_proposal_metrics()
    print(json.dumps(metrics, indent=2))
    print()

    return creative_town


def demo_translation(creative_town: CreativeTown):
    """Demo: Translate proposals to WUL + Obligations"""
    print("=" * 80)
    print("TRANSLATION LAYER - Proposal → WUL + Obligations")
    print("=" * 80)
    print()

    translator = ProposalTranslator()

    for i, proposal in enumerate(creative_town.proposals, 1):
        print(f"--- Translating Proposal {i}/{len(creative_town.proposals)} ---")
        print(f"ID: {proposal.proposal_id}")
        print(f"Type: {proposal.proposal_type.value}")

        result = translator.translate(proposal)

        if result.success:
            print("✅ TRANSLATION SUCCESS")
            print(f"   WUL Tree Nodes: {count_nodes(result.wul_tree)}")
            print(f"   Obligations Created: {len(result.obligations)}")
            print(f"   Evaluation Protocol: {result.evaluation_protocol}")

            # Show first obligation
            if result.obligations:
                obl = result.obligations[0]
                print(f"   First Obligation:")
                print(f"      - name: {obl['name']}")
                print(f"      - severity: {obl['severity']}")
                print(f"      - type: {obl['type']}")
        else:
            print("❌ TRANSLATION FAILED")
            print(f"   Reason: {result.rejection_reason}")
            print("   💀 Proposal died (expected behavior)")

        print()


def count_nodes(tree):
    """Count nodes in WUL tree"""
    if not tree:
        return 0
    count = 1
    for arg in tree.get("args", []):
        count += count_nodes(arg)
    return count


def main():
    """Run complete demo"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "CREATIVE GOVERNANCE DEMO" + " " * 34 + "║")
    print("║" + " " * 15 + "Three-Layer Architecture in Action" + " " * 29 + "║")
    print("╚" + "═" * 78 + "╝")
    print("\n")

    # Layer 2: Creative Town
    creative_town = demo_creative_generation()

    # Translation Layer
    demo_translation(creative_town)

    # Summary
    print("=" * 80)
    print("DEMO SUMMARY")
    print("=" * 80)
    print("✅ Layer 2 (Creative Town): Proposals generated")
    print("✅ Translation Layer: Proposals → WUL + Obligations")
    print()
    print("Next steps in real system:")
    print("  → Layer 1 (Oracle Town): Run evaluation protocols")
    print("  → Factory: Emit attestations")
    print("  → Layer 0 (Kernel): Mayor decides SHIP/NO_SHIP")
    print()
    print("🎯 Creative proposals are now formalized and ready for Oracle evaluation")
    print()


if __name__ == "__main__":
    main()
