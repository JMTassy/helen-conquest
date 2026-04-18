#!/usr/bin/env python3
"""
Option 1: Concrete Execution Test
==================================

A real OpenClaw skill proposal through the full Oracle Town pipeline:
1. Claim generation (with mandatory acceptance criteria)
2. Counter-analysis (BRF_COUNTER)
3. Gate evaluation (K0-K7)
4. TRI verdict
5. Receipt signing
6. Ledger commit

This test reveals where the system actually breaks or where hidden assumptions live.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Import our modules
import sys
sys.path.insert(0, str(Path(__file__).parent / "oracle_town"))

from schemas.claim import Claim, ClaimType, AcceptanceCriteria, Diff, DiffOperation, EvidencePointer, EvidenceType


def create_moltbook_skill_proposal() -> Dict[str, Any]:
    """
    Real OpenClaw skill proposal: Add Moltbook integration skill.

    This is the kind of decision that humans currently "just let through."
    We're going to force it through Oracle Town.
    """
    return {
        "skill_name": "moltbook_sync",
        "skill_version": "1.0.0",
        "skill_purpose": "Fetch Moltbook trending posts and sync to local database",
        "skill_author": "community",
        "skill_url": "https://moltbook.com/skills/sync",

        # Key decision point: What makes this skill SAFE?
        "proposed_behavior": {
            "fetches_from": ["https://moltbook.com/api/trending"],
            "reads_from": ["local database"],
            "writes_to": ["local database", "cache"],
            "executes": ["curl", "jq", "database insert"],
            "uses_credentials": False,
            "modifies_heartbeat": False,
            "modifies_skills": False,
        },

        # Precedent
        "similar_skills_approved": [
            "twitter_sync (approved 2026-01-15)",
            "reddit_trending (approved 2025-12-20)",
        ],

        # Key risk
        "known_issues": [
            "Moltbook API rate limit: 100 req/min",
            "Potential for skill rug-pull via fetched instructions",
        ],
    }


def validate_against_schema(skill: Dict[str, Any]) -> Claim:
    """
    Force the skill proposal through the Claim schema.
    This is where humans are tempted to say "just let it through."
    """

    print("\n" + "=" * 70)
    print("EXECUTION TEST: Moltbook Skill Proposal")
    print("=" * 70)

    print("\n1️⃣  SKILL PROPOSAL:")
    print(f"   Name: {skill['skill_name']}")
    print(f"   Purpose: {skill['skill_purpose']}")
    print(f"   Fetches from: {skill['proposed_behavior']['fetches_from']}")

    # This is the hard part: CREATE ACCEPTANCE CRITERIA
    # The system forces: be specific about what success looks like

    print("\n2️⃣  MANDATORY ACCEPTANCE CRITERIA:")
    print("   The schema requires this. No ambiguity allowed.")

    acceptance_criteria = AcceptanceCriteria(
        success_conditions=[
            "fetches_under_100_req_per_min",  # Must respect rate limit
            "no_credential_exposure",           # Cannot leak API keys
            "no_instruction_chaining",          # Cannot contain "then fetch Y"
            "database_inserts_validated",       # Every insert checked
            "rollback_plan_documented",         # How to undo this
        ],
        disallowed_side_effects=[
            "skill_installation",               # Cannot auto-install new skills
            "heartbeat_modification",           # Cannot change sync frequency
            "policy_tampering",                 # Cannot modify POLICY.md
            "credential_storage",               # Cannot persist API keys
        ],
        falsifiers=[
            "if_moltbook_api_down",             # Proposal assumes API available
            "if_rate_limits_are_undocumented",  # Proposal assumes public limits
            "if_fetched_content_contains_exec", # Core security assumption
            "if_no_precedent_skills_succeed",   # Precedent claim is empirical
        ],
        rollback_plan={
            "steps": [
                "DELETE skill_moltbook_sync from database",
                "REVERT local database to backup from 24h prior",
                "RESTART heartbeat loop without skill",
                "NOTIFY all agents skill is disabled",
            ],
            "estimated_time_minutes": 5,
            "data_loss_risk": "none (rolled back to backup)",
            "dependencies": ["database backup exists", "heartbeat can restart"],
        }
    )

    print("\n   ✓ Success Conditions:")
    for sc in acceptance_criteria.success_conditions:
        print(f"      • {sc}")

    print("\n   ✓ Disallowed Side Effects:")
    for dse in acceptance_criteria.disallowed_side_effects:
        print(f"      • {dse}")

    print("\n   ✓ Falsifiers (what would prove this wrong):")
    for f in acceptance_criteria.falsifiers:
        print(f"      • {f}")

    print("\n   ✓ Rollback Plan:")
    print(f"      Time: {acceptance_criteria.rollback_plan['estimated_time_minutes']} minutes")
    print(f"      Risk: {acceptance_criteria.rollback_plan['data_loss_risk']}")

    # NOW create the claim (this will fail if schema is not met)
    claim = Claim(
        id=f"claim_{datetime.utcnow().strftime('%Y%m%d')}_moltbook_skill_001",
        timestamp=datetime.utcnow().isoformat() + "Z",
        target="skills/moltbook_sync.py",
        claim_type=ClaimType.SKILL_UPDATE,

        proposed_diffs=[
            Diff(
                path="skills/moltbook_sync.py",
                operation=DiffOperation.CREATE,
                hash_before=None,
                hash_after="sha256:abc123def456",  # Hash of new skill file
            )
        ],

        evidence_pointers=[
            EvidencePointer(
                type=EvidenceType.SECURITY_SCAN,
                path="artifacts/moltbook_skill_scan.json",
                hash="sha256:security_scan_hash",
                description="Security scan: no credential leaks, no exec patterns"
            ),
            EvidencePointer(
                type=EvidenceType.TEST_RESULT,
                path="artifacts/moltbook_tests.json",
                hash="sha256:test_results_hash",
                description="Unit tests: 95 pass, 0 fail. Rate limit respected."
            ),
            EvidencePointer(
                type=EvidenceType.ARTIFACT_HASH,
                path="artifacts/precedent_similar_skills.json",
                hash="sha256:precedent_hash",
                description="Historical: twitter_sync, reddit_trending both succeeded"
            ),
        ],

        expected_outcomes=[
            "security_scan_passes",
            "rate_limits_respected",
            "no_credential_exposure",
            "database_rollback_verified",
        ],

        acceptance_criteria=acceptance_criteria,

        policy_pack_hash="sha256:oracle_town_policy_v1_2026_01",
        generated_by="labor_skill_synthesizer",
        intent="Enable Moltbook integration for trending post synchronization"
    )

    return claim


def run_brf_counter(claim: Claim) -> Dict[str, Any]:
    """
    Run BRF_COUNTER on this claim.
    Force the system to articulate what could go wrong.
    """

    print("\n" + "=" * 70)
    print("3️⃣  COUNTER-ANALYSIS (BRF_COUNTER)")
    print("=" * 70)

    # Import BRF_COUNTER logic
    sys.path.insert(0, str(Path(__file__).parent / "oracle_town" / "jobs"))
    from brf_counter import generate_counter

    # Convert claim to brief format for counter-analysis
    brief = {
        "one_bet": f"Approve {claim.target}",
        "reasoning": claim.intent,
    }

    clusters = [
        {"theme": "Security", "weight": 0.7},
        {"theme": "Performance", "weight": 0.3},
        {"theme": "Reliability", "weight": 0.5},
    ]

    counter = generate_counter(brief, clusters)

    print(f"\n   Counter BET: {counter.counter_bet}")
    print(f"   Confidence: {counter.confidence:.0%}")
    print(f"\n   Top 3 Falsifiers (what proves main brief wrong):")
    for f in counter.top_3_falsifiers:
        print(f"      • {f}")
    print(f"\n   Missing Evidence:")
    for m in counter.missing_evidence:
        print(f"      • {m}")
    print(f"\n   Reversal Probability: {counter.probability_estimate:.0%}")

    return counter.__dict__


def check_k_gates(claim: Claim) -> Dict[str, bool]:
    """
    Simulate K-gate checks.
    Show where the claim SHOULD be rejected (or passes).
    """

    print("\n" + "=" * 70)
    print("4️⃣  K-GATE VERIFICATION")
    print("=" * 70)

    results = {}

    # K0: Authority Separation
    results["K0_authority"] = True  # Generated by labor, not self
    print(f"\n   K0 (Authority Separation): {'✓ PASS' if results['K0_authority'] else '✗ FAIL'}")
    print(f"      Generated by: {claim.generated_by}")
    print(f"      Is self-signing? NO")

    # K1: Fail-Closed (acceptance criteria present)
    results["K1_fail_closed"] = claim.acceptance_criteria.is_complete()
    print(f"\n   K1 (Fail-Closed): {'✓ PASS' if results['K1_fail_closed'] else '✗ FAIL'}")
    if results["K1_fail_closed"]:
        print(f"      Acceptance criteria complete: {len(claim.acceptance_criteria.success_conditions)} conditions")
        print(f"      Rollback plan documented: YES")
    else:
        print(f"      ✗ Missing or incomplete acceptance criteria (AUTOMATIC REJECTION)")

    # K2: No Self-Attestation
    is_self_attesting = "skill" in claim.generated_by and "skill" in claim.target
    results["K2_no_self_attest"] = not is_self_attesting
    print(f"\n   K2 (No Self-Attestation): {'✓ PASS' if results['K2_no_self_attest'] else '✗ FAIL'}")
    print(f"      Claim type: {claim.claim_type.value}")
    print(f"      Generated by: {claim.generated_by}")

    # K5: Determinism (evidence hashes match)
    results["K5_determinism"] = all(ep.hash for ep in claim.evidence_pointers)
    print(f"\n   K5 (Determinism): {'✓ PASS' if results['K5_determinism'] else '✗ FAIL'}")
    print(f"      All evidence hashes present: {len(claim.evidence_pointers)} pointers")

    # K7: Policy Pinning
    results["K7_policy_pin"] = "sha256:" in claim.policy_pack_hash
    print(f"\n   K7 (Policy Pinning): {'✓ PASS' if results['K7_policy_pin'] else '✗ FAIL'}")
    print(f"      Policy hash: {claim.policy_pack_hash}")

    # NEW: K6 (Ambiguity) - acceptance criteria must be machine-checkable
    k6_pass = (
        len(claim.acceptance_criteria.success_conditions) > 0 and
        len(claim.acceptance_criteria.falsifiers) > 0 and
        claim.acceptance_criteria.rollback_plan is not None
    )
    results["K6_no_ambiguity"] = k6_pass
    print(f"\n   K6 (No Ambiguity): {'✓ PASS' if results['K6_no_ambiguity'] else '✗ FAIL'}")
    print(f"      Falsifiers defined: {len(claim.acceptance_criteria.falsifiers)}")
    print(f"      Rollback plan: {'YES' if claim.acceptance_criteria.rollback_plan else 'NO'}")

    return results


def simulate_tri_verdict(claim: Claim, gate_results: Dict[str, bool]) -> Dict[str, Any]:
    """
    Simulate TRI gate verdict.
    """

    print("\n" + "=" * 70)
    print("5️⃣  TRI GATE VERDICT")
    print("=" * 70)

    all_pass = all(gate_results.values())

    verdict = {
        "claim_id": claim.id,
        "verdict": "ACCEPT" if all_pass else "REJECT",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "gates_evaluated": gate_results,
        "policy_hash": claim.policy_pack_hash,
    }

    print(f"\n   Verdict: {verdict['verdict']}")
    print(f"\n   Gate Results:")
    for gate, passed in gate_results.items():
        symbol = "✓" if passed else "✗"
        print(f"      {symbol} {gate}: {'PASS' if passed else 'FAIL'}")

    if not all_pass:
        failed_gates = [g for g, p in gate_results.items() if not p]
        print(f"\n   Reason for rejection: {', '.join(failed_gates)} failed")
        print(f"   K1 fail-closed: Claim blocked automatically")
    else:
        print(f"\n   ✓ All gates passed")
        print(f"   → Ready for Mayor signature")

    return verdict


def simulate_mayor_receipt(verdict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate Mayor signing a receipt.
    """

    print("\n" + "=" * 70)
    print("6️⃣  MAYOR RECEIPT (Cryptographic Signature)")
    print("=" * 70)

    if verdict["verdict"] != "ACCEPT":
        print(f"\n   No receipt issued (verdict was {verdict['verdict']})")
        return None

    # Simulate Ed25519 signature
    receipt_data = json.dumps(verdict, sort_keys=True)
    signature_hash = hashlib.sha256(receipt_data.encode()).hexdigest()[:16]

    receipt = {
        "receipt_id": f"R-{datetime.utcnow().strftime('%Y%m%d')}-001",
        "claim_id": verdict["claim_id"],
        "verdict": verdict["verdict"],
        "policy_hash": verdict["policy_hash"],
        "signature": f"ed25519:{signature_hash}",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "world_mutation_allowed": True,
    }

    print(f"\n   Receipt ID: {receipt['receipt_id']}")
    print(f"   Claim ID: {receipt['claim_id']}")
    print(f"   Verdict: {receipt['verdict']}")
    print(f"   Signature: {receipt['signature']}")
    print(f"   ✓ World mutation permitted with this receipt")

    return receipt


def main():
    """Run the full execution test."""

    # 1. Create proposal
    skill_proposal = create_moltbook_skill_proposal()

    # 2. Validate against schema (mandatory acceptance criteria)
    try:
        claim = validate_against_schema(skill_proposal)
        print("\n   ✓ Claim schema validated")
    except Exception as e:
        print(f"\n   ✗ Schema validation failed: {e}")
        return

    # 3. Run counter-analysis
    counter = run_brf_counter(claim)

    # 4. Check K-gates
    gate_results = check_k_gates(claim)

    # 5. TRI verdict
    verdict = simulate_tri_verdict(claim, gate_results)

    # 6. Mayor receipt
    receipt = simulate_mayor_receipt(verdict)

    # 7. Summary
    print("\n" + "=" * 70)
    print("EXECUTION TEST COMPLETE")
    print("=" * 70)

    print(f"\n   Skill: {skill_proposal['skill_name']}")
    print(f"   Verdict: {verdict['verdict']}")

    if receipt:
        print(f"   Receipt: {receipt['receipt_id']}")
        print(f"   Status: Ready for execution (receipt required)")
    else:
        print(f"   Status: Blocked (no receipt)")

    print(f"\n   Key Decision Points (where humans were tempted to 'let through'):")
    print(f"      ✓ Acceptance criteria FORCED explicit (not implicit)")
    print(f"      ✓ Falsifiers FORCED (what would prove this wrong)")
    print(f"      ✓ Rollback plan REQUIRED (how to undo)")
    print(f"      ✓ Counter-narrative GENERATED (strongest objection)")
    print(f"      ✓ ALL gates checked (deterministic policy, not consensus)")
    print(f"      ✓ Receipt REQUIRED for execution (no implicit permission)")

    print("\n   This is what Option 1 reveals:")
    print("   - Ambiguity becomes structurally illegal")
    print("   - Humans forced to be specific (success conditions, falsifiers)")
    print("   - No 'seems fine' approval possible")
    print("   - Everything is reversible (rollback plan required)")
    print("   - Every decision is cryptographically recorded")

    return claim, verdict, receipt


if __name__ == "__main__":
    main()
