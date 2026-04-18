#!/usr/bin/env python3
"""
ORACLE SUPERTEAM — Example Run

This script demonstrates a complete claim submission and adjudication process.
Run: python3 example_run.py
"""

from oracle.engine import run_oracle
import json

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_manifest(manifest):
    print(f"\n📋 RunManifest ID: {manifest['run_id']}")
    print(f"⚙️  Code Version: {manifest['code_version']}")
    print(f"\n🎯 DECISION: {manifest['decision']['final']}")
    print(f"   Ship Permitted: {manifest['decision']['ship_permitted']}")
    print(f"   Reason Codes: {', '.join(manifest['decision']['reason_codes'])}")
    print(f"\n📊 SCORING:")
    print(f"   S_c (QI-INT): {manifest['derived']['qi_int']['S_c']}")
    print(f"   Amplitude: {manifest['derived']['qi_int']['A_c']}")
    print(f"\n🔐 GOVERNANCE:")
    print(f"   Kill Switch: {manifest['derived']['kill_switch_triggered']}")
    print(f"   Rule Kill: {manifest['derived']['rule_kill_triggered']}")
    print(f"   Open Obligations: {len(manifest['derived']['obligations_open'])}")
    print(f"   Contradictions: {len(manifest['derived']['contradictions'])}")

    if manifest['derived']['obligations_open']:
        print(f"\n⚠️  BLOCKING OBLIGATIONS:")
        for i, ob in enumerate(manifest['derived']['obligations_open'], 1):
            print(f"   {i}. [{ob['type']}] {ob['closure_criteria']} (owner: {ob['owner_team']})")

    print(f"\n🔒 HASHES:")
    print(f"   Inputs:  {manifest['hashes']['inputs_hash'][:16]}...")
    print(f"   Outputs: {manifest['hashes']['outputs_hash'][:16]}...")

# Example 1: Successful Approval
print_header("Example 1: SUCCESSFUL APPROVAL — OAuth Implementation")

payload_success = {
    "scenario_id": "example-success",
    "claim": {
        "id": "claim-oauth",
        "assertion": "Deploy OAuth 2.0 authentication system",
        "tier": "Tier I",
        "domain": ["security", "engineering"],
        "owner_team": "Engineering Wing"
    },
    "evidence": [
        {
            "id": "ev-security-audit",
            "type": "security_audit",
            "tags": ["verified", "oauth2", "penetration_tested"]
        },
        {
            "id": "ev-compliance",
            "type": "legal_review",
            "tags": ["gdpr_compliant_claim", "data_protection"]
        }
    ],
    "votes": [
        {"team": "Engineering Wing", "vote": "APPROVE", "rationale": "Implementation complete, all tests passing."},
        {"team": "Security Sector", "vote": "APPROVE", "rationale": "Security audit passed with no critical findings."},
        {"team": "Legal Office", "vote": "APPROVE", "rationale": "Complies with data protection requirements."},
        {"team": "Strategy HQ", "vote": "APPROVE", "rationale": "Aligns with platform modernization goals."}
    ]
}

manifest_success = run_oracle(payload_success)
print_manifest(manifest_success)

# Example 2: Quarantine (Missing Evidence)
print_header("Example 2: QUARANTINE — AI Feature Without Validation")

payload_quarantine = {
    "scenario_id": "example-quarantine",
    "claim": {
        "id": "claim-ai-feature",
        "assertion": "AI-powered recommendation engine improves user engagement by 40%",
        "tier": "Tier I",
        "domain": ["ai", "product"],
        "owner_team": "Engineering Wing"
    },
    "evidence": [
        {
            "id": "ev-prototype",
            "type": "prototype_demo",
            "tags": ["preliminary", "not_peer_reviewed"]
        }
    ],
    "votes": [
        {"team": "Engineering Wing", "vote": "CONDITIONAL", "rationale": "Need A/B test results with statistical significance."},
        {"team": "Data Validation Office", "vote": "CONDITIONAL", "rationale": "40% claim requires verified metrics, not estimates."},
        {"team": "Strategy HQ", "vote": "APPROVE", "rationale": "Strategic priority for Q1."},
        {"team": "UX/Impact Bureau", "vote": "APPROVE", "rationale": "User testing feedback positive."}
    ]
}

manifest_quarantine = run_oracle(payload_quarantine)
print_manifest(manifest_quarantine)

# Example 3: Kill-Switch Activation
print_header("Example 3: KILL — Privacy Violation Risk")

payload_kill = {
    "scenario_id": "example-kill",
    "claim": {
        "id": "claim-user-tracking",
        "assertion": "Enhanced user tracking for personalization (anonymous)",
        "tier": "Tier I",
        "domain": ["privacy", "product"],
        "owner_team": "Strategy HQ"
    },
    "evidence": [
        {
            "id": "ev-privacy-claim",
            "type": "privacy_policy",
            "tags": ["anonymous_claim", "no_personal_data_claim"]
        },
        {
            "id": "ev-implementation",
            "type": "technical_spec",
            "tags": ["biometric", "face", "pii", "gdpr_special_category"]
        }
    ],
    "votes": [
        {"team": "Strategy HQ", "vote": "APPROVE", "rationale": "Key for personalization roadmap."},
        {"team": "Engineering Wing", "vote": "APPROVE", "rationale": "Technical implementation ready."},
        {"team": "Legal Office", "vote": "KILL", "rationale": "CONTRADICTION: Cannot be anonymous with biometric data. GDPR violation."},
        {"team": "Data Validation Office", "vote": "QUARANTINE", "rationale": "Evidence tags contradict privacy claim."}
    ]
}

manifest_kill = run_oracle(payload_kill)
print_manifest(manifest_kill)

# Summary
print_header("SUMMARY")
print("""
✅ Example 1: ACCEPT — All teams approved with verified evidence
⚠️  Example 2: QUARANTINE — Missing evidence triggered blocking obligations
🛑 Example 3: KILL — Privacy contradiction + kill-switch vote

Key Takeaways:
1. Obligations block shipment until resolved (supply evidence)
2. Kill-switch teams (Legal, Security) have override authority
3. Evidence contradictions trigger automatic rules (HC-PRIV-001)
4. QI-INT scoring uses complex amplitude voting (not simple averaging)
5. All decisions are hash-verified and replayable

Next Steps:
- Run full test vault: python3 -m ci.run_test_vault
- Read CONSTITUTION.md for governance axioms
- Explore test_vault/scenarios/ for edge cases
- Customize oracle/config.py for your organization
""")

print("=" * 70)
print("  ORACLE SUPERTEAM is not a conversation. It is an institution.")
print("=" * 70 + "\n")
